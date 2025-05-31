import asyncio
import argparse
import warnings
from .speech_agent import SpeechAgent

# Suppress warnings
warnings.filterwarnings("ignore")

# Debug mode flag - this needs to be accessible from other modules
DEBUG = False


async def main(debug=False):
    """Main function to run the application."""
    global DEBUG
    DEBUG = debug

    # Create speech agent (high-level orchestrator)
    speech_agent = SpeechAgent(model_id='amazon.nova-sonic-v1:0', region='us-east-1')

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
    args = parser.parse_args()
    
    # Set your AWS credentials here or use environment variables
    # os.environ['AWS_ACCESS_KEY_ID'] = "AWS_ACCESS_KEY_ID"
    # os.environ['AWS_SECRET_ACCESS_KEY'] = "AWS_SECRET_ACCESS_KEY"
    # os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

    # Run the main function
    try:
        asyncio.run(main(debug=args.debug))
    except Exception as e:
        print(f"Application error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    run_cli()