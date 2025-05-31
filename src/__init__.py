"""
Nova Sonic Speech Agent Package

A refactored speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming.
"""

from .speech_agent import SpeechAgent
from .tool_handler_base import ToolHandlerBase
from .tool_handler import ToolHandler
from .bedrock_streamer import BedrockStreamManager
from .audio_streamer import AudioStreamer
from .cli import main, run_cli

__version__ = "1.0.0"
__all__ = ["SpeechAgent", "ToolHandlerBase", "ToolHandler", "BedrockStreamManager", "AudioStreamer", "main", "run_cli"]