import os

def get_spacetraders_api_key():
    """Get the SpaceTraders API key from environment variables."""
    api_key = os.getenv("SPACETRADERS_API_KEY")
    if not api_key:
        raise ValueError("SPACETRADERS_API_KEY not found in environment variables. Please set it in your .env file.")
    return api_key