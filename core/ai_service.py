import os
from typing import Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion

class AIService:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
             # It's okay if not initialized immediately, but methods will fail
             pass
        else:
             self.client = OpenAI(api_key=self.api_key)

        self.model = model

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def generate_viral_post(self, prompt: str, link: Optional[str] = None, style: str = "viral", platform: str = "default") -> Dict[str, Any]:
        """Generate a viral post using OpenAI."""
        if not self.api_key:
            return {"success": False, "error": "OpenAI API key not set"}

        system_prompt = self._build_system_prompt(style, bool(link))
        user_prompt = self._build_user_prompt(prompt, link, platform)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            return {
                "success": True,
                "content": {
                    "text": content,
                    "link": link
                },
                "metadata": {
                    "model": self.model,
                    "tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_system_prompt(self, style: str, has_link: bool) -> str:
        base_prompt = "You are an expert social media content creator specializing in viral, engaging posts."

        styles = {
            "viral": """Create content that is:
- Attention-grabbing and shareable
- Uses emojis strategically
- Includes power words and emotional triggers
- Has a hook in the first line""",
            "professional": """Create content that is:
- Professional and authoritative
- Informative and valuable
- Suitable for LinkedIn/Business""",
            "casual": """Create content that is:
- Conversational and friendly
- Relatable and authentic"""
        }

        selected_style = styles.get(style, styles["viral"])

        link_guidance = "The content should naturally lead to the provided link." if has_link else "Focus on standalone content."

        return f"{base_prompt}\n\n{selected_style}\n\n{link_guidance}"

    def _build_user_prompt(self, prompt: str, link: Optional[str], platform: str) -> str:
        msg = f"Platform: {platform}\nTopic: {prompt}"
        if link:
            msg += f"\nLink to include: {link}"
        return msg
