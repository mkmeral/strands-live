from unittest.mock import AsyncMock, patch

import pytest

from strands_live.speech_agent import SpeechAgent


class TestSpeechAgent:
    """Test cases for the SpeechAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("strands_live.speech_agent.AudioStreamer"),
            patch("strands_live.speech_agent.BedrockStreamManager"),
        ):
            self.speech_agent = SpeechAgent()

    def test_initialization(self):
        """Test that SpeechAgent initializes correctly."""
        with (
            patch("strands_live.speech_agent.AudioStreamer"),
            patch("strands_live.speech_agent.BedrockStreamManager"),
        ):
            agent = SpeechAgent(model_id="test-model", region="test-region")

            assert agent.model_id == "test-model"
            assert agent.region == "test-region"
            assert agent.tool_handler is not None
            assert agent.bedrock_stream_manager is not None
            assert agent.audio_streamer is not None

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test the initialize method."""
        # Mock the bedrock stream manager's methods
        self.speech_agent.bedrock_stream_manager.initialize_stream = AsyncMock()
        self.speech_agent.bedrock_stream_manager.send_raw_event = AsyncMock()

        await self.speech_agent.initialize()

        # Verify initialize_stream was called
        self.speech_agent.bedrock_stream_manager.initialize_stream.assert_called_once()
        # Verify send_raw_event was called for conversation initialization
        self.speech_agent.bedrock_stream_manager.send_raw_event.assert_called()

    @pytest.mark.asyncio
    async def test_process_tool_use_delegation(self):
        """Test that process_tool_use is properly delegated to tool_handler."""
        # Mock the tool handler's process_tool_use method
        self.speech_agent.tool_handler.process_tool_use = AsyncMock(
            return_value={"result": "test"}
        )

        result = await self.speech_agent.process_tool_use(
            "testTool", {"content": "test"}
        )

        # Verify delegation occurred
        self.speech_agent.tool_handler.process_tool_use.assert_called_once_with(
            "testTool", {"content": "test"}
        )
        assert result == {"result": "test"}

    @pytest.mark.asyncio
    async def test_start_conversation(self):
        """Test the start_conversation method."""
        # Mock the audio streamer's start_streaming method
        self.speech_agent.audio_streamer.start_streaming = AsyncMock()
        self.speech_agent.audio_streamer.stop_streaming = AsyncMock()

        await self.speech_agent.start_conversation()

        # Verify start_streaming was called
        self.speech_agent.audio_streamer.start_streaming.assert_called_once()
        # Verify stop_streaming was called in finally block
        self.speech_agent.audio_streamer.stop_streaming.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_conversation(self):
        """Test the stop_conversation method."""
        # Mock the audio streamer's stop_streaming method
        self.speech_agent.audio_streamer.stop_streaming = AsyncMock()

        await self.speech_agent.stop_conversation()

        # Verify stop_streaming was called
        self.speech_agent.audio_streamer.stop_streaming.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_conversation_with_keyboard_interrupt(self):
        """Test that start_conversation handles KeyboardInterrupt gracefully."""
        # Mock the audio streamer to raise KeyboardInterrupt
        self.speech_agent.audio_streamer.start_streaming = AsyncMock(
            side_effect=KeyboardInterrupt()
        )
        self.speech_agent.audio_streamer.stop_streaming = AsyncMock()

        # Should not raise exception
        await self.speech_agent.start_conversation()

        # Verify cleanup was called
        self.speech_agent.audio_streamer.stop_streaming.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_conversation_with_exception(self):
        """Test that start_conversation handles general exceptions gracefully."""
        # Mock the audio streamer to raise a general exception
        self.speech_agent.audio_streamer.start_streaming = AsyncMock(
            side_effect=Exception("Test error")
        )
        self.speech_agent.audio_streamer.stop_streaming = AsyncMock()

        # Should handle exception without re-raising
        try:
            await self.speech_agent.start_conversation()
        except Exception:
            pytest.fail("start_conversation should handle exceptions gracefully")

        # Verify cleanup was called
        self.speech_agent.audio_streamer.stop_streaming.assert_called_once()
