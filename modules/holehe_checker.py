import httpx
import asyncio

SITES_TO_CHECK = [
    {'name': 'Twitter/X', 'url': 'https://twitter.com/users/email_available', 'method': 'POST', 'field': 'email'},
    {'name': 'Instagram', 'url': 'https://www.instagram.com/api/v1/web/accounts/check_email/', 'method': 'POST', 'field': 'email'},
    {'name': 'Facebook', 'url': 'https://www.facebook.com/api/graphql/', 'method': 'POST', 'field': 'email'},
    {'name': 'Spotify', 'url': 'https://www.spotify.com/api/signup/checkEmail', 'method': 'POST', 'field': 'email'},
    {'name': 'Pinterest', 'url': 'https://www.pinterest.com/resource/EmailExistsResource/get/', 'method': 'GET', 'field': 'email'},
    {'name': 'TikTok', 'url': 'https://www.tiktok.com/api/v1/check/email/', 'method': 'POST', 'field': 'email'},
    {'name': 'Tumblr', 'url': 'https://www.tumblr.com/svc/account/register/email_available', 'method': 'POST', 'field': 'email'},
    {'name': 'Adobe', 'url': 'https://auth.services.adobe.com/signup/v2/users/email', 'method': 'POST', 'field': 'email'},
    {'name': 'Amazon', 'url': 'https://www.amazon.com/ap/register/email', 'method': 'POST', 'field': 'email'},
    {'name': 'Apple', 'url': 'https://idmsa.apple.com/appleauth/auth/v2/authorize', 'method': 'POST', 'field': 'accountName'},
    {'name': 'WordPress', 'url': 'https://public-api.wordpress.com/rest/v1.1/users/email/exists', 'method': 'GET', 'field': 'email'},
    {'name': 'LinkedIn', 'url': 'https://www.linkedin.com/checkemail', 'method': 'POST', 'field': 'email'},
    {'name': 'Snapchat', 'url': 'https://accounts.snapchat.com/accounts/get_username_by_email', 'method': 'POST', 'field': 'email'},
    {'name': 'Telegram', 'url': 'https://oauth.telegram.org/auth/check_email', 'method': 'POST', 'field': 'email'},
    {'name': 'Patreon', 'url': 'https://www.patreon.com/api/auth/check_email', 'method': 'POST', 'field': 'email'},
    {'name': 'Medium', 'url': 'https://medium.com/_/api/users/email/available', 'method': 'POST', 'field': 'email'},
    {'name': 'GitHub', 'url': 'https://github.com/signup_check/email', 'method': 'POST', 'field': 'value'},
    {'name': 'Bitbucket', 'url': 'https://bitbucket.org/account/signup/check_email/', 'method': 'POST', 'field': 'email'},
    {'name': 'GitLab', 'url': 'https://gitlab.com/users/email_exists', 'method': 'POST', 'field': 'email'},
    {'name': 'Twitch', 'url': 'https://passport.twitch.tv/usernames/check', 'method': 'POST', 'field': 'email'},
    {'name': 'VK', 'url': 'https://api.vk.com/method/account.checkEmail', 'method': 'POST', 'field': 'email'},
]

async def check_holehe(email: str) -> dict:
    result = {
        'email': email,
        'registrations': [],
        'total_registered': 0,
        'total_checked': 0,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Origin': 'https://www.google.com',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10) as client:
        for site in SITES_TO_CHECK[:20]:
            result['total_checked'] += 1
            try:
                if site['method'] == 'POST':
                    resp = await client.post(site['url'], data={site['field']: email})
                else:
                    resp = await client.get(site['url'], params={site['field']: email})

                status = 'unknown'
                text = resp.text.lower()

                if resp.status_code in (200, 201, 202):
                    if any(flag in text for flag in ['already taken', 'already used', 'exists', 'found', 'registered', '"taken"', 'true', 'is_registered']):
                        status = 'registered'
                    elif any(flag in text for flag in ['available', 'not found', 'false', 'not registered', '"available"']):
                        status = 'available'
                    else:
                        if len(resp.text) < 50:
                            status = 'registered'
                        else:
                            status = 'unknown'
                elif resp.status_code == 400:
                    status = 'registered'
                elif resp.status_code == 404:
                    status = 'not_found'

                if status == 'registered':
                    result['registrations'].append({
                        'site': site['name'],
                        'status': 'registered',
                        'url': site['url'],
                    })
                    result['total_registered'] += 1
                elif status == 'available':
                    pass
                elif status == 'unknown':
                    result['registrations'].append({
                        'site': site['name'],
                        'status': 'unknown',
                        'url': site['url'],
                    })

            except (httpx.TimeoutException, httpx.RequestError):
                pass

            await asyncio.sleep(0.3)

    return result
