import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def validate(self) -> None:
        if not self.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Check your .env file in backend/."
            )


settings = Settings()
