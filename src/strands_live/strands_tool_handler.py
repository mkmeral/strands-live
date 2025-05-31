"""Strands Tool Handler.

This module provides a tool handler that integrates with the Strands Agents SDK,
acting as a proxy to the Strands ToolRegistry for seamless tool execution.
"""

import asyncio
import json
import logging
from typing import Any

from strands.tools.registry import ToolRegistry

from .tool_handler_base import ToolHandlerBase

logger = logging.getLogger(__name__)


class StrandsToolHandler(ToolHandlerBase):
    """Tool handler that integrates with Strands Agents SDK.

    This handler acts as a proxy to the Strands ToolRegistry, providing seamless
    integration between our speech-based agent system and the Strands ecosystem.

    Key Features:
    - Uses Strands ToolRegistry for tool management
    - Proxies tool execution through AgentTool.invoke()
    - Converts formats between Strands and our system
    - Supports both sync and async execution contexts
    """

    def __init__(
        self, tools: list[Any] | None = None, config: dict[str, Any] | None = None
    ):
        """Initialize the Strands tool handler.

        Args:
            tools: List of Strands tool functions to register.
            config: Optional configuration dictionary.
        """
        self.tools = tools or []
        super().__init__(config)

    def _initialize_handler(self) -> None:
        """Initialize the Strands tool handler implementation."""
        # Initialize Strands ToolRegistry
        self.registry = ToolRegistry()

        # Register provided tools
        if self.tools:
            logger.info(
                f"Initializing Strands tool handler with {len(self.tools)} tools"
            )
            tool_names = self.registry.process_tools(self.tools)
            logger.info(f"Registered Strands tools: {tool_names}")
        else:
            logger.info("Initialized Strands tool handler with no tools")

    def get_supported_tools(self) -> list[str]:
        """Get list of supported tool names.

        Returns:
            List of tool names available in the Strands registry.
        """
        return list(self.registry.registry.keys())

    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Get schema for a specific tool.

        Args:
            tool_name: Name of the tool to get schema for.

        Returns:
            Tool schema dictionary or None if tool not found.
        """
        # Get tool config from Strands registry
        all_configs = self.registry.get_all_tools_config()
        config = all_configs.get(tool_name)

        if not config:
            logger.warning(f"Tool {tool_name} not found in Strands registry")
            return None

        # Convert Strands format to our expected format
        schema = {
            "name": config["name"],
            "description": config["description"],
            "parameters": config["inputSchema"]["json"],  # Already JSON schema format
        }

        logger.debug(f"Retrieved schema for tool {tool_name}")
        return schema

    async def process_tool_use(
        self, tool_name: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a tool use request.

        Args:
            tool_name: Name of the tool to execute.
            parameters: Parameters to pass to the tool.

        Returns:
            Dictionary containing execution result with status and content.
        """
        logger.debug(f"Processing tool use: {tool_name} with parameters: {parameters}")
        print(f"\nTool Name: {tool_name}\nTool Params: {parameters}\n\n")
        # Get tool from registry
        tool = self.registry.registry.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found in Strands registry"
            logger.error(error_msg)
            return {"status": "error", "content": [{"text": error_msg}]}

        try:
            # Create proper ToolUse object for Strands invoke method
            tool_use = {
                "toolUseId": f"strands_tool_{tool_name}",
                "name": tool_name,
                "input": json.loads(parameters["content"]),
            }

            # Execute tool in thread pool since tool.invoke() is synchronous
            # but our method is async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, tool.invoke, tool_use)

            # Convert Strands format to our format
            # Strands returns: {"toolUseId": "...", "status": "...", "content": [...]}
            # We need: {"status": "...", "content": [...]}
            converted_result = {
                "status": result["status"],
                "content": result["content"],
            }

            logger.debug(f"Tool {tool_name} executed successfully")
            return converted_result

        except Exception as e:
            error_msg = f"Error executing Strands tool '{tool_name}': {str(e)}"
            logger.exception(error_msg)
            return {"status": "error", "content": [{"text": error_msg}]}

    def is_tool_supported(self, tool_name: str) -> bool:
        """Check if a tool is supported.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if tool is supported, False otherwise.
        """
        return tool_name in self.registry.registry

    def get_bedrock_tool_config(self) -> dict[str, Any]:
        """Get Bedrock-compatible tool configuration.

        Returns:
            Dictionary containing tools configuration for Bedrock.
        """
        tools = []

        for tool_name in self.get_supported_tools():
            schema = self.get_tool_schema(tool_name)
            if schema:
                # Convert to Bedrock format
                bedrock_tool = {
                    "toolSpec": {
                        "name": schema["name"],
                        "description": schema["description"],
                        "inputSchema": {
                            "json": json.dumps(
                                self._convert_schema_to_bedrock_format(
                                    schema["parameters"]
                                )
                            )
                        },
                    }
                }
                tools.append(bedrock_tool)

        return {"tools": tools}

    def add_strands_tool(self, tool_function) -> str:
        """Add a new Strands tool to the handler.

        Args:
            tool_function: A function decorated with @tool from Strands SDK.

        Returns:
            Name of the added tool.

        Raises:
            ValueError: If the tool function is invalid.
        """
        if not hasattr(tool_function, "TOOL_SPEC"):
            raise ValueError(
                "Tool function must be decorated with @tool from Strands SDK"
            )

        tool_names = self.registry.process_tools([tool_function])
        if tool_names:
            tool_name = tool_names[0]
            logger.info(f"Added Strands tool: {tool_name}")
            return tool_name
        else:
            raise ValueError("Failed to register Strands tool")

    def add_strands_tools(self, tool_functions: list[Any]) -> list[str]:
        """Add multiple Strands tools to the handler.

        Args:
            tool_functions: List of functions decorated with @tool from Strands SDK.

        Returns:
            List of names of the added tools.
        """
        tool_names = self.registry.process_tools(tool_functions)
        logger.info(f"Added Strands tools: {tool_names}")
        return tool_names

    def get_handler_info(self) -> dict[str, Any]:
        """Get handler information including registered tools.

        Returns:
            Dictionary containing handler information.
        """
        return {
            "handler_type": "StrandsToolHandler",
            "supported_tools": self.get_supported_tools(),
            "total_tools": len(self.registry.registry),
            "strands_registry_info": {
                "registry_tools": len(self.registry.registry),
                "dynamic_tools": len(self.registry.dynamic_tools),
            },
            "config": self.config,
        }
