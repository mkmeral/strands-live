"""
CLI for Strands Live Speech Agent with automatic context gathering.

This CLI provides options to configure project context gathering capabilities.
"""
import argparse
import asyncio
import warnings
from pathlib import Path
from typing import List, Optional

# Import Strands tools
from strands_tools import calculator, current_time

from .speech_agent import SpeechAgent
from .strands_tool_handler import StrandsToolHandler
from .tools import tasks

# Suppress warnings
warnings.filterwarnings("ignore")

# Debug mode flag - accessible from other modules
DEBUG = False


def get_default_tools():
    """Get the default set of tools for the speech agent.

    Returns:
        List of Strands tool functions to register.
    """
    return [
        current_time,
        calculator,
        tasks,
        # Add more tools here as needed
    ]


def parse_file_patterns(patterns_str: str) -> List[str]:
    """Parse comma-separated file patterns string.
    
    Args:
        patterns_str: Comma-separated file patterns
        
    Returns:
        List of file patterns
    """
    if not patterns_str:
        return []
    return [pattern.strip() for pattern in patterns_str.split(',') if pattern.strip()]


async def async_main(debug: bool = False, 
                    tools: Optional[List] = None,
                    model_id: str = "amazon.nova-sonic-v1:0",
                    region: str = "us-east-1",
                    working_directory: Optional[str] = None,
                    include_directory: bool = False,
                    include_files: bool = False,
                    include_git: bool = False,
                    file_patterns: Optional[List[str]] = None,
                    max_depth: int = 2,
                    max_files: int = 20,
                    custom_prompt: Optional[str] = None,
                    show_context: bool = False):
    """Main function to run the speech agent.
    
    Args:
        debug: Enable debug mode
        tools: List of Strands tools to use
        model_id: Bedrock model ID
        region: AWS region
        working_directory: Directory to gather context from
        include_directory: Include directory structure
        include_files: Include project files
        include_git: Include git context
        file_patterns: Custom file patterns to include
        max_depth: Maximum directory depth
        max_files: Maximum files to list
        custom_prompt: Custom system prompt
        show_context: Show the full raw context
    """
    global DEBUG
    DEBUG = debug

    if tools is None:
        tools = get_default_tools()

    context_enabled = include_directory or include_files or include_git
    
    if context_enabled:
        print(f"🚀 Starting Speech Agent with context gathering and {len(tools)} tools...")
        print("\n📋 Context Configuration:")
        print(f"   Working Directory: {working_directory or 'current directory'}")
        print(f"   Include Directory Structure: {'✅' if include_directory else '❌'}")
        print(f"   Include Project Files: {'✅' if include_files else '❌'}")
        print(f"   Include Git Context: {'✅' if include_git else '❌'}")
        if file_patterns:
            print(f"   Custom File Patterns: {', '.join(file_patterns)}")
        print(f"   Max Directory Depth: {max_depth}")
        print(f"   Max Files Listed: {max_files}")
        print()
    else:
        print(f"🚀 Starting Basic Speech Agent with {len(tools)} tools...")

    tool_handler = StrandsToolHandler(tools=tools)

    speech_agent = SpeechAgent(
        model_id=model_id,
        region=region,
        tool_handler=tool_handler,
        system_prompt=custom_prompt,
        working_directory=working_directory,
        include_directory_structure=include_directory,
        include_project_files=include_files,
        include_git_context=include_git,
        custom_file_patterns=file_patterns,
        max_directory_depth=max_depth,
        max_files_listed=max_files
    )

    # Show context summary if context is enabled
    if context_enabled:
        print("📄 Context Summary:")
        print(speech_agent.get_current_context_summary())
        print()

        # Show raw context if requested
        if show_context or debug:
            print("🔍 Raw Context Preview:")
            print("-" * 50)
            raw_context = speech_agent.get_raw_context()
            if raw_context:
                if len(raw_context) > 1000:
                    print(raw_context[:1000] + "\n... (truncated)")
                else:
                    print(raw_context)
            else:
                print("No additional context generated")
            print("-" * 50)
            print()

    try:
        await speech_agent.initialize()
        
        if context_enabled:
            print("✅ Agent initialized with project context!")
            print("🗣️  The agent now knows about your project structure, files, and git status.")
        else:
            print("✅ Agent initialized!")
        
        await speech_agent.start_conversation()

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        if debug:
            import traceback
            traceback.print_exc()


def main():
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Strands Live Speech Agent with Context Gathering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic agent (no context gathering)
  strands-live
  
  # Agent with directory structure context
  strands-live --include-directory
  
  # Agent with all context features
  strands-live --include-directory --include-files --include-git
  
  # Agent with custom file patterns
  strands-live --include-files --file-patterns "README.md,docs/*.md,package.json"
  
  # Agent for specific directory
  strands-live --working-dir /path/to/project --include-directory --include-files
        """
    )
    
    # Basic configuration
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--model-id",
        default="amazon.nova-sonic-v1:0",
        help="Bedrock model ID (default: amazon.nova-sonic-v1:0)"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    
    # Context configuration
    context_group = parser.add_argument_group("Context Options")
    context_group.add_argument(
        "--working-dir",
        help="Working directory to gather context from (default: current directory)"
    )
    context_group.add_argument(
        "--include-directory",
        action="store_true",
        help="Include directory structure in context"
    )
    context_group.add_argument(
        "--include-files",
        action="store_true", 
        help="Include project files in context (README.md, pyproject.toml, etc.)"
    )
    context_group.add_argument(
        "--include-git",
        action="store_true",
        help="Include git repository context (branch, commits, status)"
    )
    context_group.add_argument(
        "--file-patterns",
        help="Comma-separated list of file patterns to include (e.g., 'README.md,*.py,docs/*.md')"
    )
    context_group.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum directory depth to traverse (default: 2)"
    )
    context_group.add_argument(
        "--max-files",
        type=int,
        default=20,
        help="Maximum number of files to list (default: 20)"
    )
    context_group.add_argument(
        "--custom-prompt",
        help="Custom system prompt (context will be appended)"
    )
    
    # Debug options
    debug_group = parser.add_argument_group("Debug Options")
    debug_group.add_argument(
        "--show-context",
        action="store_true",
        help="Show the full raw context that will be sent to the model"
    )
    
    args = parser.parse_args()

    # Parse file patterns
    file_patterns = parse_file_patterns(args.file_patterns) if args.file_patterns else None

    # Run the agent
    try:
        asyncio.run(async_main(
            debug=args.debug,
            model_id=args.model_id,
            region=args.region,
            working_directory=args.working_dir,
            include_directory=args.include_directory,
            include_files=args.include_files,
            include_git=args.include_git,
            file_patterns=file_patterns,
            max_depth=args.max_depth,
            max_files=args.max_files,
            custom_prompt=args.custom_prompt,
            show_context=args.show_context
        ))
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()


def run_cli():
    """Entry point for backward compatibility."""
    main()


if __name__ == "__main__":
    main()
