from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class CVConfig:
    min_region_area: int = 5000
    edge_threshold: tuple = (50, 150)

@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = os.getenv("OPENAI_API_KEY", "")

@dataclass
class AnalyzerConfig:
    cv_config: CVConfig = None
    llm_config: LLMConfig = None
    
    def __post_init__(self):
        if self.cv_config is None:
            self.cv_config = CVConfig()
        if self.llm_config is None:
            self.llm_config = LLMConfig()