from unittest.mock import Mock, patch

import pytest

from strands_live.audio_streamer import AudioStreamer


class TestAudioStreamer:
    """Test cases for the AudioStreamer class."""

    @patch("strands_live.audio_streamer.pyaudio.PyAudio")
    @patch("asyncio.get_event_loop")
    def test_initialization(self, mock_get_event_loop, mock_pyaudio):
        """Test that AudioStreamer initializes correctly."""
        # Mock event loop
        mock_loop = Mock()
        mock_get_event_loop.return_value = mock_loop

        # Mock PyAudio and its streams
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance

        mock_input_stream = Mock()
        mock_output_stream = Mock()
        mock_pyaudio_instance.open.side_effect = [mock_input_stream, mock_output_stream]

        # Mock bedrock stream manager
        mock_bedrock_manager = Mock()

        # Create AudioStreamer with mock agent
        mock_agent = Mock()
        mock_agent.prompt_name = "test_prompt"
        mock_agent.audio_content_name = "test_audio_content"

        audio_streamer = AudioStreamer(mock_bedrock_manager, agent=mock_agent)

        # Verify initialization
        assert audio_streamer.bedrock_stream_manager == mock_bedrock_manager
        assert audio_streamer.is_streaming is False
        assert audio_streamer.p == mock_pyaudio_instance
        assert audio_streamer.input_stream == mock_input_stream
        assert audio_streamer.output_stream == mock_output_stream
        assert audio_streamer.loop == mock_loop

    @patch("strands_live.audio_streamer.pyaudio.PyAudio")
    @pytest.mark.asyncio
    async def test_process_input_audio(self, mock_pyaudio):
        """Test processing input audio."""
        # Mock PyAudio
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.open.return_value = Mock()

        # Mock bedrock stream manager
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.add_audio_chunk = Mock()

        # Create AudioStreamer with mock agent
        mock_agent = Mock()
        mock_agent.prompt_name = "test_prompt"
        mock_agent.audio_content_name = "test_audio_content"

        audio_streamer = AudioStreamer(mock_bedrock_manager, agent=mock_agent)
        audio_streamer.is_streaming = True

        # Test processing audio data
        test_audio_data = b"test audio data"
        await audio_streamer.process_input_audio(test_audio_data)

        # Verify audio was passed to bedrock manager with agent identifiers
        mock_bedrock_manager.add_audio_chunk.assert_called_once_with(
            test_audio_data, "test_prompt", "test_audio_content"
        )

    @patch("strands_live.audio_streamer.pyaudio.PyAudio")
    @pytest.mark.asyncio
    async def test_process_input_audio_error_handling(self, mock_pyaudio):
        """Test error handling in process_input_audio."""
        # Mock PyAudio
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.open.return_value = Mock()

        # Mock bedrock stream manager to raise exception
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.add_audio_chunk = Mock(side_effect=Exception("Test error"))

        # Create AudioStreamer with mock agent
        mock_agent = Mock()
        mock_agent.prompt_name = "test_prompt"
        mock_agent.audio_content_name = "test_audio_content"

        audio_streamer = AudioStreamer(mock_bedrock_manager, agent=mock_agent)
        audio_streamer.is_streaming = True

        # Test processing audio data with error - should not raise exception
        test_audio_data = b"test audio data"
        await audio_streamer.process_input_audio(test_audio_data)

        # Verify the method was called despite the error
        mock_bedrock_manager.add_audio_chunk.assert_called_once_with(
            test_audio_data, "test_prompt", "test_audio_content"
        )

    @patch("strands_live.audio_streamer.pyaudio.PyAudio")
    @patch("asyncio.get_event_loop")
    def test_input_callback(self, mock_get_event_loop, mock_pyaudio):
        """Test the input callback function."""
        # Mock event loop
        mock_loop = Mock()
        mock_get_event_loop.return_value = mock_loop

        # Mock PyAudio
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.open.return_value = Mock()

        # Mock bedrock stream manager
        mock_bedrock_manager = Mock()

        # Create AudioStreamer with mock agent
        mock_agent = Mock()
        mock_agent.prompt_name = "test_prompt"
        mock_agent.audio_content_name = "test_audio_content"

        audio_streamer = AudioStreamer(mock_bedrock_manager, agent=mock_agent)
        audio_streamer.is_streaming = True

        # Mock asyncio.run_coroutine_threadsafe
        with patch("asyncio.run_coroutine_threadsafe") as mock_run_coroutine:
            # Test callback with audio data
            test_audio_data = b"test audio data"
            result = audio_streamer.input_callback(test_audio_data, 1024, None, None)

            # Verify the callback scheduled a coroutine
            mock_run_coroutine.assert_called_once()

            # Verify return value (pyaudio.paContinue is actually 0)
            assert result == (None, 0)

    @patch("strands_live.audio_streamer.pyaudio.PyAudio")
    @patch("asyncio.get_event_loop")
    def test_input_callback_when_not_streaming(self, mock_get_event_loop, mock_pyaudio):
        """Test the input callback when not streaming."""
        # Mock event loop
        mock_loop = Mock()
        mock_get_event_loop.return_value = mock_loop

        # Mock PyAudio
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.open.return_value = Mock()

        # Mock bedrock stream manager
        mock_bedrock_manager = Mock()

        # Create AudioStreamer with mock agent
        mock_agent = Mock()
        mock_agent.prompt_name = "test_prompt"
        mock_agent.audio_content_name = "test_audio_content"

        audio_streamer = AudioStreamer(mock_bedrock_manager, agent=mock_agent)
        audio_streamer.is_streaming = False  # Not streaming

        # Mock asyncio.run_coroutine_threadsafe
        with patch("asyncio.run_coroutine_threadsafe") as mock_run_coroutine:
            # Test callback with audio data
            test_audio_data = b"test audio data"
            result = audio_streamer.input_callback(test_audio_data, 1024, None, None)

            # Verify no coroutine was scheduled when not streaming
            mock_run_coroutine.assert_not_called()

            # Verify return value (pyaudio.paContinue is actually 0)
            assert result == (None, 0)
