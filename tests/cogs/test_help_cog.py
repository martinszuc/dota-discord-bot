from unittest.mock import AsyncMock, Mock, patch

import pytest
from discord.ext import commands

from src.cogs.help_cog import HelpCog


@pytest.fixture
def bot():
    """Create a mock bot instance."""
    return Mock(spec=commands.Bot)


@pytest.fixture
def cog(bot):
    """Instantiate the HelpCog with a mock bot."""
    return HelpCog(bot)


@pytest.fixture
def ctx():
    """Create a mock context."""
    mock_ctx = Mock()
    mock_ctx.send = AsyncMock()
    mock_ctx.guild = Mock()
    mock_ctx.guild.name = "TestGuild"
    mock_ctx.author = Mock()
    mock_ctx.author.name = "TestUser"
    return mock_ctx


@pytest.mark.asyncio
async def test_send_help(cog, ctx):
    """Test that the help command sends the correct embed."""
    with patch('discord.Embed') as MockEmbed:
        mock_embed_instance = Mock()
        MockEmbed.return_value = mock_embed_instance

        # Invoke the command directly
        await cog.send_help.callback(cog, ctx)

        # Check that Embed was instantiated correctly with description
        MockEmbed.assert_called_once_with(
            title="Dota Timer Bot - Help",
            color=0x00ff00,
            description='List of available commands and their descriptions.'
        )

        # Check that the embed was sent with embed=mock_embed_instance
        ctx.send.assert_awaited_once_with(embed=mock_embed_instance)
