import argparse
import asyncio
import warnings

# Import Strands tools
from strands_tools import calculator, current_time

from .tools import use_llm, tasks

from .speech_agent import SpeechAgent
from .strands_tool_handler import StrandsToolHandler

# Suppress warnings
warnings.filterwarnings("ignore")

# Debug mode flag - this needs to be accessible from other modules
DEBUG = False


def get_default_tools():
    """Get the default set of tools for the speech agent.

    Returns:
        List of Strands tool functions to register.
    """
    return [
        current_time,
        calculator,
        use_llm,  # AskAgent - specialized agent delegation
        # tasks,
        # Add more tools here as needed
    ]


def main():
    """Entry point for the CLI application."""
    run_cli()


async def async_main(debug=False, tools=None):
    """Main function to run the application.

    Args:
        debug: Enable debug mode
        tools: List of Strands tools to use (defaults to get_default_tools())
    """
    global DEBUG
    DEBUG = debug

    # Use provided tools or default set
    if tools is None:
        tools = get_default_tools()

    # Create Strands tool handler with configured tools
    print(f"🚀 Using Strands Agents SDK with {len(tools)} tools... {tools}")
    tool_handler = StrandsToolHandler(tools=tools)

    # Create speech agent with Strands tool handler
    speech_agent = SpeechAgent(
        model_id="amazon.nova-sonic-v1:0", region="us-east-1", tool_handler=tool_handler
    )

    try:
        # Initialize the speech agent
        await speech_agent.initialize()

        # Start conversation
        await speech_agent.start_conversation()

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        if debug:
            import traceback

            traceback.print_exc()


def run_cli():
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="Nova Sonic Python Streaming")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Set your AWS credentials here or use environment variables
    # os.environ['AWS_ACCESS_KEY_ID'] = "AWS_ACCESS_KEY_ID"
    # os.environ['AWS_SECRET_ACCESS_KEY'] = "AWS_SECRET_ACCESS_KEY"
    # os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

    # Run the main function
    try:
        asyncio.run(async_main(debug=args.debug))
    except Exception as e:
        print(f"Application error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    run_cli()
