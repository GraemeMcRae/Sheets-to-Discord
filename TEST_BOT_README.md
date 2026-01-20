# Test Bot for Sheets-to-Discord

This is a minimal Discord bot to test the Sheets-to-Discord embed renderer.

## Purpose

This bare-bones bot demonstrates how to integrate the `discord_embed_manager.py` module into a Discord bot. Use this to:
- Verify the Sheets-to-Discord code works
- Learn integration patterns
- Test your Google Sheets setup
- Debug issues

## Quick Start

### 1. Prerequisites

- **Python 3.10+** (Python 3.9 is end-of-life and will show warnings)
- A Discord bot created at https://discord.com/developers/applications
- A Google Sheets spreadsheet
- Google Cloud service account credentials

**Note:** If you see Python 3.9 end-of-life warnings, consider upgrading to Python 3.10 or newer. The bot will still work but Google's libraries may not receive updates.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
DISCORD_TOKEN=your-actual-discord-token
BOT_NAME=Test-Sheets-to-D
GOOGLE_SPREADSHEET_NAME=Test Sheets-to-Discord
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

### 4. Setup Google Sheets

**Option A: Use the Live Example (Fastest)**

Use the public example spreadsheet:
- **URL:** https://docs.google.com/spreadsheets/d/1j9T_x0RAIWKjNm_i1QZAwSReMbS_CUIFKh3y3T5tbAg/edit?usp=sharing
- **Name:** "Test Sheets-to-Discord"
- Already configured with working example data
- Shows Discord Markdown, Title URL, Author URL, and fields
- Anyone with the link can view (read-only)

To use this:
1. Share your service account email in the spreadsheet comments if you want to test refresh
2. Or just use it read-only to see the display (refresh won't work without write access)

**Option B: Create Your Own**

1. Create a Google Spreadsheet named "Test Sheets-to-Discord"
2. Put sample JSON data in cell `Sheet1!A1`
3. Share the spreadsheet with your service account email (from `google_credentials.json`)

**Sample JSON for testing:**
```json
[["Trip 1","Ready for dispatch","https://example.com",65280,"Test System","https://example.com","Test Footer","SECRET-DATA-123","Driver","Jim Smith","Status","Ready"]]
```

**Note:** The 8th field ("SECRET-DATA-123" in this example) is the **Hidden** column. If this field contains data, a "🔍 Show Hidden" button will appear. Click it to see the hidden data. This demonstrates the `additional_buttons` feature.

### 5. Add Files

Ensure these files are in the same directory:
- `test_sheets-to-discord_bot.py` (this bot)
- `discord_embed_manager.py` (the renderer module)
- `config.py` (minimal config for the renderer)
- `google_credentials.json` (your service account credentials)
- `.env` (your configuration)

### 6. Run the Bot

```bash
python test_sheets-to-discord_bot.py
```

You should see:
```
INFO - Starting Test-Sheets-to-D...
INFO - Connected to Google Spreadsheet: Test Sheets-to-Discord
INFO - Test-Sheets-to-D connected as Test-Sheets-to-D#1234 (ID: ...)
INFO - Synced 1 command(s)
```

### 7. Test in Discord

In your Discord server, type:
```
/test
```

You should see your data displayed as interactive embed tiles!

## Custom Button Feature

This test bot demonstrates the `additional_buttons` feature. The code includes an example function `add_test_button()` that:

1. **Checks for Hidden data** - Only adds button if Hidden column has content
2. **Creates a button** - Labeled "🔍 Show Hidden"
3. **Handles clicks** - Displays the hidden data when clicked

**How it works:**

```python
def add_test_button(view, hidden_data, user_id):
    # Only add button if there's hidden data
    if not hidden_data or not hidden_data.strip():
        return
    
    button = discord.ui.Button(label="🔍 Show Hidden", ...)
    view.add_item(button)

# Usage
await display_embeds(
    interaction,
    refresh_callback=fetch_sheet_data,
    additional_buttons=add_test_button  # ← Adds custom button
)
```

**Use cases for your own buttons:**
- Trigger actions based on row data
- Open modals for user input
- Update databases
- Send notifications
- Any custom functionality you need!

The Hidden column can contain IDs, keys, or even JSON for complex data passing.

## Files Needed

```
your-test-directory/
├── test_sheets-to-discord_bot.py  ← This bot
├── discord_embed_manager.py       ← The renderer module
├── config.py                      ← Minimal config (provided)
├── requirements.txt               ← Python dependencies
├── .env                          ← Your configuration (create from .env.example)
├── .env.example                  ← Template configuration
└── google_credentials.json       ← Your service account credentials
```

## Troubleshooting

### "DISCORD_TOKEN not found in .env file"

**Problem:** `.env` file missing or incomplete

**Solution:**
1. Copy `.env.example` to `.env`
2. Fill in your actual Discord token
3. Make sure `.env` is in the same directory as the bot script

### "Spreadsheet not found"

**Problem:** Spreadsheet name doesn't match or not shared with service account

**Solution:**
1. Check spreadsheet name matches exactly (including spaces)
2. Get service account email from `google_credentials.json` (the "client_email" field)
3. Share your spreadsheet with that email address

### "Worksheet 'Sheet1' not found"

**Problem:** Worksheet renamed or doesn't exist

**Solution:**
1. Make sure your spreadsheet has a sheet named "Sheet1"
2. Or edit the bot code to use your sheet name:
   ```python
   worksheet = spreadsheet.worksheet("YourSheetName")
   ```

### "Sheet1!A1 is empty"

**Problem:** No JSON data in cell A1

**Solution:**
Put sample JSON in cell A1:
```json
[["Test Title","Test Description","",65280,"","","Test Footer","Field1","Value1"]]
```

### "/test command not showing"

**Problem:** Commands not synced or bot lacks permissions

**Solution:**
1. Wait a few minutes for Discord to sync commands
2. Check bot has "applications.commands" scope when invited
3. Re-invite bot with correct URL from Discord Developer Portal

### "No data provided" when using /test

**Problem:** fetch_sheet_data() returned None

**Solution:**
1. Check bot logs for specific error
2. Verify Google Sheets connection is working
3. Verify cell A1 has data

## What This Bot Does

**Minimal functionality:**
1. Connects to Discord
2. Connects to Google Sheets
3. Reads `Sheet1!A1`
4. Displays as embed tiles via `/test` command

**Total lines of code:** ~120 (including comments)

**Not included:**
- No role-based permissions
- No error messages to user (just logs)
- No fancy features
- Just the bare minimum to test the renderer

## Integration Pattern

This bot demonstrates the standard integration pattern:

```python
# 1. Create a fetch function
async def fetch_sheet_data():
    worksheet = spreadsheet.worksheet("Sheet1")
    return worksheet.acell('A1').value

# 2. Create a command
@tree.command(name="test")
async def test_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    # 3. Use display_embeds
    await display_embeds(
        interaction,
        json_string=None,
        refresh_callback=fetch_sheet_data
    )
```

That's it! The `discord_embed_manager` handles everything else.

## Next Steps

Once this test bot works:
1. Copy the integration pattern to your real bot
2. Customize the fetch function for your data source
3. Add error handling
4. Add permissions/roles as needed
5. Create multiple commands for different sheets

## License

Same as parent project - see LICENSE.md
