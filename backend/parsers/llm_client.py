from groq import Groq


class GroqLLMClient:
    def __init__(self, api_key: str):
        self._client = Groq(api_key=api_key)

    def structure(self, prompt: str, model: str) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content
