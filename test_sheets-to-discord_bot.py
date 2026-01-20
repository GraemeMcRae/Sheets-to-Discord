#!/usr/bin/env python3
"""
Test-Sheets-to-Discord Bot

Minimal Discord bot to test the Sheets-to-Discord embed renderer.
Reads JSON from Google Sheets cell A1 and displays as interactive embed tiles.

Usage:
    python test_sheets-to-discord_bot.py

Requirements:
    - .env file with configuration (see .env.example)
    - google_credentials.json file
    - discord_embed_manager.py module
"""

import discord
from discord import app_commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import logging
from dotenv import load_dotenv
from discord_embed_manager import display_embeds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Configuration from .env
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME = os.getenv('BOT_NAME', 'Test-Sheets-to-D')
GOOGLE_SPREADSHEET_NAME = os.getenv('GOOGLE_SPREADSHEET_NAME')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')

# Get logger
logger = logging.getLogger(BOT_NAME)


def add_test_button(view, hidden_data, user_id):
    """
    Example function that adds a custom button to the view.
    
    This demonstrates how to use the additional_buttons feature.
    The button only appears if hidden_data is not empty.
    
    Args:
        view: The EmbedNavigationView to add buttons to
        hidden_data: Content from the Hidden column for this row
        user_id: The Discord user ID who can interact with the view
    """
    # Only add button if there's hidden data
    if not hidden_data or not hidden_data.strip():
        return
    
    # Create the button
    button = discord.ui.Button(
        label="🔍 Show Hidden",
        style=discord.ButtonStyle.secondary
    )
    
    # Define what happens when button is clicked
    async def button_callback(interaction: discord.Interaction):
        # Verify it's the right user
        if interaction.user.id != user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        # Display the hidden data
        await interaction.response.send_message(
            f"**Hidden Data:**\n```\n{hidden_data}\n```",
            ephemeral=True
        )
    
    # Attach the callback to the button
    button.callback = button_callback
    
    # Add the button to the view
    view.add_item(button)


# Validate configuration
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")
if not GOOGLE_SPREADSHEET_NAME:
    raise ValueError("GOOGLE_SPREADSHEET_NAME not found in .env file")

# Connect to Google Sheets
def connect_to_sheets():
    """Connect to Google Sheets using service account credentials"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_FILE,
            scope
        )
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SPREADSHEET_NAME)
        logger.info(f"Connected to Google Spreadsheet: {GOOGLE_SPREADSHEET_NAME}")
        return sheet
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
        raise
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(f"Spreadsheet not found: {GOOGLE_SPREADSHEET_NAME}")
        logger.error("Make sure the sheet is shared with the service account email")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {e}")
        raise

# Global spreadsheet connection
spreadsheet = connect_to_sheets()

# Setup Discord bot
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


async def fetch_sheet_data():
    """
    Fetch JSON data from Sheet1!A1
    
    Returns:
        str: JSON string or None if error
    """
    try:
        worksheet = spreadsheet.worksheet("Sheet1")
        json_string = worksheet.acell('A1').value
        
        if not json_string:
            logger.error("Sheet1!A1 is empty")
            return None
        
        logger.info(f"Read {len(json_string)} characters from Sheet1!A1")
        return json_string
        
    except gspread.exceptions.WorksheetNotFound:
        logger.error("Worksheet 'Sheet1' not found")
        return None
    except Exception as e:
        logger.error(f"Error reading Sheet1!A1: {e}")
        return None


@tree.command(name="test", description="Test Sheets-to-Discord embed renderer")
async def test_command(interaction: discord.Interaction):
    """Display data from Sheet1!A1 as interactive embed tiles"""
    logger.info(f"/test command used by {interaction.user.name}")
    
    # Defer response (required before calling display_embeds)
    await interaction.response.defer(ephemeral=True)
    
    # Display using embed manager with example custom button
    await display_embeds(
        interaction,
        json_string=None,  # Will trigger fetch_sheet_data
        refresh_callback=fetch_sheet_data,
        additional_buttons=add_test_button  # Adds "Show Hidden" button if Hidden data exists
    )


@bot.event
async def on_ready():
    """Called when bot is ready"""
    logger.info(f'{BOT_NAME} connected as {bot.user.name} (ID: {bot.user.id})')
    
    # Sync commands
    try:
        synced = await tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')


# Run the bot
if __name__ == "__main__":
    logger.info(f"Starting {BOT_NAME}...")
    bot.run(DISCORD_TOKEN)
