import asyncio
import base64
import datetime
import inspect
import json
import time
import uuid

from aws_sdk_bedrock_runtime.client import (
    BedrockRuntimeClient,
    InvokeModelWithBidirectionalStreamOperationInput,
)
from aws_sdk_bedrock_runtime.config import (
    Config,
    HTTPAuthSchemeResolver,
    SigV4AuthScheme,
)
from aws_sdk_bedrock_runtime.models import (
    BidirectionalInputPayloadPart,
    InvokeModelWithBidirectionalStreamInputChunk,
)
from smithy_aws_core.credentials_resolvers.environment import (
    EnvironmentCredentialsResolver,
)

# Tool handling will be injected from outside


def debug_print(message):
    """Print only if debug mode is enabled"""
    # Import DEBUG from cli module to avoid circular imports
    from .cli import DEBUG

    if DEBUG:
        functionName = inspect.stack()[1].function
        if functionName == "time_it" or functionName == "time_it_async":
            functionName = inspect.stack()[2].function
        print(
            f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S.%f}"[:-3]
            + " "
            + functionName
            + " "
            + message
        )


def time_it(label, methodToRun):
    start_time = time.perf_counter()
    result = methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


async def time_it_async(label, methodToRun):
    start_time = time.perf_counter()
    result = await methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


class BedrockStreamManager:
    """Manages bidirectional streaming with AWS Bedrock using asyncio"""

    # Event templates
    START_SESSION_EVENT = """{
        "event": {
            "sessionStart": {
            "inferenceConfiguration": {
                "maxTokens": 1024,
                "topP": 0.9,
                "temperature": 0.7
                }
            }
        }
    }"""

    CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
            "promptName": "%s",
            "contentName": "%s",
            "type": "AUDIO",
            "interactive": true,
            "role": "USER",
            "audioInputConfiguration": {
                "mediaType": "audio/lpcm",
                "sampleRateHertz": 16000,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "audioType": "SPEECH",
                "encoding": "base64"
                }
            }
        }
    }"""

    AUDIO_EVENT_TEMPLATE = """{
        "event": {
            "audioInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
            }
        }
    }"""

    TEXT_CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
            "promptName": "%s",
            "contentName": "%s",
            "type": "TEXT",
            "role": "%s",
            "interactive": true,
                "textInputConfiguration": {
                    "mediaType": "text/plain"
                }
            }
        }
    }"""

    TEXT_INPUT_EVENT = """{
        "event": {
            "textInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
            }
        }
    }"""

    TOOL_CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
                "promptName": "%s",
                "contentName": "%s",
                "interactive": false,
                "type": "TOOL",
                "role": "TOOL",
                "toolResultInputConfiguration": {
                    "toolUseId": "%s",
                    "type": "TEXT",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        }
    }"""

    CONTENT_END_EVENT = """{
        "event": {
            "contentEnd": {
            "promptName": "%s",
            "contentName": "%s"
            }
        }
    }"""

    PROMPT_END_EVENT = """{
        "event": {
            "promptEnd": {
            "promptName": "%s"
            }
        }
    }"""

    SESSION_END_EVENT = """{
        "event": {
            "sessionEnd": {}
        }
    }"""

    def start_prompt(self):
        """Create a promptStart event"""
        # Get tool configuration from tool handler
        tool_config = {}
        if self.tool_handler:
            tool_config = self.tool_handler.get_bedrock_tool_config()
        else:
            # Fallback to empty tools if no handler
            tool_config = {"tools": []}

        prompt_start_event = {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 24000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "voiceId": "matthew",
                        "encoding": "base64",
                        "audioType": "SPEECH",
                    },
                    "toolUseOutputConfiguration": {"mediaType": "application/json"},
                    "toolConfiguration": tool_config,
                }
            }
        }

        return json.dumps(prompt_start_event)

    def tool_result_event(self, content_name, content, role):
        """Create a tool result event"""

        if isinstance(content, dict):
            content_json_string = json.dumps(content)
        else:
            content_json_string = content

        tool_result_event = {
            "event": {
                "toolResult": {
                    "promptName": self.prompt_name,
                    "contentName": content_name,
                    "content": content_json_string,
                }
            }
        }
        return json.dumps(tool_result_event)

    def __init__(
        self, model_id="amazon.nova-sonic-v1:0", region="us-east-1", tool_handler=None
    ):
        """Initialize the stream manager."""
        self.model_id = model_id
        self.region = region
        self.tool_handler = tool_handler  # Inject tool handler from outside

        # Replace RxPy subjects with asyncio queues
        self.audio_input_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        self.response_task = None
        self.stream_response = None
        self.is_active = False
        self.barge_in = False
        self.bedrock_client = None

        # Audio playback components
        self.audio_player = None

        # Text response components
        self.display_assistant_text = False
        self.role = None

        # Session information
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        self.toolUseContent = ""
        self.toolUseId = ""
        self.toolName = ""

    def _initialize_client(self):
        """Initialize the Bedrock client."""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
            http_auth_scheme_resolver=HTTPAuthSchemeResolver(),
            http_auth_schemes={"aws.auth#sigv4": SigV4AuthScheme()},
        )
        self.bedrock_client = BedrockRuntimeClient(config=config)

    async def initialize_stream(self):
        """Initialize the bidirectional stream with Bedrock."""
        if not self.bedrock_client:
            self._initialize_client()

        try:
            self.stream_response = await time_it_async(
                "invoke_model_with_bidirectional_stream",
                lambda: self.bedrock_client.invoke_model_with_bidirectional_stream(
                    InvokeModelWithBidirectionalStreamOperationInput(
                        model_id=self.model_id
                    )
                ),
            )
            self.is_active = True
            default_system_prompt = (
                "You are a helpful assistant based on Strands Agents. You can access internet, customer's files and AWS account through tools. "
                "Help user achieve thier goal. Keep the interaction conversational."
            )

            # Send initialization events
            prompt_event = self.start_prompt()
            text_content_start = self.TEXT_CONTENT_START_EVENT % (
                self.prompt_name,
                self.content_name,
                "SYSTEM",
            )
            text_content = self.TEXT_INPUT_EVENT % (
                self.prompt_name,
                self.content_name,
                default_system_prompt,
            )
            text_content_end = self.CONTENT_END_EVENT % (
                self.prompt_name,
                self.content_name,
            )

            init_events = [
                self.START_SESSION_EVENT,
                prompt_event,
                text_content_start,
                text_content,
                text_content_end,
            ]

            for event in init_events:
                await self.send_raw_event(event)
                # Small delay between init events
                await asyncio.sleep(0.1)

            # Start listening for responses
            self.response_task = asyncio.create_task(self._process_responses())

            # Start processing audio input
            asyncio.create_task(self._process_audio_input())

            # Wait a bit to ensure everything is set up
            await asyncio.sleep(0.1)

            debug_print("Stream initialized successfully")
            return self
        except Exception as e:
            self.is_active = False
            print(f"Failed to initialize stream: {str(e)}")
            raise

    async def send_raw_event(self, event_json):
        """Send a raw event JSON to the Bedrock stream."""
        if not self.stream_response or not self.is_active:
            debug_print("Stream not initialized or closed")
            return

        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode("utf-8"))
        )

        try:
            await self.stream_response.input_stream.send(event)
            # For debugging large events, you might want to log just the type
            from .cli import DEBUG

            if DEBUG:
                if len(event_json) > 200:
                    event_type = json.loads(event_json).get("event", {}).keys()
                    debug_print(f"Sent event type: {list(event_type)}")
                else:
                    debug_print(f"Sent event: {event_json}")
        except Exception as e:
            debug_print(f"Error sending event: {str(e)}")
            from .cli import DEBUG

            if DEBUG:
                import traceback

                traceback.print_exc()

    async def send_audio_content_start_event(self):
        """Send a content start event to the Bedrock stream."""
        content_start_event = self.CONTENT_START_EVENT % (
            self.prompt_name,
            self.audio_content_name,
        )
        await self.send_raw_event(content_start_event)

    async def _process_audio_input(self):
        """Process audio input from the queue and send to Bedrock."""
        while self.is_active:
            try:
                # Get audio data from the queue
                data = await self.audio_input_queue.get()

                audio_bytes = data.get("audio_bytes")
                if not audio_bytes:
                    debug_print("No audio bytes received")
                    continue

                # Base64 encode the audio data
                blob = base64.b64encode(audio_bytes)
                audio_event = self.AUDIO_EVENT_TEMPLATE % (
                    self.prompt_name,
                    self.audio_content_name,
                    blob.decode("utf-8"),
                )

                # Send the event
                await self.send_raw_event(audio_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                debug_print(f"Error processing audio: {e}")
                from .cli import DEBUG

                if DEBUG:
                    import traceback

                    traceback.print_exc()

    def add_audio_chunk(self, audio_bytes):
        """Add an audio chunk to the queue."""
        self.audio_input_queue.put_nowait(
            {
                "audio_bytes": audio_bytes,
                "prompt_name": self.prompt_name,
                "content_name": self.audio_content_name,
            }
        )

    async def send_audio_content_end_event(self):
        """Send a content end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        content_end_event = self.CONTENT_END_EVENT % (
            self.prompt_name,
            self.audio_content_name,
        )
        await self.send_raw_event(content_end_event)
        debug_print("Audio ended")

    async def send_tool_start_event(self, content_name):
        """Send a tool content start event to the Bedrock stream."""
        content_start_event = self.TOOL_CONTENT_START_EVENT % (
            self.prompt_name,
            content_name,
            self.toolUseId,
        )
        debug_print(f"Sending tool start event: {content_start_event}")
        await self.send_raw_event(content_start_event)

    async def send_tool_result_event(self, content_name, tool_result):
        """Send a tool content event to the Bedrock stream."""
        # Use the actual tool result from processToolUse
        tool_result_event = self.tool_result_event(
            content_name=content_name, content=tool_result, role="TOOL"
        )
        debug_print(f"Sending tool result event: {tool_result_event}")
        await self.send_raw_event(tool_result_event)

    async def send_tool_content_end_event(self, content_name):
        """Send a tool content end event to the Bedrock stream."""
        tool_content_end_event = self.CONTENT_END_EVENT % (
            self.prompt_name,
            content_name,
        )
        debug_print(f"Sending tool content event: {tool_content_end_event}")
        await self.send_raw_event(tool_content_end_event)

    async def send_prompt_end_event(self):
        """Close the stream and clean up resources."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        prompt_end_event = self.PROMPT_END_EVENT % (self.prompt_name)
        await self.send_raw_event(prompt_end_event)
        debug_print("Prompt ended")

    async def send_session_end_event(self):
        """Send a session end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        await self.send_raw_event(self.SESSION_END_EVENT)
        self.is_active = False
        debug_print("Session ended")

    async def _process_responses(self):
        """Process incoming responses from Bedrock."""
        try:
            while self.is_active:
                try:
                    output = await self.stream_response.await_output()
                    result = await output[1].receive()
                    if result.value and result.value.bytes_:
                        try:
                            response_data = result.value.bytes_.decode("utf-8")
                            json_data = json.loads(response_data)

                            # Handle different response types
                            if "event" in json_data:
                                if "contentStart" in json_data["event"]:
                                    debug_print("Content start detected")
                                    content_start = json_data["event"]["contentStart"]
                                    # set role
                                    self.role = content_start["role"]
                                    # Check for speculative content
                                    if "additionalModelFields" in content_start:
                                        try:
                                            additional_fields = json.loads(
                                                content_start["additionalModelFields"]
                                            )
                                            if (
                                                additional_fields.get("generationStage")
                                                == "SPECULATIVE"
                                            ):
                                                debug_print(
                                                    "Speculative content detected"
                                                )
                                                self.display_assistant_text = True
                                            else:
                                                self.display_assistant_text = False
                                        except json.JSONDecodeError:
                                            debug_print(
                                                "Error parsing additionalModelFields"
                                            )
                                elif "textOutput" in json_data["event"]:
                                    text_content = json_data["event"]["textOutput"][
                                        "content"
                                    ]
                                    _role = json_data["event"]["textOutput"]["role"]
                                    # Check if there is a barge-in
                                    if '{ "interrupted" : true }' in text_content:
                                        debug_print(
                                            "Barge-in detected. Stopping audio output."
                                        )
                                        self.barge_in = True

                                    if (
                                        self.role == "ASSISTANT"
                                        and self.display_assistant_text
                                    ):
                                        print(f"Assistant: {text_content}")
                                    elif self.role == "USER":
                                        print(f"\n----- USER -------\nUser: {text_content}\n\n")

                                elif "audioOutput" in json_data["event"]:
                                    audio_content = json_data["event"]["audioOutput"][
                                        "content"
                                    ]
                                    audio_bytes = base64.b64decode(audio_content)
                                    await self.audio_output_queue.put(audio_bytes)
                                elif "toolUse" in json_data["event"]:
                                    self.toolUseContent = json_data["event"]["toolUse"]
                                    self.toolName = json_data["event"]["toolUse"][
                                        "toolName"
                                    ]
                                    self.toolUseId = json_data["event"]["toolUse"][
                                        "toolUseId"
                                    ]
                                    debug_print(
                                        f"Tool use detected: {self.toolName}, ID: {self.toolUseId}"
                                    )
                                elif (
                                    "contentEnd" in json_data["event"]
                                    and json_data["event"]
                                    .get("contentEnd", {})
                                    .get("type")
                                    == "TOOL"
                                ):
                                    debug_print(
                                        "Processing tool use and sending result"
                                    )
                                    if self.tool_handler:
                                        toolResult = (
                                            await self.tool_handler.process_tool_use(
                                                self.toolName, self.toolUseContent
                                            )
                                        )
                                        toolContent = str(uuid.uuid4())
                                        await self.send_tool_start_event(toolContent)
                                        await self.send_tool_result_event(
                                            toolContent, toolResult
                                        )
                                        await self.send_tool_content_end_event(
                                            toolContent
                                        )
                                    else:
                                        debug_print("No tool handler available")

                                elif "completionEnd" in json_data["event"]:
                                    # Handle end of conversation, no more response will be generated
                                    print("End of response sequence")

                            # Put the response in the output queue for other components
                            await self.output_queue.put(json_data)
                        except json.JSONDecodeError:
                            await self.output_queue.put({"raw_data": response_data})
                except StopAsyncIteration:
                    # Stream has ended
                    break
                except Exception as e:
                    # Handle ValidationException properly
                    if "ValidationException" in str(e):
                        error_message = str(e)
                        print(f"Validation error: {error_message}")
                    else:
                        print(f"Error receiving response: {e}")
                    break

        except Exception as e:
            print(f"Response processing error: {e}")
        finally:
            self.is_active = False

    async def close(self):
        """Close the stream properly."""
        if not self.is_active:
            return

        self.is_active = False
        if self.response_task and not self.response_task.done():
            self.response_task.cancel()

        await self.send_audio_content_end_event()
        await self.send_prompt_end_event()
        await self.send_session_end_event()

        if self.stream_response:
            await self.stream_response.input_stream.close()
