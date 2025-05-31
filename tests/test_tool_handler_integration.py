import json
from unittest.mock import AsyncMock, patch

import pytest

from strands_live.bedrock_streamer import BedrockStreamManager
from strands_live.speech_agent import SpeechAgent
from strands_live.tool_handler import ToolHandler
from strands_live.tool_handler_base import ToolHandlerBase


class TestToolHandlerIntegration:
    """Integration tests to ensure tool handler abstraction works with existing system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_handler = ToolHandler()

    def test_backward_compatibility_interface(self):
        """Test that the tool handler still provides the same interface as before."""
        # These are the methods that were available before
        assert hasattr(self.tool_handler, "process_tool_use")
        assert callable(self.tool_handler.process_tool_use)

        # The new interface methods should also be available
        assert hasattr(self.tool_handler, "get_supported_tools")
        assert hasattr(self.tool_handler, "get_tool_schema")
        assert hasattr(self.tool_handler, "is_tool_supported")

    @pytest.mark.asyncio
    async def test_backward_compatibility_functionality(self):
        """Test that existing tool functionality works exactly as before."""
        # Test date/time tool - should work exactly as before
        result = await self.tool_handler.process_tool_use("getDateAndTimeTool", {})

        # Same structure as before
        assert "formattedTime" in result
        assert "date" in result
        assert "year" in result
        assert "month" in result
        assert "day" in result
        assert "dayOfWeek" in result
        assert "timezone" in result

        # Test order tracking - should work exactly as before
        tool_use_content = {
            "content": json.dumps({"orderId": "12345"}),
            "requestNotifications": False,
        }

        result = await self.tool_handler.process_tool_use(
            "trackOrderTool", tool_use_content
        )

        # Same structure as before
        assert "orderStatus" in result
        assert "orderNumber" in result
        assert result["orderNumber"] == "12345"

    def test_bedrock_streamer_integration(self):
        """Test that BedrockStreamManager can still use the tool handler."""
        # Mock the AWS imports at the module level
        with patch("boto3.client"), patch("botocore.config.Config"):
            bedrock_manager = BedrockStreamManager(tool_handler=self.tool_handler)

            # Should be able to inject the tool handler
            assert bedrock_manager.tool_handler is self.tool_handler
            assert isinstance(bedrock_manager.tool_handler, ToolHandlerBase)

    def test_speech_agent_integration(self):
        """Test that SpeechAgent can still use the tool handler."""
        with (
            patch("strands_live.speech_agent.AudioStreamer"),
            patch("strands_live.speech_agent.BedrockStreamManager"),
        ):
            speech_agent = SpeechAgent()

            # Should create a tool handler instance
            assert hasattr(speech_agent, "tool_handler")
            assert isinstance(speech_agent.tool_handler, ToolHandlerBase)
            assert isinstance(speech_agent.tool_handler, ToolHandler)

    @pytest.mark.asyncio
    async def test_speech_agent_tool_delegation(self):
        """Test that SpeechAgent can still delegate to tool handler."""
        with (
            patch("strands_live.speech_agent.AudioStreamer"),
            patch("strands_live.speech_agent.BedrockStreamManager"),
        ):
            speech_agent = SpeechAgent()

            # Mock the tool handler's process_tool_use method
            speech_agent.tool_handler.process_tool_use = AsyncMock(
                return_value={"result": "test"}
            )

            # Should be able to call process_tool_use
            result = await speech_agent.process_tool_use(
                "testTool", {"content": "test"}
            )

            # Verify delegation occurred
            speech_agent.tool_handler.process_tool_use.assert_called_once_with(
                "testTool", {"content": "test"}
            )
            assert result == {"result": "test"}

    @pytest.mark.asyncio
    async def test_deterministic_behavior_preserved(self):
        """Test that deterministic behavior is preserved across the abstraction."""
        # Same order ID should always return the same result
        tool_use_content = {
            "content": json.dumps({"orderId": "DETERMINISTIC123"}),
            "requestNotifications": False,
        }

        # Test multiple times to ensure determinism
        results = []
        for _ in range(5):
            result = await self.tool_handler.process_tool_use(
                "trackOrderTool", tool_use_content
            )
            results.append(result)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result["orderStatus"] == first_result["orderStatus"]
            assert result["orderNumber"] == first_result["orderNumber"]

    def test_configuration_extensibility(self):
        """Test that configuration can be extended without breaking existing functionality."""
        # Custom configuration should not break existing tools
        custom_config = {
            "timezone": "Europe/London",
            "custom_setting": "custom_value",
            "order_statuses": ["New Status 1", "New Status 2"],
        }

        handler = ToolHandler(custom_config)

        # Should still support the same tools
        assert handler.is_tool_supported("getDateAndTimeTool")
        assert handler.is_tool_supported("trackOrderTool")

        # Should have custom configuration
        assert handler.get_config("custom_setting") == "custom_value"
        assert handler.get_config("timezone") == "Europe/London"

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that error handling is consistent with previous behavior."""
        # Unknown tool should still return error structure, but now through validation
        result = await self.tool_handler.process_tool_use("unknownTool", {})

        assert "error" in result
        # With the new validation, unknown tools are caught at validation stage
        assert "Tool execution failed" in result["error"]

    def test_new_features_dont_break_old_usage(self):
        """Test that new abstraction features don't interfere with old usage patterns."""
        # Old usage pattern should still work
        handler = ToolHandler()

        # These are new methods but shouldn't affect old functionality
        _tools = handler.get_supported_tools()
        _schema = handler.get_tool_schema("getDateAndTimeTool")
        _info = handler.get_handler_info()

        # Old functionality should remain unaffected
        assert callable(handler.process_tool_use)

    @pytest.mark.asyncio
    async def test_validation_does_not_break_valid_requests(self):
        """Test that new validation doesn't break previously valid requests."""
        # These requests worked before and should still work
        valid_requests = [
            ("getDateAndTimeTool", {}),
            (
                "trackOrderTool",
                {
                    "content": json.dumps({"orderId": "VALID123"}),
                    "requestNotifications": False,
                },
            ),
            (
                "trackOrderTool",
                {
                    "content": json.dumps({"orderId": "VALID456"}),
                    "requestNotifications": True,
                },
            ),
        ]

        for tool_name, content in valid_requests:
            result = await self.tool_handler.process_tool_use(tool_name, content)

            # Should not have validation errors
            assert "error" not in result or "Invalid tool request" not in result.get(
                "error", ""
            )

    @pytest.mark.asyncio
    async def test_polymorphism_support(self):
        """Test that the abstraction supports polymorphism correctly."""
        # Should be able to treat ToolHandler as ToolHandlerBase
        handler: ToolHandlerBase = ToolHandler()

        # All base methods should be available
        assert await handler.validate_tool_request("getDateAndTimeTool", {}) is True
        assert handler.is_tool_supported("getDateAndTimeTool") is True
        assert len(handler.get_supported_tools()) > 0

        # Should be able to process tools through base interface
        result = await handler.process_tool_use("getDateAndTimeTool", {})
        assert "formattedTime" in result

    def test_multiple_instances_independence(self):
        """Test that multiple tool handler instances are independent."""
        handler1 = ToolHandler({"timezone": "America/New_York"})
        handler2 = ToolHandler({"timezone": "Asia/Tokyo"})

        # Configuration should be independent
        assert handler1.get_config("timezone") == "America/New_York"
        assert handler2.get_config("timezone") == "Asia/Tokyo"

        # Changes to one shouldn't affect the other
        handler1.set_config("custom_key", "value1")
        handler2.set_config("custom_key", "value2")

        assert handler1.get_config("custom_key") == "value1"
        assert handler2.get_config("custom_key") == "value2"

    def test_interface_completeness(self):
        """Test that all abstract methods are properly implemented."""
        handler = ToolHandler()

        # All abstract methods should be implemented and callable
        abstract_methods = [
            "_initialize_handler",
            "process_tool_use",
            "get_supported_tools",
            "get_tool_schema",
        ]

        for method_name in abstract_methods:
            assert hasattr(handler, method_name)
            method = getattr(handler, method_name)
            assert callable(method)
