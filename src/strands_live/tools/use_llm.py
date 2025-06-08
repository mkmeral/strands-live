"""
AskAgent tool for Strands Agent delegation and specialized assistance.

This module provides functionality to communicate with powerful specialized agents
that have access to a comprehensive toolkit. When you don't know how to answer
a user's request or need specialized assistance, use this tool to delegate to
expert agents with different specializations.

Each agent specialty is configured with optimized system prompts and has access
to all available tools for comprehensive problem-solving capabilities.

Usage with Strands Agent:
```python
from strands import Agent
from strands_tools import use_llm

agent = Agent(tools=[use_llm])

# Ask a coding specialist
result = agent.tool.use_llm(
    prompt="How do I implement a binary search tree in Python?",
    agent_specialty="coding"
)

# Ask a research specialist
result = agent.tool.use_llm(
    prompt="What are the latest developments in quantum computing?",
    agent_specialty="research"
)

# The response is available in the returned object
print(result["content"][0]["text"])  # Prints the response text
```

See the use_llm function docstring for more details on available specialties.
"""

import logging
from typing import Any

from strands import Agent
from strands.telemetry.metrics import metrics_to_string
from strands.types.tools import ToolResult, ToolUse

# Strands tools
from strands_tools import (
    agent_graph,
    calculator,
    cron,
    current_time,
    editor,
    environment,
    file_read,
    file_write,
    generate_image,
    http_request,
    image_reader,
    journal,
    load_tool,
    memory,
    nova_reels,
    python_repl,
    retrieve,
    shell,
    slack,
    speak,
    stop,
    swarm,
    think,
    use_aws,
    workflow,
)

logger = logging.getLogger(__name__)
PROMPT_APPENDED_TEXT = "Make sure to return short and concise answers. It should respond to user question, nothing else!"
# Agent specialty system prompts
AGENT_SPECIALTIES = {
    "coding": "You are an expert software developer and architect. You excel at writing clean, efficient code, debugging issues, and explaining complex programming concepts. You have deep knowledge of multiple programming languages, frameworks, and best practices.",
    "research": "You are a skilled researcher and analyst. You excel at finding, synthesizing, and presenting information from multiple sources. You provide comprehensive, well-sourced answers and can analyze complex topics from multiple perspectives.",
    "writing": "You are a professional writer and editor. You excel at creating clear, engaging content, improving existing text, and adapting writing style to different audiences and purposes. You understand grammar, style, and effective communication principles.",
    "troubleshooting": "You are a systematic problem-solver and diagnostician. You excel at identifying root causes, breaking down complex problems into manageable steps, and providing actionable solutions. You approach issues methodically and thoroughly.",
    "analysis": "You are a data analyst and critical thinker. You excel at examining information, identifying patterns, drawing insights, and presenting findings clearly. You can work with quantitative and qualitative data to provide meaningful conclusions.",
    "general": "You are a knowledgeable and helpful assistant. You provide accurate, comprehensive answers across a wide range of topics. You're resourceful, think step-by-step, and use available tools effectively to solve problems.",
}

TOOL_SPEC = {
    "name": "use_llm",
    "description": "Communicate with powerful specialized AI agents that have access to comprehensive toolkits. If you don't know how to answer a user's request or need expert assistance, ALWAYS use this tool to delegate to specialized agents with different expertise areas. These agents can access internet, user's files and user's AWS account. Use these agents to access this information.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request or question to send to the specialized agent",
                },
                "agent_specialty": {
                    "type": "string",
                    "description": "The type of specialized agent to use",
                    "enum": [
                        "coding",
                        "research",
                        "writing",
                        "troubleshooting",
                        "analysis",
                        "general",
                    ],
                    "default": "general",
                },
            },
            "required": ["prompt"],
        }
    },
}


def use_llm(tool: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Communicate with specialized agents that have comprehensive tool access.

    This function creates a specialized Strands Agent with optimized system prompts
    and full tool access. Use this whenever you need expert assistance or don't know
    how to handle a user's request. Each specialty provides focused expertise while
    maintaining access to all available tools for comprehensive problem-solving.

    How It Works:
    ------------
    1. Selects appropriate system prompt based on agent specialty
    2. Creates a new Agent instance with specialized configuration
    3. Processes the request in an isolated context with full tool access
    4. Returns detailed response with performance metrics
    5. Agent instance is cleaned up automatically after use

    Available Specialties:
    --------------------
    - coding: Expert software development, debugging, and architecture
    - research: Information gathering, analysis, and synthesis
    - writing: Content creation, editing, and communication
    - troubleshooting: Systematic problem diagnosis and resolution
    - analysis: Data examination, pattern recognition, and insights
    - general: Broad knowledge with effective tool utilization (default)

    When to Use:
    -----------
    - You don't know how to answer a user's request
    - You need specialized expertise in a particular domain
    - Complex problems requiring systematic tool usage
    - Tasks that benefit from focused, expert-level assistance

    Args:
        tool (ToolUse): Tool use object containing:
            - prompt (str): The request or question for the specialized agent
            - agent_specialty (str, optional): Agent type - defaults to "general"
        **kwargs (Any): Additional keyword arguments

    Returns:
        ToolResult: Dictionary with status and response content:
        {
            "toolUseId": "unique-tool-use-id",
            "status": "success",
            "content": [
                {"text": "Response: [Agent's detailed response]"},
                {"text": "Metrics: [Performance and usage metrics]"}
            ]
        }

    Notes:
        - All agents have access to the complete toolkit for maximum capability
        - Responses include both the answer and performance metrics
        - Agent instances are temporary and isolated from parent context
        - Use this tool liberally when uncertain - it's designed for delegation
    """
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    prompt = tool_input["prompt"]
    agent_specialty = tool_input.get("agent_specialty", "general")

    # Get system prompt for the specified specialty
    system_prompt = (
        AGENT_SPECIALTIES.get(agent_specialty, AGENT_SPECIALTIES["general"])
        + PROMPT_APPENDED_TEXT
    )

    tools = [
        agent_graph,
        calculator,
        cron,
        current_time,
        editor,
        environment,
        file_read,
        file_write,
        generate_image,
        http_request,
        image_reader,
        journal,
        load_tool,
        memory,
        nova_reels,
        python_repl,
        retrieve,
        shell,
        slack,
        speak,
        stop,
        swarm,
        think,
        use_aws,
        use_llm,
        workflow,
    ]
    trace_attributes = {}

    extra_kwargs = {}
    parent_agent = kwargs.get("agent")
    if parent_agent:
        trace_attributes = parent_agent.trace_attributes
        extra_kwargs["callback_handler"] = parent_agent.callback_handler
    if "callback_handler" in kwargs:
        extra_kwargs["callback_handler"] = kwargs["callback_handler"]

    # Display input prompt and selected specialty
    logger.debug(f"\n--- Input Prompt ---\n{prompt}\n")
    logger.debug(f"Agent Specialty: {agent_specialty}")

    # Visual indicator for new specialized agent
    logger.debug(f"🔄 Creating new {agent_specialty} specialist agent...")

    # Initialize the new Agent with specialized system prompt
    agent = Agent(
        messages=[],
        tools=tools,
        system_prompt=system_prompt,
        trace_attributes=trace_attributes,
        **extra_kwargs,
    )
    # Run the agent with the provided prompt
    result = agent(prompt)

    # Extract response
    assistant_response = str(result)

    # Display assistant response
    logger.debug(f"\n--- Assistant Response ---\n{assistant_response.strip()}\n")

    # Print metrics if available
    metrics_text = ""
    if result.metrics:
        metrics = result.metrics
        metrics_text = metrics_to_string(metrics)
        logger.debug(metrics_text)

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [
            {"text": f"Response: {assistant_response}"},
            {"text": f"Metrics: {metrics_text}"},
        ],
    }
