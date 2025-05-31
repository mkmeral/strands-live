"""
Tests for StrandsToolHandler.

This module contains comprehensive tests for the StrandsToolHandler,
which integrates the Strands Agents SDK with our speech-based agent system.
"""

import asyncio
import json
import logging
import pytest
from unittest.mock import patch, MagicMock

from src.strands_tool_handler import StrandsToolHandler


class TestStrandsToolHandler:
    """Test suite for StrandsToolHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create a StrandsToolHandler instance for testing."""
        return StrandsToolHandler()
    
    def test_initialization(self, handler):
        """Test handler initialization."""
        assert isinstance(handler, StrandsToolHandler)
        assert hasattr(handler, 'registry')
        assert hasattr(handler, 'config')
    
    def test_get_supported_tools(self, handler):
        """Test getting supported tools."""
        tools = handler.get_supported_tools()
        assert isinstance(tools, list)
        assert 'current_time' in tools
        assert len(tools) >= 1
    
    def test_get_tool_schema(self, handler):
        """Test getting tool schema."""
        schema = handler.get_tool_schema('current_time')
        
        assert schema is not None
        assert 'name' in schema
        assert 'description' in schema
        assert 'parameters' in schema
        
        assert schema['name'] == 'current_time'
        assert isinstance(schema['description'], str)
        assert len(schema['description']) > 0
        
        # Check parameters schema
        params = schema['parameters']
        assert isinstance(params, dict)
        assert 'type' in params
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'timezone' in params['properties']
    
    def test_get_tool_schema_unknown_tool(self, handler):
        """Test getting schema for unknown tool."""
        schema = handler.get_tool_schema('nonexistent_tool')
        assert schema is None
    
    def test_is_tool_supported(self, handler):
        """Test tool support checking."""
        assert handler.is_tool_supported('current_time') is True
        assert handler.is_tool_supported('nonexistent_tool') is False
    
    @pytest.mark.asyncio
    async def test_process_tool_use_no_params(self, handler):
        """Test tool execution with no parameters."""
        result = await handler.process_tool_use('current_time', {})
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'content' in result
        assert result['status'] == 'success'
        assert isinstance(result['content'], list)
        assert len(result['content']) > 0
        assert 'text' in result['content'][0]
        
        # Verify the result looks like a timestamp
        timestamp = result['content'][0]['text']
        assert isinstance(timestamp, str)
        assert 'T' in timestamp  # ISO format
        assert '+' in timestamp or 'Z' in timestamp  # Timezone info
    
    @pytest.mark.asyncio
    async def test_process_tool_use_with_timezone(self, handler):
        """Test tool execution with timezone parameter."""
        result = await handler.process_tool_use('current_time', {'timezone': 'US/Pacific'})
        
        assert result['status'] == 'success'
        timestamp = result['content'][0]['text']
        
        # Pacific time should end with -07:00 or -08:00 depending on DST
        assert timestamp.endswith('-07:00') or timestamp.endswith('-08:00')
    
    @pytest.mark.asyncio
    async def test_process_tool_use_europe_timezone(self, handler):
        """Test tool execution with European timezone."""
        result = await handler.process_tool_use('current_time', {'timezone': 'Europe/London'})
        
        assert result['status'] == 'success'
        timestamp = result['content'][0]['text']
        
        # London time should end with +00:00 or +01:00 depending on DST
        assert timestamp.endswith('+00:00') or timestamp.endswith('+01:00')
    
    @pytest.mark.asyncio
    async def test_process_tool_use_invalid_tool(self, handler):
        """Test tool execution with invalid tool name."""
        result = await handler.process_tool_use('nonexistent_tool', {})
        
        assert result['status'] == 'error'
        assert 'Tool \'nonexistent_tool\' not found' in result['content'][0]['text']
    
    def test_get_bedrock_tool_config(self, handler):
        """Test getting Bedrock-compatible tool configuration."""
        config = handler.get_bedrock_tool_config()
        
        assert isinstance(config, dict)
        assert 'tools' in config
        assert isinstance(config['tools'], list)
        assert len(config['tools']) >= 1
        
        # Check the first tool (current_time)
        tool = config['tools'][0]
        assert 'toolSpec' in tool
        
        tool_spec = tool['toolSpec']
        assert 'name' in tool_spec
        assert 'description' in tool_spec
        assert 'inputSchema' in tool_spec
        
        assert tool_spec['name'] == 'current_time'
        assert isinstance(tool_spec['description'], str)
        
        # Check input schema format
        input_schema = tool_spec['inputSchema']
        assert 'json' in input_schema
        assert isinstance(input_schema['json'], str)
        
        # Parse the JSON to verify it's valid
        parsed_schema = json.loads(input_schema['json'])
        assert parsed_schema['type'] == 'object'
        assert 'properties' in parsed_schema
        assert 'timezone' in parsed_schema['properties']
    
    def test_get_handler_info(self, handler):
        """Test getting handler information."""
        info = handler.get_handler_info()
        
        assert isinstance(info, dict)
        assert 'handler_type' in info
        assert 'supported_tools' in info
        assert 'total_tools' in info
        assert 'strands_registry_info' in info
        assert 'config' in info
        
        assert info['handler_type'] == 'StrandsToolHandler'
        assert isinstance(info['supported_tools'], list)
        assert 'current_time' in info['supported_tools']
        assert info['total_tools'] >= 1
        
        registry_info = info['strands_registry_info']
        assert 'registry_tools' in registry_info
        assert 'dynamic_tools' in registry_info
    
    def test_add_strands_tool_invalid(self, handler):
        """Test adding an invalid Strands tool."""
        def invalid_tool():
            return "not a tool"
        
        with pytest.raises(ValueError, match="Tool function must be decorated with @tool"):
            handler.add_strands_tool(invalid_tool)
    
    def test_inheritance_from_base(self, handler):
        """Test that StrandsToolHandler inherits from ToolHandlerBase."""
        from src.tool_handler_base import ToolHandlerBase
        assert isinstance(handler, ToolHandlerBase)
    
    def test_configuration_persistence(self, handler):
        """Test that configuration is properly maintained."""
        # Test default configuration
        assert handler.get_config('test_key', 'default') == 'default'
        
        # Test setting configuration
        handler.set_config('test_key', 'test_value')
        assert handler.get_config('test_key') == 'test_value'
    
    @pytest.mark.asyncio
    async def test_error_handling_with_exception(self, handler):
        """Test error handling when tool execution raises an exception."""
        # Mock the registry to simulate an exception
        original_registry = handler.registry.registry
        mock_tool = MagicMock()
        mock_tool.invoke.side_effect = Exception("Simulated error")
        
        handler.registry.registry = {'current_time': mock_tool}
        
        try:
            result = await handler.process_tool_use('current_time', {})
            assert result['status'] == 'error'
            assert 'Error executing Strands tool' in result['content'][0]['text']
            assert 'Simulated error' in result['content'][0]['text']
        finally:
            # Restore original registry
            handler.registry.registry = original_registry
    
    def test_schema_conversion_with_bedrock_format(self, handler):
        """Test that schemas are properly converted to Bedrock format."""
        schema = handler.get_tool_schema('current_time')
        converted = handler._convert_schema_to_bedrock_format(schema['parameters'])
        
        # Should already be in correct format from Strands
        assert 'type' in converted
        assert 'properties' in converted
        assert converted['type'] == 'object'
        assert 'timezone' in converted['properties']
        
        # Verify timezone property structure
        timezone_prop = converted['properties']['timezone']
        assert 'type' in timezone_prop
        assert 'description' in timezone_prop
        assert timezone_prop['type'] == 'string'
    
    def test_concurrent_tool_execution(self, handler):
        """Test that multiple tool calls can be executed concurrently."""
        async def run_concurrent_tools():
            tasks = []
            for i in range(3):
                task = handler.process_tool_use('current_time', {})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert result['status'] == 'success'
                assert 'content' in result
            
            return results
        
        # Run the concurrent test
        results = asyncio.run(run_concurrent_tools())
        assert len(results) == 3
    
    def test_tool_validation_compatibility(self, handler):
        """Test that tool validation works correctly."""
        # Valid tool should pass validation
        asyncio.run(self._test_validation_helper(handler, 'current_time', {}, True))
        
        # Invalid tool should fail validation
        asyncio.run(self._test_validation_helper(handler, 'nonexistent_tool', {}, False))
    
    async def _test_validation_helper(self, handler, tool_name, params, expected):
        """Helper method for validation testing."""
        result = await handler.validate_tool_request(tool_name, params)
        assert result == expected
    
    def test_bedrock_integration_format(self, handler):
        """Test that the Bedrock integration format is correct."""
        config = handler.get_bedrock_tool_config()
        
        # Simulate what BedrockStreamManager would do
        for tool in config['tools']:
            tool_spec = tool['toolSpec']
            
            # This should not raise an exception
            input_schema = json.loads(tool_spec['inputSchema']['json'])
            
            # Verify the schema structure Bedrock expects
            assert isinstance(input_schema, dict)
            assert 'type' in input_schema
            assert input_schema['type'] == 'object'
            
            if 'properties' in input_schema:
                for prop_name, prop_def in input_schema['properties'].items():
                    assert isinstance(prop_def, dict)
                    assert 'type' in prop_def
                    assert 'description' in prop_def