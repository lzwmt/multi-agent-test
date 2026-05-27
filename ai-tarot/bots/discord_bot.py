#!/usr/bin/env python3
"""
AI Tarot Discord Bot
A Discord bot that provides AI-powered tarot readings via a backend API.
"""

import os
import sys
import logging
import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_tarot_bot')

# Configuration from environment variables
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
TAROT_API_URL = os.environ.get('TAROT_API_URL', 'http://localhost:18899')

if not DISCORD_BOT_TOKEN:
    logger.error("DISCORD_BOT_TOKEN environment variable is not set!")
    sys.exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# HTTP client for API calls
http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the HTTP client for API calls."""
    global http_client
    if http_client is None or http_client.is_closed:
        http_client = httpx.AsyncClient(base_url=TAROT_API_URL, timeout=30.0)
    return http_client


class PersonaSelect(discord.ui.Select):
    """Select menu for choosing a tarot reader persona."""

    def __init__(self, personas: list, spread: str, question: str):
        options = [
            discord.SelectOption(
                label=persona.get('name', 'Unknown'),
                value=persona.get('id', str(i)),
                description=persona.get('description', 'A tarot reader persona')[:100]
            )
            for i, persona in enumerate(personas[:25])  # Discord limit: 25 options
        ]
        super().__init__(
            placeholder='选择一位塔罗师...',
            min_values=1,
            max_values=1,
            options=options
        )
        self.personas = personas
        self.spread = spread
        self.question = question

    async def callback(self, interaction: discord.Interaction):
        """Handle persona selection."""
        selected_id = self.values[0]
        selected_persona = next(
            (p for p in self.personas if str(p.get('id')) == selected_id),
            None
        )

        if not selected_persona:
            await interaction.response.send_message(
                '❌ 未找到选中的塔罗师',
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        try:
            client = await get_http_client()
            payload = {
                'spread': self.spread,
                'question': self.question,
                'persona_id': selected_persona.get('id')
            }

            response = await client.post('/api/divination/', json=payload)
            response.raise_for_status()
            result = response.json()

            embed = format_reading_result(result, selected_persona)
            await interaction.followup.send(embed=embed)

        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.status_code} - {e.response.text}")
            await interaction.followup.send(
                f'❌ API 错误: {e.response.status_code}',
                ephemeral=True
            )
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            await interaction.followup.send(
                '❌ 无法连接到塔罗服务，请稍后再试',
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await interaction.followup.send(
                '❌ 发生未知错误，请稍后再试',
                ephemeral=True
            )


class PersonaView(discord.ui.View):
    """View containing the persona selection dropdown."""

    def __init__(self, personas: list, spread: str, question: str, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.add_item(PersonaSelect(personas, spread, question))

    async def on_timeout(self):
        """Handle view timeout."""
        logger.info("Persona selection view timed out")


def format_reading_result(result: dict, persona: dict) -> discord.Embed:
    """
    Format the divination result as a Discord embed.

    Args:
        result: The API response containing the reading
        persona: The selected persona information

    Returns:
        A formatted Discord embed
    """
    # Extract data from result
    spread_name = result.get('spread_name', '塔罗牌阵')
    cards = result.get('cards', [])
    reading_text = result.get('reading', '无法获取解读')
    question = result.get('question', '')

    # Create embed
    embed = discord.Embed(
        title=f'🔮 {spread_name}',
        description=reading_text[:4096],  # Discord limit: 4096 chars
        color=discord.Color.purple()
    )

    # Add question field
    if question:
        embed.add_field(
            name='💭 你的问题',
            value=question[:1024],  # Discord field value limit
            inline=False
        )

    # Add persona info
    embed.add_field(
        name='🧙 塔罗师',
        value=persona.get('name', '神秘塔罗师'),
        inline=True
    )

    # Add card fields
    for i, card in enumerate(cards):
        card_name = card.get('name', f'Card {i+1}')
        orientation = card.get('orientation', 'upright')
        position = card.get('position', str(i + 1))

        # Format orientation in Chinese
        orientation_display = '正位' if orientation.lower() in ('upright', '正') else '逆位'
        emoji = '⬆️' if orientation.lower() in ('upright', '正') else '⬇️'

        embed.add_field(
            name=f'{emoji} {card_name}',
            value=f'位置: {position}\n朝向: {orientation_display}',
            inline=True
        )

    # Add footer with disclaimer
    embed.set_footer(
        text='⚠️ 塔罗牌解读仅供参考，请理性看待。命运掌握在自己手中。'
    )

    return embed


@bot.event
async def on_ready():
    """Called when the bot is ready and connected."""
    logger.info(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guild(s)')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')


@bot.tree.command(name='tarot', description='开始一次塔罗牌占卜')
@app_commands.describe(
    spread='牌阵类型 (默认: single)',
    question='你的问题 (必填)'
)
@app_commands.choices(spread=[
    app_commands.Choice(name='单牌 (Single)', value='single'),
    app_commands.Choice(name='三牌 (Three Card)', value='three_card'),
    app_commands.Choice(name='凯尔特十字 (Celtic Cross)', value='celtic_cross'),
    app_commands.Choice(name='关系牌阵 (Relationship)', value='relationship'),
])
async def tarot_command(
    interaction: discord.Interaction,
    question: str,
    spread: Optional[app_commands.Choice[str]] = None
):
    """
    Start a new tarot reading.

    Args:
        interaction: The Discord interaction
        question: The user's question for the reading
        spread: Optional spread type (defaults to 'single')
    """
    spread_value = spread.value if spread else 'single'

    await interaction.response.defer(ephemeral=False)

    try:
        # Fetch available personas
        client = await get_http_client()
        response = await client.get('/api/divination/personas')
        response.raise_for_status()
        data = response.json()

        # Handle both list and dict responses
        if isinstance(data, dict):
            personas = data.get('personas', data.get('data', []))
        elif isinstance(data, list):
            personas = data
        else:
            personas = []

        if not personas:
            await interaction.followup.send(
                '❌ 没有可用的塔罗师',
                ephemeral=True
            )
            return

        # Create persona selection view
        view = PersonaView(personas, spread_value, question)

        embed = discord.Embed(
            title='🔮 选择你的塔罗师',
            description=f'**你的问题:** {question}\n**牌阵:** {spread_value}\n\n请从下方选择一位塔罗师为你解读:',
            color=discord.Color.blue()
        )

        await interaction.followup.send(embed=embed, view=view)

    except httpx.HTTPStatusError as e:
        logger.error(f"API error fetching personas: {e.response.status_code}")
        await interaction.followup.send(
            '❌ 无法获取塔罗师列表，请稍后再试',
            ephemeral=True
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching personas: {e}")
        await interaction.followup.send(
            '❌ 无法连接到塔罗服务，请稍后再试',
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Unexpected error in tarot command: {e}", exc_info=True)
        await interaction.followup.send(
            '❌ 发生未知错误，请稍后再试',
            ephemeral=True
        )


@bot.tree.command(name='spreads', description='查看可用的牌阵类型')
async def spreads_command(interaction: discord.Interaction):
    """List all available tarot spreads."""
    await interaction.response.defer(ephemeral=True)

    try:
        client = await get_http_client()
        response = await client.get('/api/divination/spreads')
        response.raise_for_status()
        data = response.json()

        # Handle both list and dict responses
        if isinstance(data, dict):
            spreads = data.get('spreads', data.get('data', []))
        elif isinstance(data, list):
            spreads = data
        else:
            spreads = []

        embed = discord.Embed(
            title='📜 可用牌阵',
            description='以下是所有可用的塔罗牌阵:',
            color=discord.Color.green()
        )

        for spread in spreads:
            name = spread.get('name', 'Unknown')
            description = spread.get('description', 'No description')
            card_count = spread.get('card_count', '?')

            embed.add_field(
                name=name,
                value=f'{description}\n牌数: {card_count}',
                inline=False
            )

        if not spreads:
            embed.description = '暂无可用牌阵'

        await interaction.followup.send(embed=embed)

    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.status_code}")
        await interaction.followup.send(
            '❌ 无法获取牌阵列表',
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in spreads command: {e}", exc_info=True)
        await interaction.followup.send(
            '❌ 发生错误，请稍后再试',
            ephemeral=True
        )


@bot.tree.command(name='personas', description='查看可用的塔罗师')
async def personas_command(interaction: discord.Interaction):
    """List all available reader personas."""
    await interaction.response.defer(ephemeral=True)

    try:
        client = await get_http_client()
        response = await client.get('/api/divination/personas')
        response.raise_for_status()
        data = response.json()

        # Handle both list and dict responses
        if isinstance(data, dict):
            personas = data.get('personas', data.get('data', []))
        elif isinstance(data, list):
            personas = data
        else:
            personas = []

        embed = discord.Embed(
            title='🧙 可用塔罗师',
            description='以下是所有可用的塔罗解读师:',
            color=discord.Color.orange()
        )

        for persona in personas:
            name = persona.get('name', 'Unknown')
            description = persona.get('description', 'A mysterious tarot reader')
            style = persona.get('style', 'Mystical')

            embed.add_field(
                name=name,
                value=f'{description}\n风格: {style}',
                inline=False
            )

        if not personas:
            embed.description = '暂无可用塔罗师'

        await interaction.followup.send(embed=embed)

    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.status_code}")
        await interaction.followup.send(
            '❌ 无法获取塔罗师列表',
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in personas command: {e}", exc_info=True)
        await interaction.followup.send(
            '❌ 发生错误，请稍后再试',
            ephemeral=True
        )


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Handle command errors."""
    logger.error(f"Command error: {error}", exc_info=True)

    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands

    await ctx.send(f'❌ 命令执行出错: {str(error)}')


async def cleanup():
    """Cleanup resources on bot shutdown."""
    global http_client
    if http_client and not http_client.is_closed:
        await http_client.aclose()
        logger.info("HTTP client closed")


def main():
    """Main entry point for the bot."""
    logger.info("Starting AI Tarot Discord Bot...")
    logger.info(f"API URL: {TAROT_API_URL}")

    try:
        bot.run(DISCORD_BOT_TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Run cleanup
        loop = asyncio.new_event_loop()
        loop.run_until_complete(cleanup())
        loop.close()


if __name__ == '__main__':
    main()
