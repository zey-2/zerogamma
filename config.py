"""
Configuration module for zerogamma analysis pipeline.

Loads API keys and credentials from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_config():
    """
    Retrieve all required configuration from environment variables.
    
    Returns:
        dict: Configuration dictionary with API keys and credentials.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    required_vars = [
        "FMP_API_KEY",
        "OPENROUTER_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    
    config = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var] = value
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please set them in your .env file or export them as environment variables."
        )
    
    return config
