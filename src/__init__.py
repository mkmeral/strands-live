"""
Nova Sonic Speech Agent Package

A refactored speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming.
"""

from .bedrock_streamer import BedrockStreamManager
from .audio_streamer import AudioStreamer
from .speech_agent import SpeechAgent
from .cli import main, run_cli

__version__ = "1.0.0"
__all__ = ["BedrockStreamManager", "AudioStreamer", "SpeechAgent", "main", "run_cli"]