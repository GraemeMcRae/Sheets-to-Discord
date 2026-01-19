"""
Minimal Config Module for Test Bot

This simple config provides the bot_name attribute that discord_embed_manager expects.
This allows discord_embed_manager.py to be identical to the version used in production bots.
"""

class Config:
    def __init__(self):
        self.bot_name = "Test-Sheets-to-D"

# Create singleton instance
config = Config()
