"""
Strands Live Package

A live speech agent using Amazon Nova Sonic for real-time bidirectional
audio streaming with Strands Agents SDK integration.
"""

from .audio_streamer import AudioStreamer
from .bedrock_streamer import BedrockStreamManager
from .cli import main, run_cli
from .speech_agent import SpeechAgent
from .strands_tool_handler import StrandsToolHandler
from .tool_handler import ToolHandler
from .tool_handler_base import ToolHandlerBase

__version__ = "0.1.0"
__all__ = [
    "SpeechAgent",
    "ToolHandlerBase",
    "ToolHandler",
    "StrandsToolHandler",
    "BedrockStreamManager",
    "AudioStreamer",
    "main",
    "run_cli",
]
