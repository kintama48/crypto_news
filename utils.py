import discord


def news_helper(news):
    embed = discord.Embed(
        title=news['title'],
        description=news['body'],
        color=0xD5059D
    )
    embed.set_thumbnail(url=news['imageurl'])
    embed.set_footer(text=f"[Click here to visit the article site.]({news['guid']})")
    return embed


def create_telegram_msg(news):
    text = f"\*{news['title']}\*" \
           f"\n\n\_{news['body']}\_" \
           f"\n\n\*Source:\* [Click here to visit the article site.]({news['guid']})"
    return text



