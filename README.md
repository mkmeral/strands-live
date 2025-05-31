# Nova Sonic Speech Agent

A refactored speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming with tool integration.

## Project Structure

```
├── src/
│   ├── __init__.py           # Package initialization
│   ├── bedrock_streamer.py   # BedrockStreamManager class
│   ├── audio_streamer.py     # AudioStreamer class
│   ├── speech_agent.py       # SpeechAgent tool processing
│   └── cli.py                # CLI interface and main logic
├── tests/
│   ├── __init__.py
│   └── test_speech_agent.py  # Unit tests for SpeechAgent
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Components

### BedrockStreamManager (`src/bedrock_streamer.py`)
- Manages bidirectional streaming with AWS Bedrock Nova Sonic
- Handles event serialization and stream lifecycle
- Processes responses and coordinates tool execution

### AudioStreamer (`src/audio_streamer.py`)
- Handles continuous microphone input and audio output
- Uses PyAudio for real-time audio streaming
- Manages barge-in detection and audio playback

### SpeechAgent (`src/speech_agent.py`)
- Processes tool use requests from the conversation
- Implements date/time and order tracking tools
- Provides deterministic fake data for demonstration

### CLI (`src/cli.py`)
- Command-line interface with debug mode support
- Main application orchestration
- Argument parsing and configuration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up AWS credentials (environment variables or AWS CLI):
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Usage

### Run the application:
```bash
python main.py
```

### Enable debug mode:
```bash
python main.py --debug
```

### Run tests:
```bash
pytest tests/
```

## Features

- **Real-time Audio**: Bidirectional streaming with Nova Sonic
- **Tool Integration**: Built-in date/time and order tracking tools
- **Barge-in Support**: Interrupt assistant speech with user input
- **Debug Mode**: Detailed logging for troubleshooting
- **Modular Design**: Clean separation of concerns
- **Async/Await**: Modern Python asynchronous programming

## Available Tools

1. **getDateAndTimeTool**: Returns current date and time in PST
2. **trackOrderTool**: Simulates order tracking with deterministic fake data

## Requirements

- Python 3.8+
- AWS account with Bedrock access
- Microphone and speakers for audio interaction
- PyAudio system dependencies (may require additional setup on some systems)

## Development

The code is structured for easy extension:

- Add new tools by extending `SpeechAgent.process_tool_use()`
- Modify audio settings in `audio_streamer.py` constants
- Extend Bedrock event handling in `BedrockStreamManager`
- Add new CLI options in `cli.py`

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with async support:
```bash
pytest tests/ -v --asyncio-mode=auto
```