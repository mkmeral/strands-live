from .audio_streamer import AudioStreamer
from .bedrock_streamer import BedrockStreamManager, time_it_async
from .tool_handler import ToolHandler


class SpeechAgent:
    """High-level speech agent that orchestrates audio streaming and bedrock communication."""

    def __init__(
        self, model_id="amazon.nova-sonic-v1:0", region="us-east-1", tool_handler=None
    ):
        """Initialize the speech agent with its components.

        Args:
            model_id: The Bedrock model ID to use
            region: AWS region
            tool_handler: Optional tool handler to use (defaults to ToolHandler)
        """
        self.model_id = model_id
        self.region = region

        # Initialize tool handler (use provided or default)
        self.tool_handler = tool_handler if tool_handler is not None else ToolHandler()

        # Initialize Bedrock stream manager with tool handler
        self.bedrock_stream_manager = BedrockStreamManager(
            model_id=model_id, region=region, tool_handler=self.tool_handler
        )

        # Initialize audio streamer
        self.audio_streamer = AudioStreamer(self.bedrock_stream_manager)

    async def initialize(self):
        """Initialize the speech agent and its components."""
        await time_it_async(
            "initialize_stream", self.bedrock_stream_manager.initialize_stream
        )

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
