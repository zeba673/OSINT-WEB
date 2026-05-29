import httpx
from modules.accounts_config import get_platform_accounts

async def scrape_discord(target: str, search_type: str = 'user') -> dict:
    result = {
        'target': target,
        'search_type': search_type,
        'authenticated': False,
        'user_info': None,
        'mutual_guilds': [],
        'friends': [],
        'messages': [],
        'error': None,
    }

    accounts = get_platform_accounts('discord')
    token = None
    if accounts and accounts.get('enabled'):
        token = accounts.get('user_token')
        result['authenticated'] = bool(token)

    if not token:
        result['error'] = 'No Discord user token configured'
        return result

    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
    }

    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        try:
            if search_type == 'user':
                resp = await client.get(f'https://discord.com/api/v9/users/{target}')
                if resp.status_code == 200:
                    data = resp.json()
                    result['user_info'] = {
                        'id': data.get('id'),
                        'username': data.get('username'),
                        'discriminator': data.get('discriminator'),
                        'global_name': data.get('global_name'),
                        'avatar_url': f"https://cdn.discordapp.com/avatars/{data.get('id')}/{data.get('avatar')}.png" if data.get('avatar') else None,
                        'banner_url': f"https://cdn.discordapp.com/banners/{data.get('id')}/{data.get('banner')}.png" if data.get('banner') else None,
                        'accent_color': data.get('accent_color'),
                        'verified': data.get('verified', False),
                        'bot': data.get('bot', False),
                        'premium_type': data.get('premium_type', 0),
                        'public_flags': data.get('public_flags', 0),
                        'flags': data.get('flags', 0),
                    }
                elif resp.status_code == 404:
                    result['error'] = 'User not found'
                else:
                    result['error'] = f'API error: {resp.status_code}'

            resp = await client.get('https://discord.com/api/v9/users/@me/guilds')
            if resp.status_code == 200:
                guilds = resp.json()
                result['mutual_guilds'] = [
                    {
                        'id': g.get('id'),
                        'name': g.get('name'),
                        'icon_url': f"https://cdn.discordapp.com/icons/{g.get('id')}/{g.get('icon')}.png" if g.get('icon') else None,
                        'owner': g.get('owner', False),
                        'permissions': g.get('permissions'),
                        'approximate_member_count': g.get('approximate_member_count', 0),
                        'approximate_presence_count': g.get('approximate_presence_count', 0),
                    }
                    for g in guilds[:30]
                ]

            resp = await client.get('https://discord.com/api/v9/users/@me/relationships')
            if resp.status_code == 200:
                relationships = resp.json()
                result['friends'] = [
                    {
                        'id': r.get('id'),
                        'username': r.get('user', {}).get('username'),
                        'global_name': r.get('user', {}).get('global_name'),
                        'type': r.get('type'),
                        'avatar_url': f"https://cdn.discordapp.com/avatars/{r.get('id')}/{r.get('user', {}).get('avatar')}.png" if r.get('user', {}).get('avatar') else None,
                    }
                    for r in relationships[:30]
                ]

        except httpx.HTTPStatusError as e:
            result['error'] = f'HTTP {e.response.status_code}: {e.response.text[:200]}'
        except Exception as e:
            result['error'] = str(e)[:300]

    return result
