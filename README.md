# Sheets-to-Discord: Interactive Embed Renderer

Transform Google Sheets data into rich, interactive Discord embed tiles with navigation.

## Overview

**Sheets-to-Discord** is a Python module that bridges Google Sheets and Discord, enabling you to display structured data as beautiful, interactive embed tiles. All business logic stays in your spreadsheet formulas—the Python code is just a rendering engine.

### The Problem This Solves

**Traditional Approach:**
- Complex data locked in spreadsheets
- Manual copy-paste to share information
- Static, non-interactive displays
- Updates require code changes

**Sheets-to-Discord Approach:**
- Data remains in Google Sheets (single source of truth)
- One formula packages data as JSON
- Rich, interactive Discord embeds with navigation
- Updates via formula changes (no code changes)
- Clickable links back to source data
- Mobile-friendly display

### Key Features

✅ **Formula-Driven** - All logic in Google Sheets formulas  
✅ **Interactive Navigation** - << < > >> buttons with refresh  
✅ **Rich Formatting** - Markdown support, colors, URLs  
✅ **Clickable Links** - Title and Author can link to external resources  
✅ **Layout Control** - Full-width or inline fields via tilde prefix  
✅ **Mobile Optimized** - Works perfectly on phones  
✅ **General Purpose** - Works with any structured data  
✅ **Zero Maintenance** - Stable Python code, business logic in formulas  

## Visual Examples

### Error Alert (Red)
```
┌──────────────────────────────────────────┐
│ Trip L-111SYLLRP (clickable)             │
│ ERROR: Driver mismatch detected          │
├──────────────────────────────────────────┤
│ Driver          Timing         Route     │
│ Jim Smith       Anchor: 6:00 AM ...      │
│ Scheduled:      On Duty: 7:30 PM         │
│ Bob Jones       PAT: 10:00 PM            │
│ (clickable)                               │
└──────────────────────────────────────────┘
[<<] [<] [7/20] [>] [>>] [🔄]
```

### Success (Green)
```
┌──────────────────────────────────────────┐
│ Trip B-MRGSK4TH8 (clickable)             │
│ Ready for dispatch                        │
├──────────────────────────────────────────┤
│ Driver              Timing      Route    │
│ Sarah Chen          Anchor:     Truck:   │
│ (clickable)         8:30 PM     864521   │
│                                 (click.) │
└──────────────────────────────────────────┘
[<<] [<] [8/20] [>] [>>] [🔄]
```

## Table of Contents

- [Quick Start](#quick-start)
- [Table Format](#table-format)
- [Field Reference](#field-reference)
- [Creating JSON from Google Sheets](#creating-json-from-google-sheets)
- [Integration Guide](#integration-guide)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Dependencies

```bash
pip install discord.py gspread oauth2client
```

### 2. Add Module to Your Bot

Copy `discord_embed_manager.py` to your bot's directory.

### 3. Create Your Data Table in Google Sheets

| Title | Description | TitleURL | Color | Author | AuthorURL | Footer | Field1 | Value1 | Field2 | Value2 |
|-------|-------------|----------|-------|--------|-----------|--------|--------|--------|--------|--------|
| Trip 1 | Ready | http://... | 65280 | System | http://... | Footer text | Driver | John | Status | Ready |

### 4. Convert to JSON

Use the ToJSON formula (see [Creating JSON section](#creating-json-from-google-sheets)) to package your table as JSON in cell A1.

### 5. Integrate into Your Bot

```python
from discord_embed_manager import display_embeds

async def my_refresh_callback():
    # Fetch JSON from your Google Sheets cell A1
    worksheet = sheet.worksheet("MySheet")
    return worksheet.acell('A1').value

@bot.tree.command(name="mydata")
async def my_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await display_embeds(
        interaction,
        json_string=None,  # Will call refresh_callback
        refresh_callback=my_refresh_callback
    )
```

## Table Format

### Column Structure

Your table must have **at least 7 columns** in this exact order:

| Index | Column | Type | Max Length | Required | Description |
|-------|--------|------|-----------|----------|-------------|
| 0 | Title | String | 256 chars | Yes | Embed title (bold, large text) |
| 1 | Description | String | 4096 chars | Yes | Main content below title |
| 2 | TitleURL | URL | No limit | No | Makes title clickable |
| 3 | Color | Integer | - | Yes | (R×256+G)×256+B |
| 4 | Author | String | 256 chars | No | Small text above title |
| 5 | AuthorURL | URL | No limit | No | Makes author clickable |
| 6 | Footer | String | 2048 chars | No | Plain text at bottom |
| 7+ | Field Name/Value | String | 256/1024 | No | Up to 25 pairs |

### Important Notes

- **No headers** in the table - each row becomes one embed tile
- **Empty columns** are allowed (will display empty)
- **Field pairs** start at index 7 (Field1 Name, Field1 Value, Field2 Name, Field2 Value, ...)
- **Total limit**: 6000 characters per embed tile
- **Maximum fields**: 25 name/value pairs per tile

### Example Table

```
Row 1:
[0] "Trip B-123"
[1] "Driver ready for dispatch"
[2] "https://relay.amazon.com/trips/B-123"
[3] 65280
[4] "Amazon Relay"
[5] "https://relay.amazon.com"
[6] "Acme Trucking • Updated 5 mins ago"
[7] "Driver"
[8] "Jim Smith"
[9] "Status"
[10] "Ready"
```

## Field Reference

### Title (Column 0)

**Purpose:** Main heading of the embed tile

**Characteristics:**
- Large, bold text
- Clickable if TitleURL provided
- Truncated at 256 characters
- Supports limited Markdown (bold/italic subtle)

**Example:**
```
"Trip B-0R8P3V8C1 Solo2 T4 Mon 0600"
```

### Description (Column 1)

**Purpose:** Main content area below title

**Characteristics:**
- Regular text
- Supports full Markdown
- Truncated at 4096 characters
- Can contain newlines (`\n`)

**Example:**
```
"ERROR: Relay driver is Jim Smith but scheduled driver is Bob Jones for Solo2 T4 06:00 in section Solo2_A"
```

**Markdown Examples:**
```
**Bold text**
_Italic text_
__Underline__
~~Strikethrough~~
`code`
> Quote
```

### TitleURL (Column 2)

**Purpose:** Make title clickable

**Requirements:**
- Must start with `http://` or `https://`
- Invalid URLs logged as WARNING and ignored
- Leave empty for non-clickable title

**Example:**
```
"https://relay.amazon.com/trips/B-0R8P3V8C1"
```

**Use Cases:**
- Link to external system
- Link to Google Sheet cell
- Link to documentation
- Link to tracking page

### Color (Column 3)

**Purpose:** Set left border color (visual priority indicator)

**Format:** Integer calculated as `(Red * 256 + Green) * 256 + Blue`

**Common Colors:**

| Color | Formula | Integer Value |
|-------|---------|---------------|
| Red | `(255*256+0)*256+0` | 16711680 |
| Yellow | `(255*256+255)*256+0` | 16776960 |
| Green | `(0*256+255)*256+0` | 65280 |
| Blue | `(0*256+0)*256+255` | 255 |
| Orange | `(255*256+165)*256+0` | 16753920 |
| Purple | `(128*256+0)*256+128` | 8388736 |

**Google Sheets Formula:**
```
=(Red * 256 + Green) * 256 + Blue
```

**Example Use:**
```
=IF(HasError, 16711680, IF(HasWarning, 16776960, 65280))
```

### Author (Column 4)

**Purpose:** Small text above title (secondary attribution)

**Characteristics:**
- Small, subtle text
- Plain text only (no Markdown)
- Clickable if AuthorURL provided
- Truncated at 256 characters
- Optional (leave empty if not needed)

**Example:**
```
"Amazon Relay"
```

### AuthorURL (Column 5)

**Purpose:** Make author name clickable

**Requirements:**
- Must start with `http://` or `https://`
- Invalid URLs logged as WARNING and ignored
- Leave empty for non-clickable author

**Example:**
```
"https://relay.amazon.com"
```

### Footer (Column 6)

**Purpose:** Small text at bottom of embed

**Characteristics:**
- Plain text only (no Markdown support - Discord limitation)
- Truncated at 2048 characters
- Optional (leave empty if not needed)

**Example:**
```
"Acme Trucking • Updated 5 minutes ago"
```

**Important:** Footer does NOT support Markdown. For formatted footer-style content, use a full-width field instead:
```
Field Name: "~"
Field Value: "**Formatted** _footer_ text"
```

### Fields (Columns 7+)

**Purpose:** Structured data display in rows of 3

**Format:** Alternating name/value pairs
- Column 7: Field 1 Name (256 chars max)
- Column 8: Field 1 Value (1024 chars max)
- Column 9: Field 2 Name
- Column 10: Field 2 Value
- ... up to Field 25

**Display:** Shows 3 fields per row (inline=True)

**Example:**
```
Column 7: "Driver"
Column 8: "Jim Smith"
Column 9: "Timing"
Column 10: "Anchor: Mon 6:00 AM\nOn Duty: Mon 7:30 PM"
Column 11: "Route"
Column 12: "Truck: 123456\nYard: LAX1"
```

**Visual Result:**
```
┌────────────────────────────────────┐
│ Driver        Timing       Route   │
│ Jim Smith     Anchor:      Truck:  │
│               Mon 6:00 AM  123456  │
│               On Duty:     Yard:   │
│               Mon 7:30 PM  LAX1    │
└────────────────────────────────────┘
```

### Field Layout Control (Tilde Prefix)

**Purpose:** Force field to span full width instead of 1/3 width

**How:** Start field name with `~` (tilde character)

**Effect:**
- Field displays full-width (inline=False)
- Tilde is removed from displayed name
- Useful for long text blocks or footer-style content

**Example:**

**Standard (3 columns):**
```
Field 1: "Driver"     Field 2: "Timing"     Field 3: "Route"
Value 1: "Jim Smith"  Value 2: "9:30 PM"    Value 3: "LAX1"
```

**With Tilde (full-width):**
```
Field 1: "Driver"     Field 2: "Timing"     Field 3: "Route"
Value 1: "Jim Smith"  Value 2: "9:30 PM"    Value 3: "LAX1"

Field 4: "~Details"   (full-width field)
Value 4: "**Important:** This trip requires special handling due to..."
```

**Visual Result:**
```
┌────────────────────────────────────┐
│ Driver      Timing       Route     │
│ Jim Smith   9:30 PM      LAX1      │
├────────────────────────────────────┤
│ Details                            │
│ Important: This trip requires      │
│ special handling due to...         │
└────────────────────────────────────┘
```

**Use Cases:**
- Long explanatory text
- Formatted "footer" content (supports Markdown unlike real footer)
- Full-width status messages
- Multi-line notes

## Creating JSON from Google Sheets

### The ToJSON Formula

This formula converts any 2D range into properly escaped JSON:

```javascript
=LET(
   MyRange, $A$1:$M$20,
   ToJSON, LAMBDA(rng, 
      "[" & TEXTJOIN(",", TRUE,
         BYROW(rng, LAMBDA(row,
            "[" & TEXTJOIN(",", TRUE,
               ARRAYFORMULA(
                  """" & 
                  SUBSTITUTE(
                     SUBSTITUTE(
                        SUBSTITUTE(row, "\", "\\"),
                        CHAR(10), "\n"
                     ),
                     """", "\"""
                  ) & 
                  """"
               )
            ) & "]"
         ))
      ) & "]"
   ),
   ToJSON(MyRange)
)
```

### How It Works

**1. LET Function Structure**
```
=LET(
   variable1, value1,
   variable2, value2,
   final_expression
)
```
Defines variables and returns the final expression.

**2. MyRange Variable**
```
MyRange, $A$1:$M$20
```
Your data range. Use absolute references ($) to prevent shifting.

**3. ToJSON LAMBDA**
```
ToJSON, LAMBDA(rng, ...)
```
Creates a reusable function that takes a range parameter.

**4. Character Escaping (Critical!)**

Three special characters must be escaped for valid JSON:

**a. Backslashes:** `\` → `\\`
```
SUBSTITUTE(row, "\", "\\")
```
Must be first! Otherwise you'd escape your own escape characters.

**b. Newlines:** actual newline → `\n`
```
SUBSTITUTE(..., CHAR(10), "\n")
```
`CHAR(10)` is the newline character in Google Sheets.

**c. Quotes:** `"` → `\"`
```
SUBSTITUTE(..., """", "\""")
```
- `""""` in Sheets = one literal quote
- `"\"""` = escaped quote for JSON

**5. Array Processing**

**BYROW:** Processes each row individually
```
BYROW(rng, LAMBDA(row, ...))
```

**ARRAYFORMULA:** Applies substitutions to all cells at once
```
ARRAYFORMULA("""" & SUBSTITUTE(...) & """")
```

**TEXTJOIN:** Joins with commas
```
TEXTJOIN(",", TRUE, ...)
```
- Used twice: once for cells within a row, once for all rows
- `TRUE` = ignore empty cells

**6. JSON Structure**
```
"[" & ... & "]"
```
Outer brackets create main array, inner brackets (from BYROW) create row arrays.

Result: `[["cell1","cell2"],["cell3","cell4"]]`

### Practical Example

**Input Range (A1:H3):**
```
Title          Description    URL              Color    Author  AuthorURL  Footer       Field1
Trip 1         Ready          http://ex.com    65280    System  http://... Company      Driver
Trip 2         Error          http://ex.com    16711680 System  http://... Company      Driver
```

**Formula Output:**
```json
[["Title","Description","URL","Color","Author","AuthorURL","Footer","Field1"],
 ["Trip 1","Ready","http://ex.com","65280","System","http://...","Company","Driver"],
 ["Trip 2","Error","http://ex.com","16711680","System","http://...","Company","Driver"]]
```

### Building Your Data in Google Sheets

**Strategy:** Use helper columns to prepare data, then reference in final range.

```
Column A: TripID (from your system)
Column B: =IF(HasError(A2), "ERROR: " & ErrorMessage(A2), "Ready")  // Description
Column C: ="http://relay.com/trips/" & A2  // URL
Column D: =IF(HasError(A2), 16711680, 65280)  // Color
... etc ...

Then: MyRange = B2:I100 (exclude TripID, include only embed columns)
```

### Tips and Best Practices

**1. Use Helper Columns**
Don't try to do everything in the ToJSON formula. Prepare your data first:
- Calculate colors in one column
- Build descriptions in another
- Format dates/times
- Create clickable links

**2. Test Your Data First**
Before converting to JSON:
- Verify all columns have correct data
- Check that URLs are valid
- Ensure colors are integers
- Confirm field names are descriptive

**3. Validate JSON**
After generating:
1. Copy formula output
2. Paste into [JSONLint](https://jsonlint.com/)
3. Verify structure
4. Test in Discord

**4. Empty Cells**
The formula preserves empty cells as empty strings `""`. This is intentional - the renderer handles them correctly.

**5. Performance**
For large datasets:
- Limit rows (Discord shows one at a time)
- Use FILTER to show only relevant rows
- Pre-calculate complex formulas
- Consider caching if data doesn't change often

**6. Newlines in Formulas**
To include newlines:
```
="Line 1" & CHAR(10) & "Line 2"
```
ToJSON converts to `\n` automatically.

**7. Markdown in Values**
Include Markdown directly:
```
="**Driver:** " & DriverName & CHAR(10) & "_Route:_ " & Route
```

### Advanced Techniques

**Conditional Rows**
```
=LET(
   AllData, A1:G100,
   FilteredData, FILTER(AllData, (StatusColumn="Active")),
   ToJSON, LAMBDA(...),
   ToJSON(FilteredData)
)
```

**Dynamic Field Count**
Some rows can have more fields than others - the renderer handles variable field counts automatically.

**Sorting**
```
=LET(
   Data, A1:G100,
   SortedData, SORT(Data, 4, TRUE),  // Sort by column 4 (Color) ascending
   ToJSON, LAMBDA(...),
   ToJSON(SortedData)
)
```

**Combining Multiple Sources**
```
=LET(
   Trips, Trips!A2:G10,
   Alerts, Alerts!A2:G5,
   Combined, {Trips; Alerts},
   ToJSON, LAMBDA(...),
   ToJSON(Combined)
)
```

## Integration Guide

### Prerequisites

**You must already have:**
- A Discord bot created and invited to your server
- Python 3.8+ environment
- Bot token configured
- Basic command structure working

**Out of scope:**
- Creating a Discord bot
- Setting up Discord Developer Portal
- Bot authentication and tokens
- Discord permissions configuration

### Installation

**1. Copy Module**
```bash
cp discord_embed_manager.py /path/to/your/bot/
```

**2. Install Dependencies**
```bash
pip install discord.py gspread oauth2client
```

### Integration Steps

**Step 1: Import the Module**
```python
from discord_embed_manager import display_embeds
```

**Step 2: Create Data Fetch Function**

This function retrieves JSON from your data source (typically Google Sheets):

```python
async def fetch_my_data():
    """
    Fetch JSON string from your data source
    
    Returns:
        str: JSON string, or None if error
    """
    try:
        # Example: Read from Google Sheets
        worksheet = sheet.worksheet("MyDataSheet")
        json_string = worksheet.acell('A1').value
        
        if not json_string:
            logger.error("Cell A1 is empty")
            return None
            
        return json_string
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return None
```

**Step 3: Create Command Handler**

```python
@bot.tree.command(name="mydata", description="Display my data")
async def mydata_command(interaction: discord.Interaction):
    """Handle /mydata command"""
    
    # Defer response (required - this can take a few seconds)
    await interaction.response.defer(ephemeral=True)
    
    # Display using embed manager
    await display_embeds(
        interaction,
        json_string=None,  # Will trigger refresh_callback
        refresh_callback=fetch_my_data
    )
```

**That's it!** The embed manager handles:
- JSON parsing
- Embed creation
- Navigation buttons
- Refresh functionality
- Error handling
- Timeout management

### Integration Patterns

**Pattern 1: Always Fetch Fresh Data**
```python
await display_embeds(
    interaction,
    json_string=None,
    refresh_callback=fetch_my_data
)
```
Best for: Dynamic data that changes frequently

**Pattern 2: Pre-fetched Data (No Refresh)**
```python
json_string = await fetch_my_data()
await display_embeds(
    interaction,
    json_string=json_string,
    refresh_callback=None  # No refresh button
)
```
Best for: Static data, archived data, snapshots

**Pattern 3: Pre-fetched with Refresh Option**
```python
json_string = await fetch_my_data()
await display_embeds(
    interaction,
    json_string=json_string,
    refresh_callback=fetch_my_data  # Refresh button shown
)
```
Best for: Balance of immediate display + refresh capability

### Error Handling

The embed manager handles most errors automatically:
- Invalid JSON → Error message to user
- Empty data → "Nothing to display"
- Parse failures → Error message with details
- Refresh failures → Error message, keeps old data

**Your responsibility:** Handle errors in your fetch function and return `None` on failure.

```python
async def fetch_my_data():
    try:
        # ... fetch data ...
        return json_string
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return None  # Manager will show error
```

### Multiple Commands

You can create multiple commands using the same manager:

```python
async def fetch_trips():
    return sheet.worksheet("Trips").acell('A1').value

async def fetch_drivers():
    return sheet.worksheet("Drivers").acell('A1').value

async def fetch_alerts():
    return sheet.worksheet("Alerts").acell('A1').value

@bot.tree.command(name="trips")
async def trips_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await display_embeds(interaction, None, fetch_trips)

@bot.tree.command(name="drivers")
async def drivers_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await display_embeds(interaction, None, fetch_drivers)

@bot.tree.command(name="alerts")
async def alerts_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await display_embeds(interaction, None, fetch_alerts)
```

## Advanced Features

### Custom Navigation Labels

Currently, navigation buttons use standard symbols (<< < > >>). Future versions may support custom labels.

### Conditional Formatting

All conditional formatting should be done in your Google Sheets formulas:

```
// Color based on priority
=IF(Priority="HIGH", 16711680, IF(Priority="MED", 16776960, 65280))

// Show/hide fields based on status
=IF(Status="Active", "Driver", "")
=IF(Status="Active", DriverName, "")
```

### Dynamic Field Count

Each row can have different numbers of fields. The renderer automatically:
- Skips trailing empty field pairs
- Preserves internal gaps (Field 1, Field 3 with Field 2 empty)

### Combining Multiple Sources

Use Google Sheets to combine data from multiple sources:

```
=LET(
   Source1, QUERY(Sheet1!A:G, "SELECT * WHERE Status='Active'"),
   Source2, QUERY(Sheet2!A:G, "SELECT * WHERE Flag=TRUE"),
   Combined, {Source1; Source2},
   ToJSON, LAMBDA(...),
   ToJSON(Combined)
)
```

### Clickable Deep Links

Create links to specific cells in Google Sheets:

```
="https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=SHEET_ID&range=A5"
```

This opens the sheet and selects cell A5, perfect for quick edits.

### Markdown Richness

Take full advantage of Discord Markdown in Description and Field Values:

```
Description:
**ERROR:** Driver mismatch detected
_This requires immediate attention_

Field Value:
> Status: **Ready**
> Driver: _Assigned_
> Truck: `321554`
```

## API Reference

### Main Function

#### `display_embeds(interaction, json_string=None, refresh_callback=None)`

Display JSON data as interactive Discord embed tiles.

**Parameters:**
- `interaction` (discord.Interaction): Discord interaction object (required)
- `json_string` (str, optional): JSON string to display
- `refresh_callback` (async function, optional): Function that returns fresh JSON

**Behavior:**
- If `json_string` is None and `refresh_callback` is provided, calls callback to fetch data
- If `json_string` is provided, displays it immediately
- If `refresh_callback` is provided, adds refresh button to navigation
- Interaction must already be deferred before calling this function

**Returns:** None

**Example:**
```python
await display_embeds(
    interaction,
    json_string=None,
    refresh_callback=my_fetch_function
)
```

### Helper Functions

#### `parse_json_cell(cell_value)`

Parse JSON string into list of lists.

**Parameters:**
- `cell_value` (str): JSON string

**Returns:** 
- List of lists on success
- None on parse error

**Logs:**
- ERROR on parse failure

#### `validate_url(url, field_name, row_idx)`

Validate URL starts with http:// or https://.

**Parameters:**
- `url` (str): URL to validate
- `field_name` (str): Field name for logging
- `row_idx` (int): Row index for logging

**Returns:**
- Valid URL string
- None if invalid or empty

**Logs:**
- WARNING for invalid URLs

#### `parse_embed_data(data)`

Convert parsed JSON into embed specifications.

**Parameters:**
- `data` (list): List of lists from parse_json_cell

**Returns:**
- List of embed specification dicts
- Empty list if no valid data

**Logs:**
- WARNING for rows with insufficient columns
- INFO for truncations
- ERROR for 6000 character limit exceeded

#### `create_discord_embed(embed_spec)`

Create Discord Embed object from specification.

**Parameters:**
- `embed_spec` (dict): Embed specification with keys:
  - title, description, title_url, color, author, author_url, footer, fields

**Returns:**
- discord.Embed object

### Classes

#### `EmbedNavigationView`

Discord UI View with navigation buttons.

**Parameters:**
- `embeds_spec` (list): List of embed specifications
- `current_page` (int): Starting page (0-indexed)
- `user_id` (int): Discord user ID who can interact
- `refresh_callback` (async function, optional): Refresh function

**Attributes:**
- `message`: Discord message object (set after sending)
- `timeout`: 300 seconds (5 minutes)

**Methods:**
- `goto_top()`: Jump to first page
- `previous_page()`: Go to previous page
- `next_page()`: Go to next page
- `goto_bottom()`: Jump to last page
- `refresh_data()`: Refresh from callback
- `on_timeout()`: Handle 5-minute timeout

## Examples

### Example 1: Simple Trip Display

**Google Sheets Table:**
| Title | Description | URL | Color | Author | AuthorURL | Footer | Driver | John | Status | Ready |
|-------|-------------|-----|-------|--------|-----------|--------|--------|------|--------|-------|
| Trip B-123 | Ready for dispatch | http://... | 65280 | System | | Company | Driver | John | Status | Ready |

**Python Code:**
```python
async def fetch_trips():
    return sheet.worksheet("Trips").acell('A1').value

@bot.tree.command(name="trips")
async def trips_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await display_embeds(interaction, None, fetch_trips)
```

### Example 2: Error Alerts with Priority Colors

**Google Sheets Formula:**
```
=LET(
   Errors, FILTER(Trips!A:G, Trips!H:H = "ERROR"),
   WithColor, ARRAYFORMULA({Errors, (255*256+0)*256+0}),  // Add red color
   ToJSON, LAMBDA(...),
   ToJSON(WithColor)
)
```

### Example 3: Dynamic Driver Schedule

**Google Sheets:**
```
Title: =DriverName & " Schedule"
Description: ="**Shift:** " & ShiftTime & CHAR(10) & "**Route:** " & Route
TitleURL: ="" // No link
Color: =IF(Status="Available", 65280, 16776960)
```

### Example 4: Clickable Links to Sheet Cells

**Formula:**
```
DriverURL: ="https://docs.google.com/spreadsheets/d/" & SpreadsheetID & "/edit#gid=" & SheetID & "&range=" & CellAddress
```

Click driver name → Opens schedule sheet at exact cell for quick edits.

## Dependencies

### Required Python Packages

```bash
pip install discord.py gspread oauth2client
```

**Package Versions:**
- `discord.py` >= 2.0.0
- `gspread` >= 5.0.0
- `oauth2client` >= 4.1.3

### External Dependencies

**1. Logging**

The module requires a logger named after your bot:

```python
from config import Config
config = Config()
logger = logging.getLogger(config.bot_name)
```

**To satisfy this dependency:**

**Option A:** Create a `config.py` with:
```python
class Config:
    def __init__(self):
        self.bot_name = "MyBot"
```

**Option B:** Modify `discord_embed_manager.py`:
```python
# Replace this:
config = Config()
logger = logging.getLogger(config.bot_name)

# With this:
logger = logging.getLogger("MyBot")
```

**2. Google Sheets Connection**

Your fetch callback needs to access Google Sheets. This is **your responsibility** to set up.

**Typical setup:**
```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheets():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json',
        scope
    )
    client = gspread.authorize(creds)
    return client.open("My Spreadsheet")

sheet = connect_to_sheets()
```

**3. Discord Bot Setup**

You must have:
- Discord bot created and configured
- Bot token in environment/config
- Bot invited to server with appropriate permissions
- Command tree synced

### No Other External Dependencies

The module is self-contained and only requires:
- Standard Python libraries (json, logging, asyncio)
- Discord.py for Discord interaction
- gspread for Google Sheets (in your fetch function)
- A logger instance (easily satisfied)

## Troubleshooting

### Common Issues

**Issue 1: "No data provided"**

**Cause:** refresh_callback returned None or empty string

**Solution:**
- Check your fetch function returns valid JSON
- Verify Google Sheets cell A1 has data
- Check logs for fetch errors

**Issue 2: "Failed to parse JSON"**

**Cause:** Invalid JSON format

**Solution:**
- Copy cell A1 content
- Paste into [JSONLint](https://jsonlint.com/)
- Check for:
  - Missing quotes
  - Unescaped characters
  - Malformed arrays

**Issue 3: "This interaction failed"**

**Cause:** 15-minute Discord interaction timeout exceeded

**Solution:**
- This is expected after 15 minutes
- User should just run command again
- View timeout (5 min) removes buttons and shows message

**Issue 4: URLs not clickable**

**Cause:** URL doesn't start with http:// or https://

**Solution:**
- Check logs for "Invalid URL" warnings
- Ensure URLs have proper scheme
- Example: `http://example.com` not `example.com`

**Issue 5: Footer not formatting**

**Cause:** Discord footer doesn't support Markdown

**Solution:**
- Use full-width field instead
- Field name: `~`
- Field value: Your formatted text with Markdown

**Issue 6: Fields not full-width**

**Cause:** Missing tilde prefix

**Solution:**
- Start field name with `~`
- Example: `~Details` not `Details`

**Issue 7: "Row has fewer than 7 required columns"**

**Cause:** Table missing required columns

**Solution:**
- Ensure at least 7 columns: Title, Description, TitleURL, Color, Author, AuthorURL, Footer
- Empty columns are okay, but they must exist

### Debug Logging

Enable debug logging to see detailed processing:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Key log messages:**
- INFO: "Read X characters from Sheet!A1"
- INFO: "Calling refresh_callback to fetch initial data..."
- INFO: "Displayed embeds (showing 1/N)"
- WARNING: "Invalid URL..."
- ERROR: "Failed to parse JSON..."
- ERROR: "Row X: Embed truncated at field Y due to 6000 character limit"

### Performance Issues

**Problem:** Slow refresh times

**Solutions:**
- Optimize Google Sheets formulas
- Reduce data complexity
- Use FILTER to limit rows
- Cache calculated values

**Problem:** Discord rate limits

**Solutions:**
- Don't refresh too frequently
- Limit number of users refreshing simultaneously
- Consider caching in your fetch function

## License

See [sheets-to-discord_LICENSE.md](sheets-to-discord_LICENSE.md) for full license terms.

**Summary:** 
- Free to use for any purpose (commercial or personal)
- Attribution required
- Modifications allowed
- No warranty provided

## Contributing

This project is currently **read-only** on GitHub. To request features or report bugs, please open an issue.

## Support

For questions or issues:
1. Check this README thoroughly
2. Review examples in the `/examples` directory
3. Open a GitHub issue with:
   - Your table structure
   - JSON output (first 500 chars)
   - Error logs
   - What you expected vs. what happened

## Credits

Created to bridge Google Sheets and Discord for a trucking company's operations management, enabling rich data displays without coding knowledge.

**Key Innovation:** Keep business logic in spreadsheet formulas (where domain experts are comfortable) while providing powerful Discord integration (where teams communicate).

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Python:** 3.8+  
**Discord.py:** 2.0+
