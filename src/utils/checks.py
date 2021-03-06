from discord.ext import commands
import discord.utils
from utils import config


# Check for Role
def check_role(ctx, check):
    msg = ctx.message
    ch = msg.channel
    author = msg.author

    if ch.is_private:
        return False

    role = discord.utils.find(check, author.roles)
    return role is not None


# Check for Staff
def is_staff():
    def predicate(ctx):
        return check_role(ctx, lambda r: r.id in (config.ROLE_ID_ADMIN, config.ROLE_ID_MOD))

    return commands.check(predicate)


# Check for Admins
def is_admin():
    def predicate(ctx):
        return check_role(ctx, lambda r: r.id == config.ROLE_ID_ADMIN)

    return commands.check(predicate)


# Check for Moderators
def is_mod():
    def predicate(ctx):
        return check_role(ctx, lambda r: r.id == config.ROLE_ID_MOD)

    return commands.check(predicate)


# Check for Comrade/Member
def is_member():
    def predicate(ctx):
        return check_role(ctx, lambda r: r.id == config.ROLE_ID_MEMBER)

    return commands.check(predicate)


# Check for User Allowed to Use Events
def can_use_events():
    def predicate(ctx):
        return not check_role(ctx, lambda r: r.id == config.ROLE_ID_NO_EVENTS)

    return commands.check(predicate)
