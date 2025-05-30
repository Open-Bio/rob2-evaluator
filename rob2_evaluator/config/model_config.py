from dotenv import load_dotenv, find_dotenv
from rob2_evaluator.llm.models import ModelProvider
import os


class ModelConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 加载环境变量
        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        self.provider_map = {
            "ANTHROPIC": ModelProvider.ANTHROPIC,
            "DEEPSEEK": ModelProvider.DEEPSEEK,
            "GEMINI": ModelProvider.GEMINI,
            "GROQ": ModelProvider.GROQ,
            "OPENAI": ModelProvider.OPENAI,
            "OLLAMA": ModelProvider.OLLAMA,
        }

    def get_model_name(self) -> str:
        return os.getenv("MODEL_NAME", "gemma3:27b")

    def get_model_provider(self) -> ModelProvider:
        env_provider = os.getenv("MODEL_PROVIDER", "OLLAMA").upper()
        return self.provider_map.get(env_provider, ModelProvider.OLLAMA)
