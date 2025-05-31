# Strands Live 🎤

A live speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming with Strands Agents SDK integration.

## Features

- **Real-time Audio Streaming**: Bidirectional audio communication with Amazon Nova Sonic
- **Tool Integration**: Powered by Strands Agents SDK with 50+ built-in tools
- **Extensible**: Easy to add custom tools and capabilities
- **Voice Activity Detection**: Smart audio processing with barge-in support
- **Cross-platform**: Works on macOS, Linux, and Windows

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/murmeral/strands-live.git
cd strands-live
make install

# Or install as CLI
make install-cli
```

### Usage

```bash
# Run directly
python strands_live_main.py

# Or use CLI after install-cli
strands-live --help
```

### Configuration

Set up your AWS credentials and configure the region:

```bash
export AWS_REGION=us-west-2  # or your preferred region
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

## Development

```bash
# Install development dependencies
make install

# Run tests
make test

# Format code
make format

# Build package
make build

# Clean up
make clean
```

## Architecture

The system consists of several key components:

- **SpeechAgent**: Main orchestrator for speech processing
- **BedrockStreamManager**: Handles Nova Sonic streaming
- **AudioStreamer**: Manages audio input/output
- **StrandsToolHandler**: Integrates with Strands SDK tools
- **CLI**: Command-line interface

## Requirements

- Python 3.10+
- PyAudio for audio processing
- AWS credentials with Bedrock access
- Microphone and speakers/headphones

## License

Apache License 2.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting
5. Submit a pull request