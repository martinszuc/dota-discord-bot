import discord
import asyncio
import time
from discord.ext import commands, tasks
from typing import Dict, Any, Optional

from src.utils.config import logger, PREFIX
from src.webapp.backend.gsi_endpoint import gsi_manager
from src.gsi.gsi_state import gsi_state
from src.bot import start_game, stop_game, rosh_timer_command, glyph_timer_command


class GSICog(commands.Cog):
    """
    Discord commands and functionality related to Game State Integration.

    This cog provides commands to interact with Dota 2 GSI data and
    automatically sync game state with the bot's timer functionality.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize the GSI cog.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        self.active_games = {}  # Currently tracked games by guild ID

        # Start the background task for syncing
        self.gsi_sync_task.start()
        logger.info("GSI Cog initialized")

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.gsi_sync_task.cancel()

    @commands.command(name="gsi-status")
    async def gsi_status(self, ctx: commands.Context):
        """
        Check the current status of the GSI connection.

        Shows whether Dota 2 is connected and sending game state data.
        """
        last_update = gsi_manager.get_last_update_time()
        in_game = gsi_manager.is_in_game()

        # Calculate how long since the last update
        last_update_seconds_ago = time.time() - last_update if last_update > 0 else None
        connected = last_update > 0 and last_update_seconds_ago < 60 if last_update_seconds_ago is not None else False

        # Create an embed with the GSI status
        embed = discord.Embed(
            title="Dota 2 GSI Status",
            color=discord.Color.green() if connected else discord.Color.red()
        )

        embed.add_field(
            name="Connection Status",
            value="✅ Connected" if connected else "❌ Disconnected",
            inline=False
        )

        if connected:
            embed.add_field(
                name="Last Update",
                value=f"{int(last_update_seconds_ago)} seconds ago" if last_update_seconds_ago is not None else "Never",
                inline=True
            )

            embed.add_field(
                name="In Game",
                value="✅ Yes" if in_game else "❌ No",
                inline=True
            )

            if in_game:
                game_mode = gsi_manager.get_game_mode()
                match_id = gsi_manager.get_match_id()
                game_time = gsi_manager.get_game_time()
                player_team = gsi_manager.get_player_team()

                if game_mode:
                    embed.add_field(
                        name="Game Mode",
                        value=game_mode.replace("_", " ").title(),
                        inline=True
                    )

                if match_id:
                    embed.add_field(
                        name="Match ID",
                        value=match_id,
                        inline=True
                    )

                if game_time is not None:
                    minutes = int(game_time) // 60
                    seconds = int(game_time) % 60
                    embed.add_field(
                        name="Game Time",
                        value=f"{minutes:02}:{seconds:02}",
                        inline=True
                    )

                if player_team:
                    embed.add_field(
                        name="Your Team",
                        value=player_team.title(),
                        inline=True
                    )

                # Add Roshan info
                roshan_state = gsi_manager.get_roshan_state()
                if not roshan_state["alive"] and roshan_state["death_time"] is not None:
                    embed.add_field(
                        name="Roshan",
                        value="Dead",
                        inline=True
                    )

                    game_time = gsi_manager.get_game_time() or 0
                    min_remaining = max(0, int((roshan_state["min_respawn_time"] - game_time) // 60))
                    max_remaining = max(0, int((roshan_state["max_respawn_time"] - game_time) // 60))

                    embed.add_field(
                        name="Respawn Window",
                        value=f"{min_remaining}-{max_remaining} minutes",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="Roshan",
                        value="Alive",
                        inline=True
                    )

                # Add Glyph info
                glyph_status = gsi_manager.are_glyph_available()
                embed.add_field(
                    name="Glyphs",
                    value=(
                        f"Radiant: {'✅' if glyph_status['radiant'] else '❌'}\n"
                        f"Dire: {'✅' if glyph_status['dire'] else '❌'}"
                    ),
                    inline=True
                )

        # Add sync status for this guild
        is_synced = ctx.guild.id in gsi_state.synced_guilds
        embed.add_field(
            name="Auto-Sync",
            value="✅ Enabled" if is_synced else "❌ Disabled",
            inline=False
        )

        # Footer with help command
        embed.set_footer(text=f"Use {PREFIX}gsi-sync to enable/disable auto-sync")

        await ctx.send(embed=embed)

    @commands.command(name="gsi-sync")
    async def gsi_sync(self, ctx: commands.Context):
        """
        Toggle automatic synchronization with Dota 2 GSI.

        When enabled, the bot will automatically start and stop timers
        based on your current game state.
        """
        guild_id = ctx.guild.id

        # Toggle sync for this guild
        is_enabled = gsi_state.toggle_guild_sync(guild_id)

        if is_enabled:
            # Add channel info to the state
            if hasattr(ctx, 'channel') and ctx.channel:
                # We'll store this in the active_games dict since it's specific to this cog
                self.active_games[guild_id] = {
                    'channel_id': ctx.channel.id,
                    'last_sync': 0
                }
            await ctx.send(
                "✅ Auto-sync with Dota 2 has been **enabled**. The bot will now automatically start and stop timers based on your game state.")
            logger.info(f"GSI auto-sync enabled for guild {guild_id}")
        else:
            # Clean up any stored info
            if guild_id in self.active_games:
                del self.active_games[guild_id]
            await ctx.send("✅ Auto-sync with Dota 2 has been **disabled**.")
            logger.info(f"GSI auto-sync disabled for guild {guild_id}")

    @tasks.loop(seconds=10)
    async def gsi_sync_task(self):
        """Background task that syncs GSI data with the bot's timers."""
        try:
            # Skip if there are no synced guilds
            if not gsi_state.synced_guilds:
                return

            # Check if we're in a game
            in_game = gsi_manager.is_in_game()
            game_mode = gsi_manager.get_game_mode() if in_game else None
            match_id = gsi_manager.get_match_id() if in_game else None

            # Process each synced guild
            for guild_id in list(gsi_state.synced_guilds):
                try:
                    # Skip if we don't have channel info for this guild
                    if guild_id not in self.active_games:
                        continue

                    guild_data = self.active_games[guild_id]

                    # Skip if we've synced recently (within 30 seconds)
                    if time.time() - guild_data.get('last_sync', 0) < 30:
                        continue

                    # Get the guild and channel
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        # Guild no longer exists or bot isn't in it
                        logger.warning(f"Could not find guild {guild_id}, removing from synced guilds")
                        gsi_state.synced_guilds.discard(guild_id)
                        if guild_id in self.active_games:
                            del self.active_games[guild_id]
                        continue

                    channel = guild.get_channel(guild_data['channel_id'])
                    if not channel:
                        # Channel no longer exists
                        logger.warning(f"Could not find channel {guild_data['channel_id']} in guild {guild_id}")
                        continue

                    # Create a context object for commands
                    ctx = await self.bot.get_context(await channel.fetch_message(channel.last_message_id))

                    # Check if we need to start a new game timer
                    if in_game and match_id and match_id != guild_data.get('current_match_id'):
                        # New game detected
                        logger.info(f"New game detected for guild {guild_id}: mode={game_mode}, match_id={match_id}")

                        # Stop any existing timer
                        if guild_id in self.active_games and 'current_match_id' in guild_data:
                            await stop_game(ctx)

                        # Start a new timer
                        mode_str = "turbo" if game_mode == "turbo" else "regular"
                        game_time = gsi_manager.get_game_time() or 0

                        if game_time <= 0:
                            # Game is just starting, use positive countdown
                            await start_game(ctx, "30", mode_str)
                        else:
                            # Game is already in progress, use negative time
                            formatted_time = f"-{int(game_time)}"
                            await start_game(ctx, formatted_time, mode_str)

                        # Update guild data
                        guild_data['current_match_id'] = match_id
                        guild_data['last_sync'] = time.time()

                        await channel.send(f"✅ Automatically started {mode_str} game timer based on GSI data.")

                    # Check if we need to stop the timer because game ended
                    elif not in_game and guild_data.get('current_match_id'):
                        # Game ended
                        logger.info(f"Game ended for guild {guild_id}")

                        # Stop the timer
                        await stop_game(ctx)

                        # Update guild data
                        guild_data['current_match_id'] = None
                        guild_data['last_sync'] = time.time()

                        await channel.send("✅ Automatically stopped game timer as your game has ended.")

                    # Check if we need to sync Roshan/Glyph timers during the game
                    elif in_game and guild_data.get('current_match_id'):
                        # Currently in a game with an active timer
                        needs_sync = False
                        sync_message = ""

                        # Check Roshan
                        roshan_state = gsi_manager.get_roshan_state()
                        if not roshan_state["alive"] and not guild_data.get('roshan_synced'):
                            # Roshan is dead and we haven't synced yet
                            await rosh_timer_command(ctx)
                            guild_data['roshan_synced'] = True
                            guild_data['last_sync'] = time.time()
                            needs_sync = True
                            sync_message += "• Synchronized Roshan timer with GSI data.\n"
                        elif roshan_state["alive"] and guild_data.get('roshan_synced'):
                            # Roshan is alive again
                            guild_data['roshan_synced'] = False

                        # Check Enemy Glyph
                        player_team = gsi_manager.get_player_team()
                        glyph_status = gsi_manager.are_glyph_available()

                        if player_team and not glyph_status[player_team]:
                            # Our team's glyph is on cooldown
                            pass  # We don't track our own glyph, only enemy glyph

                        enemy_team = "dire" if player_team == "radiant" else "radiant"
                        if not glyph_status.get(enemy_team, True) and not guild_data.get('enemy_glyph_synced'):
                            # Enemy glyph is on cooldown and we haven't synced yet
                            await glyph_timer_command(ctx)
                            guild_data['enemy_glyph_synced'] = True
                            guild_data['last_sync'] = time.time()
                            needs_sync = True
                            sync_message += "• Synchronized enemy glyph timer with GSI data.\n"
                        elif glyph_status.get(enemy_team, True) and guild_data.get('enemy_glyph_synced'):
                            # Enemy glyph is available again
                            guild_data['enemy_glyph_synced'] = False

                        if needs_sync:
                            await channel.send(f"✅ GSI Sync:\n{sync_message}")

                except Exception as e:
                    logger.error(f"Error processing guild {guild_id} in GSI sync task: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in GSI sync task: {e}", exc_info=True)

    @gsi_sync_task.before_loop
    async def before_gsi_sync_task(self):
        """Wait for the bot to be ready before starting the sync task."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Set up the GSI cog.

    Args:
        bot (commands.Bot): The Discord bot instance.
    """
    await bot.add_cog(GSICog(bot))