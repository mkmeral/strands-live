import json

import pytest

from strands_live.bedrock_streamer import BedrockStreamManager
from strands_live.tool_handler import ToolHandler


class TestBedrockStreamManager:
    """Test cases for the BedrockStreamManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_handler = ToolHandler()
        self.stream_manager = BedrockStreamManager(
            model_id="test-model", region="test-region", tool_handler=self.tool_handler
        )

    def test_initialization(self):
        """Test that BedrockStreamManager initializes correctly."""
        assert self.stream_manager.model_id == "test-model"
        assert self.stream_manager.region == "test-region"
        assert self.stream_manager.tool_handler == self.tool_handler
        assert self.stream_manager.is_active is False
        assert self.stream_manager.prompt_name is not None
        assert self.stream_manager.content_name is not None
        assert self.stream_manager.audio_content_name is not None

    def test_initialization_without_tool_handler(self):
        """Test initialization works without a tool handler."""
        manager = BedrockStreamManager()
        assert manager.tool_handler is None
        assert manager.model_id == "amazon.nova-sonic-v1:0"
        assert manager.region == "us-east-1"

    def test_start_prompt_event_structure(self):
        """Test that start_prompt generates valid JSON."""
        prompt_event = self.stream_manager.start_prompt()

        # Should be valid JSON
        data = json.loads(prompt_event)
        assert "event" in data
        assert "promptStart" in data["event"]
        assert "promptName" in data["event"]["promptStart"]
        assert (
            data["event"]["promptStart"]["promptName"]
            == self.stream_manager.prompt_name
        )

    def test_tool_result_event_with_dict(self):
        """Test tool_result_event with dictionary content."""
        content = {"status": "success", "data": "test"}
        event = self.stream_manager.tool_result_event("test-content", content, "TOOL")

        data = json.loads(event)
        assert "event" in data
        assert "toolResult" in data["event"]
        assert (
            data["event"]["toolResult"]["promptName"] == self.stream_manager.prompt_name
        )
        assert data["event"]["toolResult"]["contentName"] == "test-content"

        # Content should be JSON string of the dictionary
        content_data = json.loads(data["event"]["toolResult"]["content"])
        assert content_data == content

    def test_tool_result_event_with_string(self):
        """Test tool_result_event with string content."""
        content = "simple string content"
        event = self.stream_manager.tool_result_event("test-content", content, "TOOL")

        data = json.loads(event)
        assert data["event"]["toolResult"]["content"] == content

    def test_add_audio_chunk(self):
        """Test adding audio chunks to the queue."""
        audio_data = b"fake audio data"

        # Queue should be empty initially
        assert self.stream_manager.audio_input_queue.empty()

        # Add audio chunk
        self.stream_manager.add_audio_chunk(audio_data)

        # Queue should now have one item
        assert not self.stream_manager.audio_input_queue.empty()

        # Get the item and verify its structure
        item = self.stream_manager.audio_input_queue.get_nowait()
        assert item["audio_bytes"] == audio_data
        assert item["prompt_name"] == self.stream_manager.prompt_name
        assert item["content_name"] == self.stream_manager.audio_content_name

    @pytest.mark.asyncio
    async def test_send_raw_event_when_not_active(self):
        """Test that send_raw_event handles inactive stream gracefully."""
        self.stream_manager.is_active = False
        self.stream_manager.stream_response = None

        # Should not raise exception
        await self.stream_manager.send_raw_event('{"test": "event"}')

    def test_event_templates_are_valid_json(self):
        """Test that all event templates generate valid JSON."""
        templates_to_test = [
            (self.stream_manager.START_SESSION_EVENT, {}),
            (self.stream_manager.CONTENT_START_EVENT, ("prompt", "content")),
            (
                self.stream_manager.AUDIO_EVENT_TEMPLATE,
                ("prompt", "content", "base64data"),
            ),
            (
                self.stream_manager.TEXT_CONTENT_START_EVENT,
                ("prompt", "content", "USER"),
            ),
            (self.stream_manager.TEXT_INPUT_EVENT, ("prompt", "content", "text")),
            (
                self.stream_manager.TOOL_CONTENT_START_EVENT,
                ("prompt", "content", "tool-id"),
            ),
            (self.stream_manager.CONTENT_END_EVENT, ("prompt", "content")),
            (self.stream_manager.PROMPT_END_EVENT, ("prompt",)),
            (self.stream_manager.SESSION_END_EVENT, {}),
        ]

        for template, args in templates_to_test:
            if args:
                event_json = template % args
            else:
                event_json = template

            # Should be valid JSON
            try:
                json.loads(event_json)
            except json.JSONDecodeError:
                pytest.fail(f"Template produced invalid JSON: {template}")

    def test_prompt_name_consistency(self):
        """Test that prompt names are consistent across the manager."""
        # All content should use the same prompt name
        assert self.stream_manager.prompt_name is not None

        # Generate some events and verify they use the same prompt name
        prompt_event = json.loads(self.stream_manager.start_prompt())
        assert (
            prompt_event["event"]["promptStart"]["promptName"]
            == self.stream_manager.prompt_name
        )
