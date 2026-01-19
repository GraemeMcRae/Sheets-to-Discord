"""
Discord Embed Manager - General Purpose JSON to Discord Embed Renderer

This module provides a general-purpose system for displaying JSON data as
interactive Discord embed tiles with navigation.

Features:
- Parse JSON from Google Sheets or any source
- Render as Discord Embed tiles with navigation buttons
- Optional refresh callback for live data updates
- URL validation and Markdown support
- Tilde prefix (~) for full-width fields
- 5-minute timeout with graceful degradation

Usage:
    from discord_embed_manager import display_embeds
    
    async def my_refresh_callback():
        # Fetch fresh JSON data
        return json_string
    
    await display_embeds(interaction, json_string, refresh_callback=my_refresh_callback)
"""

import discord
from discord import app_commands
import logging
import json
from config import Config

config = Config()
logger = logging.getLogger(config.bot_name)


def parse_json_cell(cell_value):
    """
    Parse JSON from cell value
    
    Args:
        cell_value: String containing standard JSON (list of lists)
                   Quotes escaped as \" and backslashes as \\
        
    Returns:
        Parsed data structure (list of lists) or None if error
    """
    try:
        data = json.loads(cell_value)
        
        # Validate it's a list of lists
        if not isinstance(data, list):
            logger.error("Cell data is not a list")
            return None
        
        for row in data:
            if not isinstance(row, list):
                logger.error("Cell data contains non-list row")
                return None
        
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from cell: {e}")
        logger.error(f"Cell content (first 500 chars): {cell_value[:500]}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing cell: {e}")
        return None


def validate_url(url, field_name, row_idx):
    """
    Validate that a URL is well-formed and uses http/https scheme
    
    Args:
        url: URL string to validate
        field_name: Name of the field (for logging)
        row_idx: Row index (for logging)
        
    Returns:
        Valid URL string or None if invalid
    """
    if not url:
        return None
    
    url_str = str(url).strip()
    
    if not url_str:
        return None
    
    # Check if URL starts with http:// or https://
    if not (url_str.startswith('http://') or url_str.startswith('https://')):
        logger.warning(f"Row {row_idx + 1}: Invalid {field_name} URL '{url_str}' - must start with http:// or https://. Treating as empty.")
        return None
    
    # Basic validation - Discord will reject if malformed
    # We just check for scheme, Discord does the rest
    return url_str


def parse_embed_data(data):
    """
    Parse table data into Discord Embed specifications
    
    Table format (no headers):
    [0] Title (256 chars)
    [1] Description (4096 chars)
    [2] TitleURL (optional URL for title)
    [3] Color (integer: (R*256+G)*256+B)
    [4] Author (256 chars, optional)
    [5] AuthorURL (optional URL for author)
    [6] Footer (2048 chars)
    [7] Field 1 Name (256 chars)
    [8] Field 1 Value (1024 chars)
    [9] Field 2 Name (256 chars)
    [10] Field 2 Value (1024 chars)
    ... up to 25 field pairs (indices 7-56)
    
    Total embed limit: 6000 characters
    
    Returns:
        List of embed specs (one per row)
    """
    if not data or len(data) == 0:
        return []
    
    embeds = []
    
    for row_idx, row in enumerate(data):
        if len(row) < 7:
            logger.warning(f"Row {row_idx + 1} has fewer than 7 required columns, skipping")
            continue
        
        # Extract fixed fields with URL columns
        title = str(row[0])[:256] if len(row) > 0 else ""
        description = str(row[1])[:4096] if len(row) > 1 else ""
        title_url = validate_url(row[2] if len(row) > 2 else None, "TitleURL", row_idx)
        
        try:
            color = int(row[3]) if len(row) > 3 and row[3] else 0
        except (ValueError, TypeError):
            logger.warning(f"Row {row_idx + 1}: Invalid color value '{row[3]}', using 0")
            color = 0
        
        author = str(row[4])[:256] if len(row) > 4 and row[4] else None
        author_url = validate_url(row[5] if len(row) > 5 else None, "AuthorURL", row_idx)
        footer = str(row[6])[:2048] if len(row) > 6 else ""
        
        # Log truncations
        if len(row) > 0 and len(str(row[0])) > 256:
            logger.info(f"Row {row_idx + 1}: Title truncated from {len(str(row[0]))} to 256 chars")
        if len(row) > 1 and len(str(row[1])) > 4096:
            logger.info(f"Row {row_idx + 1}: Description truncated from {len(str(row[1]))} to 4096 chars")
        if len(row) > 4 and len(str(row[4])) > 256:
            logger.info(f"Row {row_idx + 1}: Author truncated from {len(str(row[4]))} to 256 chars")
        if len(row) > 6 and len(str(row[6])) > 2048:
            logger.info(f"Row {row_idx + 1}: Footer truncated from {len(str(row[6]))} to 2048 chars")
        
        # Extract fields (up to 25 pairs, starting at index 7)
        fields = []
        total_chars = len(title) + len(description) + len(footer)
        if author:
            total_chars += len(author)
        
        for field_idx in range(25):
            name_idx = 7 + (field_idx * 2)
            value_idx = 8 + (field_idx * 2)
            
            if name_idx >= len(row):
                break
            
            # Check if all remaining fields are empty
            all_remaining_empty = True
            for check_idx in range(name_idx, min(len(row), 57)):
                if row[check_idx]:
                    all_remaining_empty = False
                    break
            
            if all_remaining_empty:
                break
            
            name = str(row[name_idx]) if name_idx < len(row) else ""
            value = str(row[value_idx]) if value_idx < len(row) else ""
            
            # Truncate field name and value
            original_name_len = len(name)
            original_value_len = len(value)
            name = name[:256]
            value = value[:1024]
            
            if original_name_len > 256:
                logger.info(f"Row {row_idx + 1}, Field {field_idx + 1}: Name truncated from {original_name_len} to 256 chars")
            if original_value_len > 1024:
                logger.info(f"Row {row_idx + 1}, Field {field_idx + 1}: Value truncated from {original_value_len} to 1024 chars")
            
            # Check 6000 character limit
            field_chars = len(name) + len(value)
            if total_chars + field_chars > 6000:
                logger.error(f"Row {row_idx + 1}: Embed truncated at field {field_idx + 1} due to 6000 character limit")
                break
            
            total_chars += field_chars
            fields.append({"name": name, "value": value})
        
        embeds.append({
            "title": title,
            "description": description,
            "title_url": title_url,
            "color": color,
            "author": author,
            "author_url": author_url,
            "footer": footer,
            "fields": fields
        })
    
    return embeds


def create_discord_embed(embed_spec):
    """
    Create Discord Embed from specification
    
    Args:
        embed_spec: Dict with title, description, title_url, color, author, 
                   author_url, footer, fields
        
    Returns:
        discord.Embed object
        
    Notes:
        - Field names starting with '~' are displayed full-width (inline=False)
        - The '~' prefix is removed from the displayed name
    """
    embed = discord.Embed(
        title=embed_spec["title"] or None,
        description=embed_spec["description"] or None,
        url=embed_spec["title_url"],  # URL for title
        color=embed_spec["color"]
    )
    
    # Set author if provided (name or URL)
    if embed_spec["author"] or embed_spec["author_url"]:
        embed.set_author(
            name=embed_spec["author"] or "\u200b",  # Zero-width space if no name
            url=embed_spec["author_url"]
        )
    
    # Set footer if provided (plain text, no Markdown support in Discord)
    if embed_spec["footer"]:
        embed.set_footer(text=embed_spec["footer"])
    
    # Add fields (Discord renders max 3 per row with inline=True)
    for field in embed_spec["fields"]:
        # Skip completely empty field pairs
        if not field["name"] and not field["value"]:
            continue
        
        field_name = field["name"]
        field_value = field["value"]
        
        # Check if field name starts with ~ (force full-width)
        if field_name.startswith("~"):
            inline = False
            field_name = field_name[1:]  # Remove the ~ prefix
        else:
            inline = True
        
        embed.add_field(
            name=field_name or "\u200b",  # Zero-width space for empty names
            value=field_value or "\u200b",  # Zero-width space for empty values
            inline=inline
        )
    
    return embed


class EmbedNavigationView(discord.ui.View):
    """
    View with navigation buttons for embed display
    
    Args:
        embeds_spec: List of embed specifications
        current_page: Starting page (0-indexed)
        user_id: User ID who can interact with this view
        refresh_callback: Optional async function to fetch fresh data
    """
    
    def __init__(self, embeds_spec, current_page, user_id, refresh_callback=None):
        super().__init__(timeout=300)  # 5 minute timeout
        self.embeds_spec = embeds_spec
        self.current_page = current_page
        self.total_pages = len(embeds_spec)
        self.user_id = user_id
        self.refresh_callback = refresh_callback
        self.message = None  # Will be set after sending
        self.update_buttons()
    
    async def on_timeout(self):
        """Called when view times out after 5 minutes"""
        if self.message:
            try:
                # Get current embed and update footer
                embed = create_discord_embed(self.embeds_spec[self.current_page])
                
                # Add timeout message to footer
                original_footer = embed.footer.text if embed.footer else ""
                timeout_footer = f"{original_footer}\n\n⏱️ View expired due to inactivity. Please refresh to continue."
                embed.set_footer(text=timeout_footer)
                
                # Remove all buttons
                await self.message.edit(embed=embed, view=None)
                logger.info(f"Embed view timed out for user {self.user_id}")
            except Exception as e:
                logger.warning(f"Failed to update message on timeout: {e}")
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.clear_items()
        
        # Top button (<<)
        top_button = discord.ui.Button(label="<<", style=discord.ButtonStyle.secondary, disabled=(self.current_page == 0))
        top_button.callback = self.goto_top
        self.add_item(top_button)
        
        # Previous button (<)
        prev_button = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=(self.current_page == 0))
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Page indicator
        page_button = discord.ui.Button(label=f"{self.current_page + 1}/{self.total_pages}", style=discord.ButtonStyle.secondary, disabled=True)
        self.add_item(page_button)
        
        # Next button (>)
        next_button = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=(self.current_page >= self.total_pages - 1))
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        # Bottom button (>>)
        bottom_button = discord.ui.Button(label=">>", style=discord.ButtonStyle.secondary, disabled=(self.current_page >= self.total_pages - 1))
        bottom_button.callback = self.goto_bottom
        self.add_item(bottom_button)
        
        # Refresh button (only if callback provided)
        if self.refresh_callback:
            refresh_button = discord.ui.Button(label="🔄", style=discord.ButtonStyle.success)
            refresh_button.callback = self.refresh_data
            self.add_item(refresh_button)
    
    async def goto_top(self, interaction: discord.Interaction):
        """Go to first page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        self.current_page = 0
        embed = create_discord_embed(self.embeds_spec[self.current_page])
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            embed = create_discord_embed(self.embeds_spec[self.current_page])
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            embed = create_discord_embed(self.embeds_spec[self.current_page])
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def goto_bottom(self, interaction: discord.Interaction):
        """Go to last page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        self.current_page = self.total_pages - 1
        embed = create_discord_embed(self.embeds_spec[self.current_page])
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def refresh_data(self, interaction: discord.Interaction):
        """Refresh data from source"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your view", ephemeral=True)
            return
        
        if not self.refresh_callback:
            await interaction.response.defer()
            return
        
        await interaction.response.defer()
        
        try:
            # Call refresh callback to get fresh JSON
            json_string = await self.refresh_callback()
            
            if not json_string:
                await interaction.followup.send("❌ Refresh failed: No data returned", ephemeral=True)
                return
            
            # Parse new data
            data = parse_json_cell(json_string)
            if not data:
                await interaction.followup.send("❌ Refresh failed: Invalid JSON", ephemeral=True)
                return
            
            new_embeds_spec = parse_embed_data(data)
            
            if not new_embeds_spec:
                embed = discord.Embed(title="No Data", description="Nothing to display", color=discord.Color.orange())
                await interaction.edit_original_response(embed=embed, view=None)
                return
            
            # Update data
            self.embeds_spec = new_embeds_spec
            self.total_pages = len(new_embeds_spec)
            
            # Adjust current page if needed
            if self.current_page >= self.total_pages:
                self.current_page = self.total_pages - 1
            
            # Format and update
            embed = create_discord_embed(self.embeds_spec[self.current_page])
            self.update_buttons()
            
            await interaction.edit_original_response(embed=embed, view=self)
            logger.info(f"Embed view refreshed ({self.total_pages} items)")
            
        except Exception as e:
            logger.error(f"Error refreshing embed view: {e}")
            await interaction.followup.send(f"❌ Refresh failed: {e}", ephemeral=True)


async def display_embeds(interaction, json_string=None, refresh_callback=None):
    """
    Display JSON data as interactive Discord embed tiles
    
    Args:
        interaction: Discord interaction object
        json_string: JSON string to display (optional if refresh_callback provided)
        refresh_callback: Optional async function that returns fresh JSON string
        
    The interaction should already be deferred before calling this function.
    
    If json_string is None but refresh_callback is provided, calls refresh_callback
    to fetch initial data.
    
    Returns:
        None
    """
    # If no json_string but has refresh_callback, fetch first
    if not json_string and refresh_callback:
        try:
            logger.info("Calling refresh_callback to fetch initial data...")
            json_string = await refresh_callback()
            logger.info(f"Refresh callback returned: {type(json_string)} with length {len(json_string) if json_string else 0}")
        except Exception as e:
            logger.error(f"Error fetching initial data: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch data:\n{e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
    
    if not json_string:
        logger.error("No JSON string provided and no refresh callback, or refresh callback returned None")
        embed = discord.Embed(
            title="Error",
            description="No data provided",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Parse JSON
    data = parse_json_cell(json_string)
    
    if not data:
        embed = discord.Embed(
            title="Error",
            description="Failed to parse JSON data",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Parse embed data
    embeds_spec = parse_embed_data(data)
    
    if not embeds_spec:
        embed = discord.Embed(
            title="No Data",
            description="Nothing to display",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Start at page 0
    current_page = 0
    total_pages = len(embeds_spec)
    
    # Create first embed
    embed = create_discord_embed(embeds_spec[current_page])
    
    # Create view with navigation buttons (including refresh if callback provided)
    view = EmbedNavigationView(embeds_spec, current_page, interaction.user.id, refresh_callback)
    
    # Send message and store reference in view for timeout handler
    message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = message
    
    logger.info(f"Displayed embeds (showing 1/{total_pages})")
