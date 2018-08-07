import settings


# When Someone Reacts with a Pushpin Emote
async def on_pin(reaction, bot):

    # Define Allowed Channels
    channels = []
    for channel_id in settings.ALLOWED_PIN_CHANNELS:
        channels.append(bot.get_channel(channel_id))

    current_pinned = await bot.pins_from(reaction.message.channel)
    if len(current_pinned) < 50:
        await bot.pin_message(reaction.message)
    else:
        await bot.send_message(reaction.message.channel, "I cannot pin the message. We have reached the maximum number "
                                                         "of pins comrades!")