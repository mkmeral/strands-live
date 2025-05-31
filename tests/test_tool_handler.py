import asyncio
import pytest
import json
import pytz
from unittest.mock import patch, Mock
from src.tool_handler import ToolHandler
from src.tool_handler_base import ToolHandlerBase


class TestToolHandler:
    """Test cases for the ToolHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_handler = ToolHandler()

    def test_inheritance(self):
        """Test that ToolHandler properly inherits from ToolHandlerBase."""
        assert isinstance(self.tool_handler, ToolHandlerBase)
        assert hasattr(self.tool_handler, 'process_tool_use')
        assert hasattr(self.tool_handler, 'get_supported_tools')
        assert hasattr(self.tool_handler, 'get_tool_schema')

    def test_initialization_with_default_config(self):
        """Test initialization with default configuration."""
        handler = ToolHandler()
        
        # Check default configuration
        assert handler.get_config('timezone') == 'America/Los_Angeles'
        assert 'order_statuses' in handler.config
        assert 'status_weights' in handler.config
        assert len(handler.get_config('order_statuses')) == 8
        assert len(handler.get_config('status_weights')) == 8

    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        custom_config = {
            'timezone': 'Europe/London',
            'order_statuses': ['Custom Status 1', 'Custom Status 2'],
            'status_weights': [50, 50]
        }
        handler = ToolHandler(custom_config)
        
        assert handler.get_config('timezone') == 'Europe/London'
        assert handler.get_config('order_statuses') == ['Custom Status 1', 'Custom Status 2']
        assert handler.get_config('status_weights') == [50, 50]

    def test_get_supported_tools(self):
        """Test getting supported tools list."""
        tools = self.tool_handler.get_supported_tools()
        
        assert isinstance(tools, list)
        assert "getDateAndTimeTool" in tools
        assert "trackOrderTool" in tools
        assert len(tools) == 2

    def test_get_tool_schema_date_time(self):
        """Test getting schema for date/time tool."""
        schema = self.tool_handler.get_tool_schema("getDateAndTimeTool")
        
        assert schema is not None
        assert schema["name"] == "getDateAndTimeTool"
        assert "description" in schema
        assert "parameters" in schema
        assert "returns" in schema
        
        # Check return schema structure
        returns = schema["returns"]
        expected_keys = ["formattedTime", "date", "year", "month", "day", "dayOfWeek", "timezone"]
        for key in expected_keys:
            assert key in returns

    def test_get_tool_schema_track_order(self):
        """Test getting schema for order tracking tool."""
        schema = self.tool_handler.get_tool_schema("trackOrderTool")
        
        assert schema is not None
        assert schema["name"] == "trackOrderTool"
        assert "description" in schema
        assert "parameters" in schema
        assert "returns" in schema
        
        # Check parameter schema - now using new format
        params = schema["parameters"]
        assert "properties" in params
        assert "orderId" in params["properties"]
        assert "requestNotifications" in params["properties"]

    def test_get_tool_schema_unknown_tool(self):
        """Test getting schema for unknown tool."""
        schema = self.tool_handler.get_tool_schema("unknownTool")
        assert schema is None

    def test_is_tool_supported(self):
        """Test tool support checking with new method."""
        # Test supported tools
        assert self.tool_handler.is_tool_supported("getDateAndTimeTool") is True
        assert self.tool_handler.is_tool_supported("trackOrderTool") is True
        
        # Test case insensitive
        assert self.tool_handler.is_tool_supported("GETDATEANDTIMETOOL") is True
        assert self.tool_handler.is_tool_supported("trackordertool") is True
        
        # Test unsupported tool
        assert self.tool_handler.is_tool_supported("unknownTool") is False

    @pytest.mark.asyncio
    async def test_get_date_and_time_default_timezone(self):
        """Test the date and time tool with default timezone."""
        result = await self.tool_handler._get_date_and_time()
        
        assert "formattedTime" in result
        assert "date" in result
        assert "year" in result
        assert "month" in result
        assert "day" in result
        assert "dayOfWeek" in result
        assert "timezone" in result
        assert result["timezone"] == "Los_Angeles"  # Extracted from America/Los_Angeles

    @pytest.mark.asyncio
    async def test_get_date_and_time_custom_timezone(self):
        """Test the date and time tool with custom timezone."""
        custom_config = {'timezone': 'Europe/London'}
        handler = ToolHandler(custom_config)
        
        result = await handler._get_date_and_time()
        
        assert result["timezone"] == "London"

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
    async def test_track_order_with_dict_content(self):
        """Test order tracking with dictionary content instead of JSON string."""
        tool_use_content = {
            "content": {"orderId": "67890"},
            "requestNotifications": False
        }
        
        result = await self.tool_handler._track_order(tool_use_content)
        
        assert "orderStatus" in result
        assert "orderNumber" in result
        assert result["orderNumber"] == "67890"

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
    async def test_track_order_custom_statuses(self):
        """Test order tracking with custom status configuration."""
        custom_config = {
            'order_statuses': ['Custom Status 1', 'Custom Status 2'],
            'status_weights': [50, 50]
        }
        handler = ToolHandler(custom_config)
        
        tool_use_content = {
            "content": json.dumps({"orderId": "CUSTOM123"}),
            "requestNotifications": False
        }
        
        result = await handler._track_order(tool_use_content)
        
        assert result["orderStatus"] in ['Custom Status 1', 'Custom Status 2']

    @pytest.mark.asyncio
    async def test_process_tool_use_date_time(self):
        """Test processing the date and time tool."""
        result = await self.tool_handler.process_tool_use("getDateAndTimeTool", {})
        
        assert "formattedTime" in result
        assert "timezone" in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_process_tool_use_track_order(self):
        """Test processing the order tracking tool."""
        tool_use_content = {
            "content": json.dumps({"orderId": "PROCESS123"}),
            "requestNotifications": False
        }
        
        result = await self.tool_handler.process_tool_use("trackOrderTool", tool_use_content)
        
        assert "orderStatus" in result
        assert "orderNumber" in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_process_tool_use_unknown_tool(self):
        """Test processing an unknown tool."""
        result = await self.tool_handler.process_tool_use("unknownTool", {})
        
        assert "error" in result
        # Due to validation, unknown tools now return validation error
        assert "Tool execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_tool_request_valid_date_time(self):
        """Test validation for valid date/time tool request."""
        is_valid = await self.tool_handler.validate_tool_request("getDateAndTimeTool", {})
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_tool_request_valid_track_order(self):
        """Test validation for valid order tracking request."""
        tool_use_content = {
            "content": json.dumps({"orderId": "VALID123"})
        }
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", tool_use_content)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_tool_request_invalid_track_order_no_content(self):
        """Test validation for invalid order tracking request without content."""
        tool_use_content = {}
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", tool_use_content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_tool_request_invalid_track_order_no_order_id(self):
        """Test validation for invalid order tracking request without order ID."""
        tool_use_content = {
            "content": json.dumps({"otherField": "value"})
        }
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", tool_use_content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_tool_request_invalid_json(self):
        """Test validation with invalid JSON content."""
        tool_use_content = {
            "content": "invalid json content"
        }
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", tool_use_content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_tool_request_unsupported_tool(self):
        """Test validation for unsupported tool."""
        is_valid = await self.tool_handler.validate_tool_request("unsupportedTool", {})
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_error_handling_in_process_tool_use(self):
        """Test error handling in process_tool_use method."""
        # Mock the _get_date_and_time method to raise an exception
        with patch.object(self.tool_handler, '_get_date_and_time', side_effect=ValueError("Test error")):
            result = await self.tool_handler.process_tool_use("getDateAndTimeTool", {})
            
            assert "error" in result
            assert "Tool execution failed" in result["error"]
            assert "Test error" in result["error"]
            assert result["errorType"] == "ValueError"

    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test that validation errors are properly handled."""
        # This should trigger validation failure
        tool_use_content = {
            "content": json.dumps({})  # Missing orderId
        }
        
        result = await self.tool_handler.process_tool_use("trackOrderTool", tool_use_content)
        
        assert "error" in result
        assert "Tool execution failed" in result["error"]
        assert "Invalid tool request" in result["error"]

    def test_get_handler_info(self):
        """Test getting handler information."""
        info = self.tool_handler.get_handler_info()
        
        assert info["handler_type"] == "ToolHandler"
        assert "getDateAndTimeTool" in info["supported_tools"]
        assert "trackOrderTool" in info["supported_tools"]
        assert "timezone" in info["config_keys"]
        assert "order_statuses" in info["config_keys"]
        assert "status_weights" in info["config_keys"]

    def test_config_management(self):
        """Test configuration management methods."""
        # Test setting and getting config
        self.tool_handler.set_config("test_key", "test_value")
        assert self.tool_handler.get_config("test_key") == "test_value"
        
        # Test default values
        assert self.tool_handler.get_config("nonexistent_key", "default") == "default"
        
        # Test overriding existing config
        self.tool_handler.set_config("timezone", "UTC")
        assert self.tool_handler.get_config("timezone") == "UTC"

    def test_get_bedrock_tool_config(self):
        """Test getting Bedrock-compatible tool configuration."""
        config = self.tool_handler.get_bedrock_tool_config()
        
        assert "tools" in config
        assert len(config["tools"]) == 2
        
        # Check first tool structure
        first_tool = config["tools"][0]
        assert "toolSpec" in first_tool
        assert "name" in first_tool["toolSpec"]
        assert "description" in first_tool["toolSpec"]
        assert "inputSchema" in first_tool["toolSpec"]
        assert "json" in first_tool["toolSpec"]["inputSchema"]
        
        # Validate JSON schema format
        import json
        schema = json.loads(first_tool["toolSpec"]["inputSchema"]["json"])
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_bedrock_tool_config_contains_correct_tools(self):
        """Test that Bedrock config contains the correct tools."""
        config = self.tool_handler.get_bedrock_tool_config()
        
        tool_names = [tool["toolSpec"]["name"] for tool in config["tools"]]
        assert "getDateAndTimeTool" in tool_names
        assert "trackOrderTool" in tool_names

    def test_bedrock_tool_config_schema_conversion(self):
        """Test that tool schemas are properly converted to Bedrock format."""
        config = self.tool_handler.get_bedrock_tool_config()
        
        # Find the order tracking tool
        order_tool = None
        for tool in config["tools"]:
            if tool["toolSpec"]["name"] == "trackOrderTool":
                order_tool = tool
                break
        
        assert order_tool is not None
        
        # Check the converted schema
        import json
        schema = json.loads(order_tool["toolSpec"]["inputSchema"]["json"])
        
        assert "orderId" in schema["properties"]
        assert "requestNotifications" in schema["properties"]
        assert "orderId" in schema["required"]
        assert schema["properties"]["orderId"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_track_order_new_format(self):
        """Test order tracking with new direct parameter format."""
        tool_use_content = {
            "orderId": "NEW123",
            "requestNotifications": True
        }
        
        result = await self.tool_handler._track_order(tool_use_content)
        
        assert "orderStatus" in result
        assert "orderNumber" in result
        assert result["orderNumber"] == "NEW123"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_track_order_format_compatibility(self):
        """Test that both old and new formats produce the same result."""
        order_id = "COMPAT123"
        
        # Old format
        old_format = {
            "content": json.dumps({"orderId": order_id}),
            "requestNotifications": False
        }
        
        # New format  
        new_format = {
            "orderId": order_id,
            "requestNotifications": False
        }
        
        result_old = await self.tool_handler._track_order(old_format)
        result_new = await self.tool_handler._track_order(new_format)
        
        # Results should be identical (deterministic)
        assert result_old["orderStatus"] == result_new["orderStatus"]
        assert result_old["orderNumber"] == result_new["orderNumber"]

    @pytest.mark.asyncio
    async def test_validate_tool_request_new_format(self):
        """Test validation with new direct parameter format."""
        # Valid new format
        valid_new_format = {
            "orderId": "VALID123",
            "requestNotifications": False
        }
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", valid_new_format)
        assert is_valid is True
        
        # Invalid new format - missing orderId
        invalid_new_format = {
            "requestNotifications": False
        }
        
        is_valid = await self.tool_handler.validate_tool_request("trackOrderTool", invalid_new_format)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_timezone_configuration_impact(self):
        """Test that timezone configuration affects date/time output."""
        # Set custom timezone
        self.tool_handler.set_config("timezone", "Asia/Tokyo")
        
        result = await self.tool_handler._get_date_and_time()
        
        assert result["timezone"] == "Tokyo"