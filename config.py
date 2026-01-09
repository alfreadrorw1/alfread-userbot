import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Configuration class for the bot"""
    # Telegram API
    api_id: int = int(os.getenv("API_ID", 0))
    api_hash: str = os.getenv("API_HASH", "")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    
    # MongoDB
    mongo_uri: str = os.getenv("MONGO_URI", "")
    db_name: str = os.getenv("DB_NAME", "alfread_bot")
    
    # Bot Settings
    owner_id: int = int(os.getenv("OWNER_ID", 0))
    log_chat_id: Optional[int] = os.getenv("LOG_CHAT_ID")
    
    # Session Settings
    session_name: str = "alfread_session"
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required = [
            (self.api_id, "API_ID"),
            (self.api_hash, "API_HASH"),
            (self.bot_token, "BOT_TOKEN"),
            (self.mongo_uri, "MONGO_URI"),
            (self.owner_id, "OWNER_ID")
        ]
        
        for value, name in required:
            if not value:
                raise ValueError(f"Missing required environment variable: {name}")
        
        return True

# Global config instance
config = Config()

# Validate on import
try:
    config.validate()
    print("✅ Configuration loaded successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")