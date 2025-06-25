# Strands Live Speech Agent

A powerful speech-to-speech AI agent built with Amazon Bedrock Nova Sonic and Strands Agents SDK, featuring automatic project context gathering for enhanced conversational AI experiences.

## Features

- **🎙️ Real-time Speech Processing**: Continuous speech-to-speech conversation with Amazon Nova Sonic
- **🔧 Strands Agents Integration**: Access to powerful tools like file operations, calculations, and web requests
- **📁 Automatic Context Gathering**: Intelligent analysis of your project structure, files, and git repository
- **⚙️ Flexible Configuration**: Customize context gathering, model parameters, and tool selection
- **🧪 Comprehensive Testing**: Full test coverage with 149+ passing tests

## Installation

```bash
# Install the package
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage (No Context)
```bash
# Simple speech agent
strands-live

# With debug mode
strands-live --debug
```

### Context-Aware Usage
```bash
# Include directory structure
strands-live --include-directory

# Include project files (README, pyproject.toml, etc.)
strands-live --include-files

# Include git repository context
strands-live --include-git

# All context features enabled
strands-live --include-directory --include-files --include-git
```

### Advanced Configuration
```bash
# Custom file patterns
strands-live --include-files --file-patterns "README.md,docs/*.md,package.json"

# Different working directory
strands-live --working-dir /path/to/project --include-directory --include-files

# Custom model and region
strands-live --model-id amazon.nova-sonic-v1:0 --region us-west-2

# Show full context preview
strands-live --include-directory --include-files --include-git --show-context
```

## Context Gathering Features

The speech agent can automatically gather context about your project to provide more relevant assistance:

### 📁 Directory Structure Context
- Automatically maps your project's directory tree
- Configurable depth limits (default: 2 levels)
- File count limits to prevent overwhelming the context
- Smart filtering of common directories (.git, .venv, __pycache__)

### 📄 Project Files Context
- Reads and includes key project files automatically:
  - `README.md` - Project documentation
  - `pyproject.toml` - Python project configuration
  - `package.json` - Node.js project configuration
  - `CHANGELOG.md` - Release notes
  - `AmazonQ.md` - AI assistant documentation
- Custom file patterns supported
- Safe file reading with encoding detection

### 🌿 Git Repository Context
- Current branch information
- Recent commit history (last 5 commits)
- Working directory status (modified, added, deleted files)
- Clean/dirty repository state

## Configuration Options

### Context Options
- `--working-dir`: Set working directory for context gathering
- `--include-directory`: Include directory structure in context
- `--include-files`: Include project files in context
- `--include-git`: Include git repository context
- `--file-patterns`: Custom comma-separated file patterns
- `--max-depth`: Maximum directory depth (default: 2)
- `--max-files`: Maximum number of files to list (default: 20)

### Model Options
- `--model-id`: Bedrock model ID (default: amazon.nova-sonic-v1:0)
- `--region`: AWS region (default: us-east-1)
- `--custom-prompt`: Custom system prompt

### Debug Options
- `--debug`: Enable debug mode
- `--show-context`: Display full context preview

## Programmatic Usage

### Basic Agent
```python
from strands_live.speech_agent import SpeechAgent
from strands_live.strands_tool_handler import StrandsToolHandler

# Create agent without context
agent = SpeechAgent(
    model_id="amazon.nova-sonic-v1:0",
    region="us-east-1",
    tool_handler=StrandsToolHandler()
)

await agent.initialize()
await agent.start_conversation()
```

### Context-Aware Agent
```python
from strands_live.speech_agent import SpeechAgent
from strands_live.strands_tool_handler import StrandsToolHandler

# Create agent with context gathering
agent = SpeechAgent(
    model_id="amazon.nova-sonic-v1:0",
    region="us-east-1",
    tool_handler=StrandsToolHandler(),
    # Context configuration
    include_directory_structure=True,
    include_project_files=True,
    include_git_context=True,
    working_directory=".",
    max_directory_depth=2,
    max_files_listed=20
)

# Inspect context
print(agent.get_current_context_summary())
print(agent.get_raw_context())

await agent.initialize()
await agent.start_conversation()
```

### Dynamic Context Management
```python
# Refresh context during conversation
agent.refresh_context()

# Get context information
summary = agent.get_current_context_summary()
raw_context = agent.get_raw_context()
```

## Architecture

The speech agent consists of several key components:

- **SpeechAgent**: Main orchestrator with context building capabilities
- **ContextBuilder**: Intelligent project analysis and context generation
- **BedrockStreamManager**: Handles real-time streaming with Amazon Bedrock
- **AudioStreamer**: Manages audio input/output with PyAudio
- **StrandsToolHandler**: Provides access to Strands Agents SDK tools

## Available Tools

The agent comes with built-in tools powered by Strands Agents SDK:

- **Calculator**: Advanced mathematical computations
- **Current Time**: Time and date queries
- **Tasks**: Task management and tracking
- **File Operations**: Read, write, and manage files
- **Web Requests**: HTTP/HTTPS API calls
- **AWS Services**: Full AWS SDK access

## Environment Setup

### Required Environment Variables
```bash
# AWS credentials (for Bedrock access)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Optional: Default timezone
export DEFAULT_TIMEZONE="UTC"
```

### Audio Requirements
- Microphone access for speech input
- Audio output capability
- PyAudio dependencies (automatically installed)

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/strands_live

# Run specific test categories
pytest tests/test_speech_agent.py -v
pytest tests/integration/ -v
```

### Project Structure
```
src/strands_live/
├── speech_agent.py          # Main speech agent with context
├── context_builder.py       # Project context analysis
├── cli.py                   # Command-line interface
├── bedrock_streamer.py      # Bedrock streaming manager
├── audio_streamer.py        # Audio input/output
├── strands_tool_handler.py  # Strands tools integration
└── tools/                   # Built-in tools
    └── tasks.py
```

## Examples

### Development Assistant
```bash
# Perfect for development workflows
strands-live --include-directory --include-files --include-git --working-dir ~/my-project
```

### Documentation Helper
```bash
# Focus on documentation files
strands-live --include-files --file-patterns "README.md,docs/*.md,*.rst"
```

### Code Review Assistant
```bash
# Include git context for code reviews
strands-live --include-git --include-files --file-patterns "*.py,*.js,*.md"
```

## Troubleshooting

### Common Issues

1. **Audio Issues**: Ensure microphone permissions and PyAudio installation
2. **AWS Credentials**: Verify AWS credentials and region configuration
3. **Context Too Large**: Reduce `--max-depth` or `--max-files` values
4. **Git Context Missing**: Ensure you're in a git repository

### Debug Mode
```bash
# Enable debug output
strands-live --debug --show-context
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0.

## Support

For issues and questions:
- Check the troubleshooting section
- Review test cases for usage examples
- Open an issue on GitHub