import json
from abc import ABC, abstractmethod
from typing import Any


class ToolHandlerBase(ABC):
    """
    Abstract base class for tool handlers.

    This class defines the interface that all tool handlers must implement.
    It provides a consistent API for tool processing while allowing different
    implementations to handle tools in their own way.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the tool handler with optional configuration.

        Args:
            config: Optional configuration dictionary for the tool handler
        """
        self.config = config or {}
        self._initialize_handler()

    @abstractmethod
    def _initialize_handler(self) -> None:
        """
        Initialize the specific tool handler implementation.

        This method is called during __init__ and should be overridden
        by concrete implementations to set up any handler-specific state.
        """
        pass

    @abstractmethod
    async def process_tool_use(
        self, tool_name: str, tool_use_content: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process a tool use request and return the result.

        This is the main interface method that all tool handlers must implement.
        It should process the tool request and return a structured response.

        Args:
            tool_name: The name of the tool to execute
            tool_use_content: The content/parameters for the tool execution

        Returns:
            Dictionary containing the tool execution result
        """
        pass

    @abstractmethod
    def get_supported_tools(self) -> list[str]:
        """
        Get a list of tools supported by this handler.

        Returns:
            List of tool names that this handler can process
        """
        pass

    @abstractmethod
    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get the schema/specification for a specific tool.

        Args:
            tool_name: The name of the tool

        Returns:
            Dictionary containing the tool schema, or None if tool not found
        """
        pass

    def is_tool_supported(self, tool_name: str) -> bool:
        """
        Check if a tool is supported by this handler.

        Args:
            tool_name: The name of the tool to check

        Returns:
            True if the tool is supported, False otherwise
        """
        return tool_name.lower() in [
            tool.lower() for tool in self.get_supported_tools()
        ]

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        self.config[key] = value

    def get_handler_info(self) -> dict[str, Any]:
        """
        Get information about this tool handler.

        Returns:
            Dictionary containing handler metadata
        """
        return {
            "handler_type": self.__class__.__name__,
            "supported_tools": self.get_supported_tools(),
            "config_keys": list(self.config.keys()),
            "description": self.__class__.__doc__ or "No description available",
        }

    async def validate_tool_request(
        self, tool_name: str, tool_use_content: dict[str, Any]
    ) -> bool:
        """
        Validate a tool request before processing.

        This method can be overridden by implementations to add custom validation.

        Args:
            tool_name: The name of the tool
            tool_use_content: The tool request content

        Returns:
            True if the request is valid, False otherwise
        """
        # Basic validation - check if tool is supported
        if not self.is_tool_supported(tool_name):
            return False

        # Additional validation can be implemented by subclasses
        return True

    async def handle_tool_error(
        self, tool_name: str, error: Exception
    ) -> dict[str, Any]:
        """
        Handle tool execution errors.

        This method can be overridden by implementations to provide custom error handling.

        Args:
            tool_name: The name of the tool that failed
            error: The exception that occurred

        Returns:
            Dictionary containing error information
        """
        return {
            "error": f"Tool execution failed for {tool_name}: {str(error)}",
            "toolName": tool_name,
            "errorType": type(error).__name__,
        }

    def get_bedrock_tool_config(self) -> dict[str, Any]:
        """
        Get tool configuration in Bedrock-compatible format.

        Returns:
            Dictionary containing Bedrock-compatible tool configuration with:
            - tools: List of tool specifications for Bedrock
        """
        tools = []

        for tool_name in self.get_supported_tools():
            schema = self.get_tool_schema(tool_name)
            if schema:
                # Convert our schema format to Bedrock format
                bedrock_tool = {
                    "toolSpec": {
                        "name": schema["name"],
                        "description": schema["description"],
                        "inputSchema": {
                            "json": json.dumps(
                                self._convert_schema_to_bedrock_format(
                                    schema.get("parameters", {})
                                )
                            )
                        },
                    }
                }
                tools.append(bedrock_tool)

        return {"tools": tools}

    def _convert_schema_to_bedrock_format(
        self, parameters_schema: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Convert our parameter schema format to Bedrock JSON schema format.

        Args:
            parameters_schema: Our parameter schema format

        Returns:
            Bedrock-compatible JSON schema
        """
        # If it's already in the right format, return as-is
        if isinstance(parameters_schema, dict) and "type" in parameters_schema:
            return parameters_schema

        # Convert from our simplified format to JSON schema format
        properties = {}
        required = []

        for param_name, param_info in parameters_schema.items():
            if isinstance(param_info, str):
                # Simple format: "param_name": "type description"
                if "(" in param_info and param_info.endswith(")"):
                    # Extract type and description: "string (description)"
                    parts = param_info.split(" (", 1)
                    param_type = parts[0].strip()
                    description = parts[1].rstrip(")")

                    # Check if optional
                    if description.startswith("optional"):
                        description = description.replace("optional, ", "").replace(
                            "optional ", ""
                        )
                    else:
                        required.append(param_name)

                else:
                    # Just type: "string"
                    param_type = param_info.strip()
                    description = f"Parameter {param_name}"
                    required.append(param_name)

                properties[param_name] = {
                    "type": param_type,
                    "description": description,
                }
            elif isinstance(param_info, dict):
                # Already detailed format
                properties[param_name] = param_info
                if param_info.get("required", True):  # Default to required
                    required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}
