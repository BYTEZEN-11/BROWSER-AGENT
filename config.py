"""
Configuration Management
Load settings from environment variables or defaults
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Flask Configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Agent Configuration
    DEFAULT_MAX_STEPS = int(os.getenv('DEFAULT_MAX_STEPS', 50))
    MIN_MAX_STEPS = int(os.getenv('MIN_MAX_STEPS', 10))
    MAX_MAX_STEPS = int(os.getenv('MAX_MAX_STEPS', 150))
    
    # Browser Configuration
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'True').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', 30000))
    
    # OpenAI Configuration
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 4096))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'browser_agent.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Paths
    BASE_DIR = Path(__file__).parent
    MARK_PAGE_SCRIPT = BASE_DIR / 'mark_page.js'
    
    # Application Info
    APP_NAME = os.getenv('APP_NAME', 'LangGraph Browser Agent')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    APP_DESCRIPTION = os.getenv('APP_DESCRIPTION', 'AI-Powered Web Automation')
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.MARK_PAGE_SCRIPT.exists():
            raise FileNotFoundError(f"mark_page.js not found at {cls.MARK_PAGE_SCRIPT}")
        return True

# Validate configuration on import
Config.validate()

