"""
Example: Custom Tool Handler Implementation

This demonstrates how to create a custom tool handler using the ToolHandlerBase abstraction.
This example creates an "AdvancedToolHandler" with additional tools while maintaining
the same interface.
"""

import asyncio
import random
from typing import Dict, Any, List, Optional
from src.tool_handler_base import ToolHandlerBase


class AdvancedToolHandler(ToolHandlerBase):
    """
    Advanced tool handler with additional mathematical and utility tools.
    
    This demonstrates how to create alternative implementations of the tool handler
    while maintaining the same interface and contract.
    """
    
    def _initialize_handler(self) -> None:
        """Initialize the advanced tool handler."""
        # Set default configuration for advanced tools
        if 'math_precision' not in self.config:
            self.config['math_precision'] = 6
        
        if 'random_seed' not in self.config:
            self.config['random_seed'] = None

    async def process_tool_use(self, tool_name: str, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process tool use request and return the result."""
        # Validate the request first
        if not await self.validate_tool_request(tool_name, tool_use_content):
            return await self.handle_tool_error(tool_name, ValueError("Invalid tool request"))
        
        try:
            tool = tool_name.lower()
            
            if tool == "calculatortool":
                return await self._calculator(tool_use_content)
            elif tool == "randomnumbertool":
                return await self._random_number(tool_use_content)
            elif tool == "uuidgeneratortool":
                return await self._uuid_generator()
            elif tool == "texttransformtool":
                return await self._text_transform(tool_use_content)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "toolName": tool_name
                }
        except Exception as e:
            return await self.handle_tool_error(tool_name, e)

    def get_supported_tools(self) -> List[str]:
        """Get list of supported tools."""
        return [
            "calculatorTool",
            "randomNumberTool", 
            "uuidGeneratorTool",
            "textTransformTool"
        ]
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific tool."""
        schemas = {
            "calculatortool": {
                "name": "calculatorTool",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "expression": "string (mathematical expression)"
                },
                "returns": {
                    "result": "number",
                    "expression": "string"
                }
            },
            "randomnumbertool": {
                "name": "randomNumberTool",
                "description": "Generate random numbers within a range",
                "parameters": {
                    "min": "number (optional, default: 0)",
                    "max": "number (optional, default: 100)"
                },
                "returns": {
                    "random_number": "number",
                    "range": "string"
                }
            },
            "uuidgeneratortool": {
                "name": "uuidGeneratorTool",
                "description": "Generate a unique UUID",
                "parameters": {},
                "returns": {
                    "uuid": "string",
                    "version": "string"
                }
            },
            "texttransformtool": {
                "name": "textTransformTool",
                "description": "Transform text (uppercase, lowercase, reverse, etc.)",
                "parameters": {
                    "text": "string",
                    "transform": "string (upper, lower, reverse, title)"
                },
                "returns": {
                    "original_text": "string",
                    "transformed_text": "string",
                    "transform_type": "string"
                }
            }
        }
        
        return schemas.get(tool_name.lower())

    async def _calculator(self, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Simple calculator tool."""
        expression = tool_use_content.get("expression", "")
        
        if not expression:
            return {"error": "No expression provided"}
        
        try:
            # Simple evaluation (for demo purposes - in production use a safer evaluator)
            result = eval(expression)
            precision = self.get_config('math_precision', 6)
            
            if isinstance(result, float):
                result = round(result, precision)
            
            return {
                "result": result,
                "expression": expression,
                "precision": precision
            }
        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}

    async def _random_number(self, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Random number generator tool."""
        min_val = tool_use_content.get("min", 0)
        max_val = tool_use_content.get("max", 100)
        
        # Set seed if configured
        seed = self.get_config('random_seed')
        if seed is not None:
            random.seed(seed)
        
        random_num = random.randint(min_val, max_val)
        
        return {
            "random_number": random_num,
            "range": f"{min_val} to {max_val}",
            "seed_used": seed is not None
        }

    async def _uuid_generator(self) -> Dict[str, Any]:
        """UUID generator tool."""
        import uuid
        
        generated_uuid = str(uuid.uuid4())
        
        return {
            "uuid": generated_uuid,
            "version": "4",
            "format": "standard"
        }

    async def _text_transform(self, tool_use_content: Dict[str, Any]) -> Dict[str, Any]:
        """Text transformation tool."""
        text = tool_use_content.get("text", "")
        transform_type = tool_use_content.get("transform", "").lower()
        
        if not text:
            return {"error": "No text provided"}
        
        if not transform_type:
            return {"error": "No transform type specified"}
        
        transformed_text = text
        
        if transform_type == "upper":
            transformed_text = text.upper()
        elif transform_type == "lower":
            transformed_text = text.lower()
        elif transform_type == "reverse":
            transformed_text = text[::-1]
        elif transform_type == "title":
            transformed_text = text.title()
        else:
            return {"error": f"Unknown transform type: {transform_type}"}
        
        return {
            "original_text": text,
            "transformed_text": transformed_text,
            "transform_type": transform_type,
            "length": len(text)
        }

    async def validate_tool_request(self, tool_name: str, tool_use_content: Dict[str, Any]) -> bool:
        """Validate tool request with specific checks for advanced tools."""
        # First do base validation
        if not await super().validate_tool_request(tool_name, tool_use_content):
            return False
        
        # Additional validation for specific tools
        tool = tool_name.lower()
        
        if tool == "calculatortool":
            expression = tool_use_content.get("expression")
            if not expression or not isinstance(expression, str):
                return False
        elif tool == "texttransformtool":
            text = tool_use_content.get("text")
            transform = tool_use_content.get("transform")
            if not text or not transform:
                return False
            if transform.lower() not in ["upper", "lower", "reverse", "title"]:
                return False
        
        return True


async def demo_advanced_tool_handler():
    """Demonstrate the advanced tool handler."""
    print("🔧 Advanced Tool Handler Demo")
    print("=" * 40)
    
    # Create handler with custom configuration
    config = {
        'math_precision': 4,
        'random_seed': 42
    }
    handler = AdvancedToolHandler(config)
    
    # Show handler info
    info = handler.get_handler_info()
    print(f"Handler Type: {info['handler_type']}")
    print(f"Supported Tools: {', '.join(info['supported_tools'])}")
    print()
    
    # Test calculator
    print("📊 Calculator Tool:")
    result = await handler.process_tool_use("calculatorTool", {"expression": "2 + 3 * 4"})
    print(f"Expression: 2 + 3 * 4")
    print(f"Result: {result.get('result', 'Error')}")
    print()
    
    # Test random number
    print("🎲 Random Number Tool:")
    result = await handler.process_tool_use("randomNumberTool", {"min": 1, "max": 10})
    print(f"Range: 1 to 10")
    print(f"Random Number: {result.get('random_number', 'Error')}")
    print()
    
    # Test UUID generator
    print("🆔 UUID Generator Tool:")
    result = await handler.process_tool_use("uuidGeneratorTool", {})
    print(f"Generated UUID: {result.get('uuid', 'Error')}")
    print()
    
    # Test text transform
    print("📝 Text Transform Tool:")
    result = await handler.process_tool_use("textTransformTool", {
        "text": "Hello World", 
        "transform": "reverse"
    })
    print(f"Original: {result.get('original_text', 'Error')}")
    print(f"Transformed: {result.get('transformed_text', 'Error')}")
    print()
    
    # Test polymorphism - can be used as ToolHandlerBase
    from src.tool_handler_base import ToolHandlerBase
    base_handler: ToolHandlerBase = handler
    assert isinstance(base_handler, ToolHandlerBase)
    print("✅ Polymorphism: Can be used as ToolHandlerBase")
    
    print("🎉 Advanced Tool Handler Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_advanced_tool_handler())