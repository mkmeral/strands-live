import json
import uuid
from pathlib import Path
from typing import List, Optional, Union

from .audio_streamer import AudioStreamer
from .bedrock_streamer import BedrockStreamManager, debug_print, time_it_async
from .context_builder import ContextBuilder, create_enhanced_system_prompt
from .tool_handler import ToolHandler


class SpeechAgent:
    """High-level speech agent that orchestrates audio streaming and bedrock communication."""

    def __init__(
        self,
        model_id="amazon.nova-sonic-v1:0",
        region="us-east-1",
        tool_handler=None,
        # Configuration parameters
        system_prompt=None,
        max_tokens=1024,
        top_p=0.9,
        temperature=0.7,
        voice_id="matthew",
        sample_rate_hz=24000,
        sample_size_bits=16,
        channel_count=1,
        audio_encoding="base64",
        audio_type="SPEECH",
        # Context building parameters
        working_directory: Optional[Union[str, Path]] = None,
        include_directory_structure: bool = False,
        include_project_files: bool = False,
        include_git_context: bool = False,
        custom_file_patterns: Optional[List[str]] = None,
        max_directory_depth: int = 2,
        max_files_listed: int = 20,
    ):
        """Initialize the speech agent with its components.

        Args:
            model_id: The Bedrock model ID to use
            region: AWS region
            tool_handler: Optional tool handler to use (defaults to ToolHandler)
            system_prompt: Custom system prompt (defaults to standard assistant prompt)
            max_tokens: Maximum tokens for response generation
            top_p: Top-p parameter for response generation
            temperature: Temperature parameter for response generation
            voice_id: Voice ID for audio output
            sample_rate_hz: Audio sample rate
            sample_size_bits: Audio sample size in bits
            channel_count: Audio channel count
            audio_encoding: Audio encoding format
            audio_type: Audio type
            
            # Context building parameters
            working_directory: Directory to gather context from (defaults to current directory)
            include_directory_structure: Include directory tree in context
            include_project_files: Include contents of README.md, package.json, etc.
            include_git_context: Include git branch, recent commits, and status
            custom_file_patterns: Custom list of files to include in context
            max_directory_depth: Maximum depth for directory tree
            max_files_listed: Maximum number of files to list in directory tree
        """
        self.model_id = model_id
        self.region = region

        # Store context configuration
        self.working_directory = Path(working_directory) if working_directory else Path.cwd()
        self.include_directory_structure = include_directory_structure
        self.include_project_files = include_project_files
        self.include_git_context = include_git_context
        self.custom_file_patterns = custom_file_patterns
        self.max_directory_depth = max_directory_depth
        self.max_files_listed = max_files_listed

        # Build enhanced system prompt with context
        enhanced_prompt = self._build_enhanced_system_prompt(system_prompt)

        # Configuration
        self.system_prompt = enhanced_prompt
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.voice_id = voice_id
        self.sample_rate_hz = sample_rate_hz
        self.sample_size_bits = sample_size_bits
        self.channel_count = channel_count
        self.audio_encoding = audio_encoding
        self.audio_type = audio_type

        # State management
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        self.display_assistant_text = False
        self.current_role = None
        self.barge_in = False

        # Tool execution state
        self.current_tool_use_content = ""
        self.current_tool_use_id = ""
        self.current_tool_name = ""

        # Initialize tool handler (use provided or default)
        self.tool_handler = tool_handler if tool_handler is not None else ToolHandler()

        # Initialize Bedrock stream manager as transport layer
        self.bedrock_stream_manager = BedrockStreamManager(
            model_id=model_id,
            region=region,
            tool_handler=self.tool_handler,
            agent=self,  # Pass reference so streamer can call back
        )

        # Initialize audio streamer with agent reference
        self.audio_streamer = AudioStreamer(self.bedrock_stream_manager, agent=self)

    def get_inference_config(self):
        """Get inference configuration for the session."""
        return {
            "maxTokens": self.max_tokens,
            "topP": self.top_p,
            "temperature": self.temperature,
        }

    def get_audio_output_config(self):
        """Get audio output configuration."""
        return {
            "mediaType": "audio/lpcm",
            "sampleRateHertz": self.sample_rate_hz,
            "sampleSizeBits": self.sample_size_bits,
            "channelCount": self.channel_count,
            "voiceId": self.voice_id,
            "encoding": self.audio_encoding,
            "audioType": self.audio_type,
        }

    def get_tool_config(self):
        """Get tool configuration from tool handler."""
        if self.tool_handler:
            return self.tool_handler.get_bedrock_tool_config()
        return {"tools": []}

    async def initialize(self):
        """Initialize the speech agent and its components."""
        await time_it_async(
            "initialize_stream", self.bedrock_stream_manager.initialize_stream
        )

        # Send initial session setup
        await self._initialize_conversation()

    async def _initialize_conversation(self):
        """Initialize the conversation with system prompt and configuration."""
        # Send session start
        session_start_event = {
            "event": {
                "sessionStart": {"inferenceConfiguration": self.get_inference_config()}
            }
        }
        await self.bedrock_stream_manager.send_raw_event(
            json.dumps(session_start_event)
        )

        # Send prompt start with configurations
        prompt_start_event = {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": self.get_audio_output_config(),
                    "toolUseOutputConfiguration": {"mediaType": "application/json"},
                    "toolConfiguration": self.get_tool_config(),
                }
            }
        }
        await self.bedrock_stream_manager.send_raw_event(json.dumps(prompt_start_event))

        # Send system prompt
        await self._send_system_prompt()

    async def _send_system_prompt(self):
        """Send the system prompt to establish context."""
        # Content start for system message
        system_content_start = {
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "type": "TEXT",
                    "role": "SYSTEM",
                    "interactive": True,
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        }
        await self.bedrock_stream_manager.send_raw_event(
            json.dumps(system_content_start)
        )

        # System prompt content
        system_content = {
            "event": {
                "textInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "content": self.system_prompt,
                }
            }
        }
        await self.bedrock_stream_manager.send_raw_event(json.dumps(system_content))

        # Content end for system message
        system_content_end = {
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                }
            }
        }
        await self.bedrock_stream_manager.send_raw_event(json.dumps(system_content_end))

    async def handle_response_event(self, json_data):
        """Handle response events from Bedrock stream."""
        if "event" not in json_data:
            return

        event = json_data["event"]

        if "contentStart" in event:
            await self._handle_content_start(event["contentStart"])
        elif "textOutput" in event:
            await self._handle_text_output(event["textOutput"])
        elif "audioOutput" in event:
            await self._handle_audio_output(event["audioOutput"])
        elif "toolUse" in event:
            await self._handle_tool_use(event["toolUse"])
        elif "contentEnd" in event:
            await self._handle_content_end(event["contentEnd"])
        elif "completionEnd" in event:
            await self._handle_completion_end()

    async def _handle_content_start(self, content_start):
        """Handle content start event."""
        debug_print("Content start detected")
        self.current_role = content_start["role"]

        # Check for speculative content
        if "additionalModelFields" in content_start:
            try:
                additional_fields = json.loads(content_start["additionalModelFields"])
                if additional_fields.get("generationStage") == "SPECULATIVE":
                    debug_print("Speculative content detected")
                    self.display_assistant_text = True
                else:
                    self.display_assistant_text = False
            except json.JSONDecodeError:
                debug_print("Error parsing additionalModelFields")

    async def _handle_text_output(self, text_output):
        """Handle text output event."""
        text_content = text_output["content"]
        # role = text_output["role"]  # Currently unused, but may be needed for future features

        # Check for barge-in
        if '{ "interrupted" : true }' in text_content:
            debug_print("Barge-in detected. Stopping audio output.")
            self.barge_in = True

        # Display text based on role and display settings
        if self.current_role == "ASSISTANT" and self.display_assistant_text:
            print(f"Assistant: {text_content}")
        elif self.current_role == "USER":
            print(f"\n----- USER -------\nUser: {text_content}\n\n")

    async def _handle_audio_output(self, audio_output):
        """Handle audio output event."""
        audio_content = audio_output["content"]
        import base64

        audio_bytes = base64.b64decode(audio_content)
        await self.bedrock_stream_manager.audio_output_queue.put(audio_bytes)

    async def _handle_tool_use(self, tool_use):
        """Handle tool use event."""
        self.current_tool_use_content = tool_use
        self.current_tool_name = tool_use["toolName"]
        self.current_tool_use_id = tool_use["toolUseId"]
        debug_print(
            f"Tool use detected: {self.current_tool_name}, ID: {self.current_tool_use_id}"
        )

    async def _handle_content_end(self, content_end):
        """Handle content end event."""
        if content_end.get("type") == "TOOL":
            debug_print("Processing tool use and sending result")
            await self._execute_tool()

    async def _handle_completion_end(self):
        """Handle completion end event."""
        print("End of response sequence")

    async def _execute_tool(self):
        """Execute tool and send result back to stream."""
        if self.tool_handler:
            tool_result = await self.tool_handler.process_tool_use(
                self.current_tool_name, self.current_tool_use_content
            )
            tool_content_name = str(uuid.uuid4())

            # Send tool result through the stream manager
            await self.bedrock_stream_manager.send_tool_start_event(
                tool_content_name, self.current_tool_use_id, self.prompt_name
            )
            await self.bedrock_stream_manager.send_tool_result_event(
                tool_content_name, tool_result, self.prompt_name
            )
            await self.bedrock_stream_manager.send_tool_content_end_event(
                tool_content_name, self.prompt_name
            )
        else:
            debug_print("No tool handler available")

    async def start_conversation(self):
        """Start a conversation session."""
        try:
            # This will run until the user presses Enter
            await self.audio_streamer.start_streaming()
        except KeyboardInterrupt:
            print("Interrupted by user")
        except Exception as e:
            print(f"Error in conversation: {e}")
        finally:
            # Clean up
            await self.stop_conversation()

    async def stop_conversation(self):
        """Stop the conversation and clean up resources."""
        await self.audio_streamer.stop_streaming()

    async def process_tool_use(self, tool_name, tool_use_content):
        """Process tool use - delegated to tool handler for backward compatibility."""
        return await self.tool_handler.process_tool_use(tool_name, tool_use_content)
    
    def _build_enhanced_system_prompt(self, base_prompt: Optional[str] = None) -> str:
        """Build enhanced system prompt with project context.
        
        Args:
            base_prompt: Base system prompt to enhance
            
        Returns:
            Enhanced system prompt with context
        """
        # Use provided base prompt or default
        if base_prompt is None:
            base_prompt = (
                "You are a helpful assistant based on Strands Agents. You can access internet, customer's files and AWS account through tools. "
                "Help user achieve their goal. Keep the interaction conversational. "
                "When reading order numbers, please read each digit individually, separated by pauses. For example, order #1234 should be read as 'order number one-two-three-four' rather than 'order number one thousand two hundred thirty-four'."
            )
        
        # If no context features are enabled, return base prompt
        if not (self.include_directory_structure or self.include_project_files or self.include_git_context):
            return base_prompt
        
        try:
            # Create context builder
            context_builder = ContextBuilder(self.working_directory)
            
            # Build enhanced prompt
            enhanced_prompt = create_enhanced_system_prompt(
                base_prompt=base_prompt,
                context_builder=context_builder,
                include_directory=self.include_directory_structure,
                include_files=self.include_project_files,
                include_git=self.include_git_context,
                file_patterns=self.custom_file_patterns
            )
            
            return enhanced_prompt
            
        except Exception as e:
            print(f"Warning: Failed to build enhanced context: {e}")
            return base_prompt
    
    def refresh_context(self) -> str:
        """Refresh the project context and return the updated system prompt.
        
        This can be called to update the context if files have changed during
        the conversation.
        
        Returns:
            Updated system prompt with fresh context
        """
        try:
            refreshed_prompt = self._build_enhanced_system_prompt()
            self.system_prompt = refreshed_prompt
            print("✅ Project context refreshed successfully")
            return refreshed_prompt
        except Exception as e:
            print(f"❌ Failed to refresh context: {e}")
            return self.system_prompt
    
    def get_current_context_summary(self) -> str:
        """Get a summary of the current context being used.
        
        Returns:
            Human-readable summary of context configuration
        """
        summary_parts = [
            f"**Working Directory:** {self.working_directory.absolute()}",
        ]
        
        if self.include_directory_structure:
            summary_parts.append("✅ Directory structure included")
        else:
            summary_parts.append("❌ Directory structure excluded")
            
        if self.include_project_files:
            patterns = self.custom_file_patterns or ['README.md', 'AmazonQ.md', 'CHANGELOG.md', 'package.json', 'pyproject.toml']
            summary_parts.append(f"✅ Project files included: {', '.join(patterns)}")
        else:
            summary_parts.append("❌ Project files excluded")
            
        if self.include_git_context:
            summary_parts.append("✅ Git context included")
        else:
            summary_parts.append("❌ Git context excluded")
        
        return "\n".join(summary_parts)
    
    def get_raw_context(self) -> str:
        """Get the raw context that was added to the system prompt.
        
        Returns:
            The raw context string that was appended to the system prompt
        """
        try:
            context_builder = ContextBuilder(self.working_directory)
            return context_builder.build_full_context(
                include_directory=self.include_directory_structure,
                include_files=self.include_project_files,
                include_git=self.include_git_context,
                file_patterns=self.custom_file_patterns
            )
        except Exception as e:
            return f"Error generating context: {e}"
