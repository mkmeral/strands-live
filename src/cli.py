import asyncio
import argparse
import warnings
from .speech_agent import SpeechAgent
from .strands_tool_handler import StrandsToolHandler
from .tool_handler import ToolHandler

# Suppress warnings
warnings.filterwarnings("ignore")

# Debug mode flag - this needs to be accessible from other modules
DEBUG = False


async def main(debug=False, use_strands=True):
    """Main function to run the application.
    
    Args:
        debug: Enable debug mode
        use_strands: Use StrandsToolHandler (default) or original ToolHandler
    """
    global DEBUG
    DEBUG = debug

    # Create tool handler based on preference
    if use_strands:
        print("🚀 Using Strands Agents SDK tools...")
        tool_handler = StrandsToolHandler()
    else:
        print("🔧 Using original tool handler...")
        tool_handler = ToolHandler()
    
    # Create speech agent with selected tool handler
    speech_agent = SpeechAgent(
        model_id='amazon.nova-sonic-v1:0', 
        region='us-east-1',
        tool_handler=tool_handler
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
    parser = argparse.ArgumentParser(description='Nova Sonic Python Streaming')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--original-tools', action='store_true', 
                       help='Use original tool handler instead of Strands tools')
    args = parser.parse_args()
    
    # Set your AWS credentials here or use environment variables
    # os.environ['AWS_ACCESS_KEY_ID'] = "AWS_ACCESS_KEY_ID"
    # os.environ['AWS_SECRET_ACCESS_KEY'] = "AWS_SECRET_ACCESS_KEY"
    # os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

    # Run the main function
    try:
        asyncio.run(main(debug=args.debug, use_strands=not args.original_tools))
    except Exception as e:
        print(f"Application error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    run_cli()