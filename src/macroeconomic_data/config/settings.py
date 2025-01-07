from pathlib import Path
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict

# Project paths
ROOT_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

# Default configurations - Match EXACTLY with your AWS Secrets Manager names
DEFAULT_FRED_SECRET = "FED_API_KEY"
DEFAULT_GROQ_SECRET = "GROQ_API_KEY"
DEFAULT_AWS_REGION = "eu-central-1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

# Default series mappings
DEFAULT_FRED_SERIES_MAPPINGS = {
    "gdp": "GDP",
    "real gdp": "GDPC1",
    "gdp per capita": "A939RX0Q048SBEA",
    "gdp growth": "A191RL1Q225SBEA",
    "unemployment rate": "UNRATE",
    "inflation": "CPIAUCSL",
    "core inflation": "CPILFESL",
    "interest rate": "FEDFUNDS",
    "federal funds rate": "FEDFUNDS",
    "industrial production": "INDPRO",
    "retail sales": "RSXFS",
    "housing starts": "HOUST",
    "personal income": "PI",
    "real personal income": "RPI",
    "consumer sentiment": "UMCSENT",
}

class Settings(BaseSettings):
    FED_SECRET_NAME: str = DEFAULT_FRED_SECRET
    GROQ_SECRET_NAME: str = DEFAULT_GROQ_SECRET
    AWS_REGION: str = DEFAULT_AWS_REGION
    GROQ_MODEL: str = DEFAULT_GROQ_MODEL
    FRED_SERIES_MAPPINGS: Dict[str, str] = DEFAULT_FRED_SERIES_MAPPINGS
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()
