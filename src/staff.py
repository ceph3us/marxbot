import discord
from discord.ext import commands
from utils import checks
from utils import config
from clipboard import clip_message
import datetime
from datetime import datetime
import csv


class Staff:
    def __init__(self, bot):
        self.bot = bot

    # ********************************************** #
    # STAFF-ONLY BOT COMMANDS ********************** #
    # ********************************************** #

    # Load Extension

    @commands.command()
    @checks.is_admin()
    async def load(self, extension_name: str):
        """Loads an extension."""

        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as ex:
            await self.bot.say("```py\n{}: {}\n```".format(type(ex).__name__, str(ex)))
            return
        await self.bot.say("{} loaded.".format(extension_name))

    # Unload Extension
    @commands.command()
    @checks.is_admin()
    async def unload(self, extension_name: str):
        """Unloads an extension."""

        self.bot.unload_extension(extension_name)
        await self.bot.say("{} unloaded.".format(extension_name))

    # COMMAND: !setplaying
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def setplaying(self, ctx, *, game_name: str):
        """Sets Karl's currently playing game."""

        await self.bot.change_presence(game=discord.Game(name=game_name))
        await self.bot.delete_message(ctx.message)
        await self.bot.say("I just started playing **{0}**! You should try it!".format(game_name))

    # COMMAND: !comrade
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def comrade(self, ctx, user: discord.Member):
        """Promotes a Psyop to a Comrade granting full server access."""

        # User to make Comrade
        # user = discord.utils.get(ctx.message.server.members, name=username)
        role_probie = discord.utils.get(ctx.message.server.roles, name="Psyops")
        role_comrade = discord.utils.get(ctx.message.server.roles, name="Comrades")

        new_roles = [role_comrade if x == role_probie else x for x in user.roles]

        # Get Channels
        channel_general = self.bot.get_channel(config.CHANNEL_ID_GENERAL)
        channel_info = self.bot.get_channel(config.CHANNEL_ID_INFO)
        channel_bot = self.bot.get_channel(config.CHANNEL_ID_BOT)

        # Check for Empty User
        if not user:
            await self.bot.say("**Error**: Missing required <user>.")
            return

        # Check For Already Comrade
        if role_comrade in user.roles:
            await self.bot.say("**ERROR**: User is already a comrade!")
            return

        # Try switching the roles
        try:
            await self.bot.replace_roles(user, *new_roles)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel,
                                        "{0.mention}, there was an error changing user's role. "
                                        "".format(ctx.message.author) + str(e))
            return

        # Set username
        username = user.nick if (user.nick is not None) else user.name

        # Approval message in Lobby
        await self.bot.say('**{1}** has successfully been made a **Comrade**!'.format(ctx.message.author, username))

        # Welcome Message in General
        await self.bot.send_message(channel_general, "Welcome our newest comrade, {0.mention}! Be sure to take a "
                                                     "look at {1.mention} for more, including a list of roles (pronouns"
                                                     ", colors, opt-in channels, etc) that you can join in {2.mention}."
                                                     " And feel free to DM a staffer if you need help or have any "
                                                     "questions.".format(user, channel_info, channel_bot))

        # Secondary Welcome DM to User
        wmsg = "Congratulations {0.mention}! You're now officially a comrade! Now that you have access to the main " \
               "server check out the {1.mention} channel for details on the different **roles** you can join. Some " \
               "are for pronouns, some give you access to private channels for recognized groups or private " \
               "interests, and some just give you a cool name color! When you're ready, head on over to the " \
               "{2.mention} channel and use `!join` or `!iam` to join your roles! \n\n If you have any questions, " \
               "feel free to ask a staff member. Thanks again, and welcome to LeftDisc!" \
               "".format(user, channel_info, channel_bot)

        # Send Private Welcome Message
        await self.bot.send_message(user, wmsg)

    # COMMAND: !psyops
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def psyops(self, ctx, page: int = 1):
        """Lists the current Psyops/probationary users and their Join Date. 20 users per page."""

        # Get Variables
        server = ctx.message.server
        server_icon = str(server.icon_url)
        all_members = server.members
        role_probie = discord.utils.get(server.roles, name="Psyops")

        psyops_members_unsorted = [member for member in all_members if role_probie in member.roles]
        psyops_members = sorted(psyops_members_unsorted, key=lambda member: member.joined_at)

        start_index = (page - 1) * 20

        psyops_list = ""
        i = 1 + start_index

        if ((page - 1) * 20) >= len(psyops_members):
            await self.bot.say("**ERROR**: Page does not exist.")
            return

        for member in psyops_members[start_index:]:
            psyops_list += ("**" + str(i) + "**. {0.mention} - ".format(member) +
                            member.joined_at.strftime('%Y-%m-%d') + "\n")
            i += 1

            # Check for Break
            if i == (start_index + 21):
                break

        # Create Embed Table
        embed = discord.Embed(title="Current Psyops Users: " + str(len(psyops_members)), colour=1315860,
                              description="Current probationary users and join dates.")
        embed.set_thumbnail(url=server_icon)
        embed.set_footer(text="Page {0}.     Staff User and Viewing Only!".format(str(page)))
        embed.add_field(name="Users", value=psyops_list, inline=False)

        await self.bot.say(embed=embed)

    # COMMAND !cleanup
    @commands.command(pass_context=True)
    @checks.is_admin()
    async def cleanup(self, ctx, certain: str = "n"):
        """Clears members in the Psyops group who have been in the server for more than 24 hours."""

        # Get Variables
        server = ctx.message.server
        all_members = server.members
        role_probie = discord.utils.get(server.roles, id=config.ROLE_ID_DEFAULT)
        psyops_members = [member for member in all_members if role_probie in member.roles]
        now = datetime.utcnow()

        total = 0

        for member in psyops_members:

            # Check Date Difference
            date_diff = now - member.joined_at
            days, seconds = date_diff.days, date_diff.seconds
            hours = (days * 24) + (seconds // 3600)

            if hours >= 24:
                if certain == "y":
                    await self.bot.kick(member)
                total += 1

        if certain == "n":
            await self.bot.say("**Total to be Purged**: " + str(total))
            return

        await self.bot.say("**Total Purged Users**: " + str(total))

    # COMMAND !setcounting
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def setcounting(self, ctx, newcount: int):
        """For correcting counting. Sets current count and updates counting."""
        
        config.CURRENT_COUNT = newcount
        
        updated = config.update_counting()
        
        if updated:
            await self.bot.say("Current count set and stats updated.")
        else:
            await self.bot.say("**ERROR**: There was an error setting the count and updating the stats.")

        await self.bot.delete_message(ctx.message)

    # COMMAND !updatecounting
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def updatecounting(self, ctx):
        """Force updates counting."""

        updated = config.update_counting()

        if updated:
            await self.bot.say("Counting stats have been updated.")
        else:
            await self.bot.say("**ERROR**: Counting stats could not be updated.")

        await self.bot.delete_message(ctx.message)

    # COMMAND !clip
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def clip(self, ctx, channel: discord.Channel, message_id: str):
        """Manually clip and item when clipping fails for some reason."""
        
        # The message
        msg = await self.bot.get_message(channel, message_id)

        await clip_message(msg, self.bot)
        await self.bot.delete_message(ctx.message)

    # COMMAND !say
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def say(self, ctx, channel: discord.Channel, *, message_string: str):
        """Have Marxbot say a message in a specific channel."""

        # Say the Message
        await self.bot.send_message(channel, message_string)

        # Delete the Command
        await self.bot.delete_message(ctx.message)

    # COMMAND !addrole
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def addrole(self, ctx, role_type: str, *, role_name: str):
        """Add a role to the roles users can join via the !join command."""

        # Allowed Types
        allowed_types = ["region", "pronoun", "game", "color", "private", "interest"]

        # Check for Allowed Role Types
        if role_type not in allowed_types:
            await self.bot.say("**ERROR**: The role type must be one of the allowed types: <region, pronoun, game, "
                               "color, private, interest>")
            return

        # Server
        server = ctx.message.server

        # The Role
        role = discord.utils.get(server.roles, name=role_name)

        # Make Sure the Role is Valid
        if role is None:
            await self.bot.say("**ERROR**: There is no role with that name on the server. You must type the role name "
                               "exactly as it appears in the role list.")
            return

        # Add the Role to the List
        added = config.add_joinable_role(role.id, role_name, role_type)

        # Return Success/Failure Message
        if added:
            await self.bot.say("The role has been added to the list.")
        else:
            await self.bot.say("**ERROR**: The role could not be added.")

    # COMMAND !removerole
    @commands.command()
    @checks.is_staff()
    async def removerole(self, *, role_name: str):
        """Add a role to the roles users can join via the !join command."""

        # Remove Role from List
        removed = config.remove_joinable_role(role_name)

        # Return Success/Failure Message
        if removed:
            await self.bot.say("The role has been removed from the list.")
        else:
            await self.bot.say("**ERROR**: The role could not be removed.")

    # COMMAND !cleanevents
    @commands.command()
    @checks.is_staff()
    async def cleanevents(self):
        """Allows staff to clean up events. Purges all roles older than 2 weeks, and deleted old events from the calendar."""

        # Clean Up Events
        cleanup = config.clean_events()

        # Return Success/Failure Message
        if cleanup:
            await self.bot.say("Event roles and calendar entries have been cleaned.")
        else:
            await self.bot.say("**ERROR**: Events are still messy; I couldn't clean them up.")

    # COMAND !chanstats
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def chanstats(self, ctx, start_date: str = None, end_date: str = None, channel: discord.Channel = None):
        """Creates a stats list per-channel of message count or unique users for a given time frame or, if provided a specific channel, lists stats for that channel. BE AWARE THIS SENDS MANY MESSAGES AND CAN TAKE QUITE AWHILE! BE PATIENT!"""

        # Check for Valid Start Date and Set
        try:
            start_datetime = datetime.strptime(start_date + ' 00:00', '%Y-%m-%d %H:%M')
        except ValueError:
            await self.bot.say("**ERROR**: Start date must be valid and in YYYY-MM-DD format.")
            return

        # Check for Valid End Date and Set
        try:
            end_datetime = datetime.strptime(end_date + ' 23:59', '%Y-%m-%d %H:%M')
        except ValueError:
            await self.bot.say("**ERROR**: End date must be valid and in YYYY-MM-DD format.")
            return

        # Handle Single Channel
        if channel is not None:

            # Setup Users and Messages
            unique_users = []
            total_messages = 0

            async for m in self.bot.logs_from(channel, limit=100000, before=end_datetime, after=start_datetime):

                # Unique Users
                if m.author.id not in unique_users:
                    unique_users.append(m.author.id)

                # Total Messages
                total_messages += 1

            # Get Total users
            total_users = len(unique_users)

            # Print Stats
            await self.bot.say(channel.mention + ": " + str(total_messages) + " messages, " + str(total_users) + " users")

            # Exit Command
            return

        # Server
        server = ctx.message.server

        # Get the Channels Minus Ignored Channels
        channels = [channel for channel in server.channels if channel.id not in config.NO_STATS_CHANNELS and channel.type == discord.ChannelType.text]

        # Sort the Channels
        channels.sort(key=lambda x: x.position, reverse=False)

        # Start Channel Mentions and Stats
        await self.bot.say("__**CHANNEL STATS FROM " + start_date + " TO " + end_date + " **__" + "\n" +
                           "Please do not interrupt until I say all stats have been printed!")

        for c in channels:

            # Setup Users and Messages
            unique_users = []
            total_messages = 0

            # Get Messages
            async for m in self.bot.logs_from(c, limit=100000, before=end_datetime, after=start_datetime):

                # Unique Users
                if m.author.id not in unique_users:
                    unique_users.append(m.author.id)

                # Total Messages
                total_messages += 1

            # Get Total users
            total_users = len(unique_users)

            # Print Stats
            await self.bot.say(c.mention + ": " + str(total_messages) + " messages, " + str(total_users) + " users")

        # Send Complete Message
        await self.bot.say("__**STATS COMPLETE**__")

    # COMAND !chanstatcsv
    @commands.command(pass_context=True)
    @checks.is_staff()
    async def chanstatcsv(self, ctx, start_date: str = None, end_date: str = None):
        """Creates a CSV file containing channel stats for a given timeframe."""

        # Check for Valid Start Date and Set
        try:
            start_datetime = datetime.strptime(start_date + ' 00:00', '%Y-%m-%d %H:%M')
        except:
            await self.bot.say("**ERROR**: Start date must be valid and in YYYY-MM-DD format.")
            return

        # Check for Valid End Date and Set
        try:
            end_datetime = datetime.strptime(end_date + ' 23:59', '%Y-%m-%d %H:%M')
        except:
            await self.bot.say("**ERROR**: End date must be valid and in YYYY-MM-DD format.")
            return

        # Server
        server = ctx.message.server

        # Get the Channels Minus Ignored Channels
        channels = [channel for channel in server.channels if channel.id not in config.NO_STATS_CHANNELS and channel.type == discord.ChannelType.text]

        # Sort the Channels
        channels.sort(key=lambda x: x.position, reverse=False)
        
        # Open the CSV file
        with open('channel_stats/stats_' + start_date + '_to_' + end_date + '.csv', mode='w') as stats_file:
        
            # Set the Writer
            stat_writer = csv.writer(stats_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Send Starting Message
            await self.bot.say("Starting channel stats...")

            # Loop Through Channels
            for c in channels:

                # Setup Users and Messages
                unique_users = []
                total_messages = 0

                # Get Messages
                async for m in self.bot.logs_from(c, limit=100000, before=end_datetime, after=start_datetime):

                    # Unique Users
                    if m.author.id not in unique_users:
                        unique_users.append(m.author.id)

                    # Total Messages
                    total_messages += 1

                # Get Total users
                total_users = len(unique_users)

                # Print Stats to CSV [channel name, messages, users]
                stat_writer.writerow(['#' + c.name, str(total_messages), str(total_users)])

        # Send Complete Message
        await self.bot.say("...Stats complete and saved to CSV.")


def setup(bot):
    bot.add_cog(Staff(bot))
