import asyncio
import pytest
import json
from src.tool_handler import ToolHandler


class TestToolHandler:
    """Test cases for the ToolHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_handler = ToolHandler()

    @pytest.mark.asyncio
    async def test_get_date_and_time(self):
        """Test the date and time tool."""
        result = await self.tool_handler._get_date_and_time()
        
        assert "formattedTime" in result
        assert "date" in result
        assert "year" in result
        assert "month" in result
        assert "day" in result
        assert "dayOfWeek" in result
        assert "timezone" in result
        assert result["timezone"] == "PST"

    @pytest.mark.asyncio
    async def test_track_order_valid_id(self):
        """Test order tracking with a valid order ID."""
        tool_use_content = {
            "content": json.dumps({"orderId": "12345"}),
            "requestNotifications": False
        }
        
        result = await self.tool_handler._track_order(tool_use_content)
        
        assert "orderStatus" in result
        assert "orderNumber" in result
        assert result["orderNumber"] == "12345"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_track_order_invalid_id(self):
        """Test order tracking with an invalid order ID."""
        tool_use_content = {
            "content": json.dumps({"orderId": ""}),
            "requestNotifications": False
        }
        
        result = await self.tool_handler._track_order(tool_use_content)
        
        assert "error" in result
        assert result["error"] == "Invalid order ID format"

    @pytest.mark.asyncio
    async def test_process_tool_use_unknown_tool(self):
        """Test processing an unknown tool."""
        result = await self.tool_handler.process_tool_use("unknownTool", {})
        
        assert "error" in result
        assert "Unknown tool: unknownTool" in result["error"]
        assert result["toolName"] == "unknownTool"

    @pytest.mark.asyncio
    async def test_process_tool_use_date_time(self):
        """Test processing the date and time tool."""
        result = await self.tool_handler.process_tool_use("getDateAndTimeTool", {})
        
        assert "formattedTime" in result
        assert "timezone" in result
        assert result["timezone"] == "PST"

    @pytest.mark.asyncio
    async def test_track_order_deterministic(self):
        """Test that the same order ID always returns the same status."""
        tool_use_content = {
            "content": json.dumps({"orderId": "TEST123"}),
            "requestNotifications": False
        }
        
        result1 = await self.tool_handler._track_order(tool_use_content)
        result2 = await self.tool_handler._track_order(tool_use_content)
        
        # Same order ID should return same status
        assert result1["orderStatus"] == result2["orderStatus"]
        assert result1["orderNumber"] == result2["orderNumber"]

    @pytest.mark.asyncio
    async def test_track_order_with_notifications(self):
        """Test order tracking with notifications enabled."""
        tool_use_content = {
            "content": json.dumps({"orderId": "NOTIFY123"}),
            "requestNotifications": True
        }
        
        result = await self.tool_handler._track_order(tool_use_content)
        
        assert "orderNumber" in result
        assert result["orderNumber"] == "NOTIFY123"
        # Should have notification status unless delivered
        if result["orderStatus"] != "Delivered":
            assert "notificationStatus" in result
            assert "NOTIFY123" in result["notificationStatus"]