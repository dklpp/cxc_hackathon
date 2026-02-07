"""
LLM module using Google Gemini API
"""

import google.generativeai as genai
from typing import List, Dict


class ConversationLLM:
    """Google Gemini LLM client with conversation history"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        system_prompt: str = "You are a helpful assistant."
    ):
        """
        Initialize Gemini LLM client

        Args:
            api_key: Google Gemini API key
            model: Model to use (default: gemini-1.5-flash for speed)
            system_prompt: System prompt defining chatbot personality
        """
        self.api_key = api_key
        self.model_name = model
        self.system_prompt = system_prompt

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt
        )

        # Start chat session
        self.chat = self.model.start_chat(history=[])

        # Track conversation history for management
        self.conversation_history: List[Dict] = []

    async def get_response(self, user_text: str) -> str:
        """
        Get LLM response to user message

        Args:
            user_text: User's message

        Returns:
            Assistant's response text

        Raises:
            Exception: If API request fails
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })

            # Send message and get response
            response = self.chat.send_message(
                user_text,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=150,  # Keep responses concise for voice
                    temperature=0.7,
                )
            )

            assistant_text = response.text.strip()

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_text
            })

            # Manage history size (keep last 20 messages = 10 turns)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return assistant_text

        except Exception as e:
            raise Exception(f"LLM API error: {e}")

    def reset_conversation(self):
        """Reset conversation history and start fresh chat"""
        self.conversation_history = []
        self.chat = self.model.start_chat(history=[])

    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history.copy()

    def get_turn_count(self) -> int:
        """Get number of conversation turns"""
        return len(self.conversation_history) // 2
