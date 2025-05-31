import pytest
from unittest.mock import AsyncMock
from abc import ABC
from src.tool_handler_base import ToolHandlerBase


class MockToolHandler(ToolHandlerBase):
    """Mock implementation for testing the base class."""
    
    def _initialize_handler(self):
        self.initialized = True
        
    async def process_tool_use(self, tool_name, tool_use_content):
        if tool_name == "mock_tool":
            return {"result": "success", "tool": tool_name}
        return {"error": f"Unknown tool: {tool_name}"}
    
    def get_supported_tools(self):
        return ["mock_tool", "another_tool"]
    
    def get_tool_schema(self, tool_name):
        if tool_name.lower() == "mock_tool":
            return {
                "name": "mock_tool",
                "description": "A mock tool for testing",
                "parameters": {"param1": "string"}
            }
        return None


class TestToolHandlerBase:
    """Test cases for the ToolHandlerBase abstract class."""

    def test_abstract_class(self):
        """Test that ToolHandlerBase is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ToolHandlerBase()

    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        config = {"key1": "value1", "key2": 42}
        handler = MockToolHandler(config)
        
        assert handler.config == config
        assert handler.initialized is True
        
    def test_initialization_without_config(self):
        """Test initialization without configuration."""
        handler = MockToolHandler()
        
        assert handler.config == {}
        assert handler.initialized is True

    def test_get_config(self):
        """Test configuration getter methods."""
        config = {"test_key": "test_value", "number": 123}
        handler = MockToolHandler(config)
        
        # Test existing key
        assert handler.get_config("test_key") == "test_value"
        assert handler.get_config("number") == 123
        
        # Test non-existing key with default
        assert handler.get_config("missing_key", "default") == "default"
        assert handler.get_config("missing_key") is None

    def test_set_config(self):
        """Test configuration setter method."""
        handler = MockToolHandler()
        
        handler.set_config("new_key", "new_value")
        assert handler.get_config("new_key") == "new_value"
        
        # Test overwriting existing key
        handler.set_config("new_key", "updated_value")
        assert handler.get_config("new_key") == "updated_value"

    def test_is_tool_supported(self):
        """Test tool support checking."""
        handler = MockToolHandler()
        
        # Test supported tools
        assert handler.is_tool_supported("mock_tool") is True
        assert handler.is_tool_supported("another_tool") is True
        
        # Test case insensitive
        assert handler.is_tool_supported("MOCK_TOOL") is True
        assert handler.is_tool_supported("Mock_Tool") is True
        
        # Test unsupported tool
        assert handler.is_tool_supported("unknown_tool") is False

    def test_get_handler_info(self):
        """Test handler information method."""
        config = {"config_key": "config_value"}
        handler = MockToolHandler(config)
        
        info = handler.get_handler_info()
        
        assert info["handler_type"] == "MockToolHandler"
        assert info["supported_tools"] == ["mock_tool", "another_tool"]
        assert info["config_keys"] == ["config_key"]
        assert "description" in info

    @pytest.mark.asyncio
    async def test_validate_tool_request_supported(self):
        """Test validation for supported tools."""
        handler = MockToolHandler()
        
        # Test supported tool
        is_valid = await handler.validate_tool_request("mock_tool", {})
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_tool_request_unsupported(self):
        """Test validation for unsupported tools."""
        handler = MockToolHandler()
        
        # Test unsupported tool
        is_valid = await handler.validate_tool_request("unknown_tool", {})
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_handle_tool_error(self):
        """Test error handling method."""
        handler = MockToolHandler()
        
        error = ValueError("Test error message")
        result = await handler.handle_tool_error("test_tool", error)
        
        assert result["error"] == "Tool execution failed for test_tool: Test error message"
        assert result["toolName"] == "test_tool"
        assert result["errorType"] == "ValueError"

    @pytest.mark.asyncio
    async def test_process_tool_use_implementation(self):
        """Test that the abstract process_tool_use method is implemented."""
        handler = MockToolHandler()
        
        # Test successful tool execution
        result = await handler.process_tool_use("mock_tool", {})
        assert result["result"] == "success"
        assert result["tool"] == "mock_tool"
        
        # Test unknown tool
        result = await handler.process_tool_use("unknown_tool", {})
        assert "error" in result

    def test_get_supported_tools_implementation(self):
        """Test that get_supported_tools is implemented."""
        handler = MockToolHandler()
        tools = handler.get_supported_tools()
        
        assert isinstance(tools, list)
        assert "mock_tool" in tools
        assert "another_tool" in tools

    def test_get_tool_schema_implementation(self):
        """Test that get_tool_schema is implemented."""
        handler = MockToolHandler()
        
        # Test existing schema
        schema = handler.get_tool_schema("mock_tool")
        assert schema is not None
        assert schema["name"] == "mock_tool"
        assert "description" in schema
        assert "parameters" in schema
        
        # Test non-existing schema
        schema = handler.get_tool_schema("unknown_tool")
        assert schema is None

    def test_configuration_persistence(self):
        """Test that configuration changes persist."""
        handler = MockToolHandler({"initial": "value"})
        
        # Add new config
        handler.set_config("new_config", "new_value")
        
        # Verify both old and new config exist
        assert handler.get_config("initial") == "value"
        assert handler.get_config("new_config") == "new_value"
        
        # Verify config keys include both
        info = handler.get_handler_info()
        assert "initial" in info["config_keys"]
        assert "new_config" in info["config_keys"]

    @pytest.mark.asyncio
    async def test_error_handling_with_different_exceptions(self):
        """Test error handling with various exception types."""
        handler = MockToolHandler()
        
        # Test different exception types
        exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            KeyError("Key error")
        ]
        
        for exc in exceptions:
            result = await handler.handle_tool_error("test_tool", exc)
            assert result["errorType"] == type(exc).__name__
            assert str(exc) in result["error"]
            assert result["toolName"] == "test_tool"