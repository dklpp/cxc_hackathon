"""
Configuration module for voice chatbot
"""

from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for voice chatbot"""
    elevenlabs_api_key: str
    gemini_api_key: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    sample_rate: int = 16000
    system_prompt: str = (
        "You are a bank collector. Inform user about their debt of $100,000 and "
        "ask kindly to pay the money back. Be professional but persistent. "
        "Keep responses concise and conversational for voice interaction."
    )

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        load_dotenv()

        api_key = os.getenv('ELEVEN_LABS_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("ELEVEN_LABS_API_KEY not found in .env file")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")

        return cls(
            elevenlabs_api_key=api_key,
            gemini_api_key=gemini_key,
            voice_id=os.getenv('VOICE_ID', "21m00Tcm4TlvDq8ikWAM"),
        )
