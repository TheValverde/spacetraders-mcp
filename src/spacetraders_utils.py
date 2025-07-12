import os
import json
from pathlib import Path
from typing import Optional, Dict
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env from mcp-mem0 directory (one level up from src)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Constants
TOKENS_FILE = "agent_tokens.json"
RATE_LIMIT_REQUESTS = 2  # requests per second according to docs
RATE_LIMIT_PERIOD = 1  # second

class SpaceTradersClient:
    def __init__(self, base_url: str = "https://api.spacetraders.io/v2"):
        self.base_url = base_url
        self.tokens: Dict[str, str] = self._load_tokens()
        self.last_request_time = datetime.now()
        self.account_token = os.getenv("SPACETRADERS_API_KEY")
        if not self.account_token:
            print("Warning: SPACETRADERS_API_KEY not found in environment variables")
        
    def _load_tokens(self) -> Dict[str, str]:
        """Load stored agent tokens from file."""
        tokens_path = Path(TOKENS_FILE)
        if tokens_path.exists():
            with open(tokens_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tokens(self) -> None:
        """Save agent tokens to file."""
        with open(TOKENS_FILE, 'w') as f:
            json.dump(self.tokens, f, indent=2)
            
    def store_token(self, agent_symbol: str, token: str) -> None:
        """Store a new agent token."""
        self.tokens[agent_symbol] = token
        self._save_tokens()
        
    def get_token(self, agent_symbol: str) -> Optional[str]:
        """Get token for an agent if it exists."""
        return self.tokens.get(agent_symbol)
        
    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        now = datetime.now()
        elapsed = now - self.last_request_time
        if elapsed.total_seconds() < (1.0 / RATE_LIMIT_REQUESTS):
            sleep_time = (1.0 / RATE_LIMIT_REQUESTS) - elapsed.total_seconds()
            import time
            time.sleep(sleep_time)
        self.last_request_time = datetime.now()
        
    def make_request(self, method: str, endpoint: str, agent_symbol: str = None, use_account_token: bool = False, **kwargs) -> requests.Response:
        """Make a rate-limited request to the Space Traders API."""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = kwargs.pop('headers', {})
        headers['Content-Type'] = 'application/json'
        
        # Use account token for registration, agent token for other operations
        if use_account_token:
            if not self.account_token:
                raise ValueError("SPACETRADERS_API_KEY not found in environment variables")
            headers['Authorization'] = f'Bearer {self.account_token}'
        elif agent_symbol and (token := self.get_token(agent_symbol)):
            headers['Authorization'] = f'Bearer {token}'
            
        response = requests.request(method, url, headers=headers, **kwargs)
        return response

# Create a global instance
client = SpaceTradersClient() 