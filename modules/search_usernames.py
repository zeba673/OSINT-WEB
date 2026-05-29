import httpx
import asyncio
from bs4 import BeautifulSoup

PLATFORMS = [
    {'name': 'GitHub', 'url': 'https://github.com/{username}', 'type': '404'},
    {'name': 'GitLab', 'url': 'https://gitlab.com/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found', 'could not be found']},
    {'name': 'Bitbucket', 'url': 'https://bitbucket.org/{username}', 'type': 'text', 'not_found': ['This page either doesn\'t exist', 'Page not found', 'Not Found']},
    {'name': 'Keybase', 'url': 'https://keybase.io/{username}', 'type': '404'},
    {'name': 'Flickr', 'url': 'https://www.flickr.com/people/{username}', 'type': '404'},
    {'name': 'SoundCloud', 'url': 'https://soundcloud.com/{username}', 'type': '404'},
    {'name': 'YouTube', 'url': 'https://www.youtube.com/@{username}', 'type': '404'},
    {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/user?id={username}', 'type': 'text', 'not_found': ['No such user', 'No such', 'Unknown']},
    {'name': 'Chess.com', 'url': 'https://www.chess.com/member/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'could not be found']},
    {'name': 'MyAnimeList', 'url': 'https://myanimelist.net/profile/{username}', 'type': 'text', 'not_found': ['not found', 'does not exist', 'Page Not Found']},
    {'name': 'Steam', 'url': 'https://steamcommunity.com/id/{username}', 'type': 'text', 'not_found': ['The specified profile could not be found', 'No profile', 'Page Not Found', 'Error']},
    {'name': 'Dev.to', 'url': 'https://dev.to/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'Medium', 'url': 'https://medium.com/@{username}', 'type': 'medium'},
    {'name': 'DevianArt', 'url': 'https://www.deviantart.com/{username}', 'type': 'text', 'not_found': ['Not Found', 'Page Not Found', 'This user hasn\'t joined']},
    {'name': 'Mixcloud', 'url': 'https://www.mixcloud.com/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found']},
    {'name': 'Codecademy', 'url': 'https://www.codecademy.com/profiles/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found', 'User not found']},
    {'name': 'Codepen', 'url': 'https://codepen.io/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found']},
    {'name': 'Mastodon.social', 'url': 'https://mastodon.social/@{username}', 'type': 'text', 'not_found': ['This page doesn\'t exist', 'no results', 'Not Found']},
    {'name': 'Replit', 'url': 'https://replit.com/@{username}', 'type': 'text', 'not_found': ['Page Not Found', 'doesn\'t exist']},
    {'name': 'Wattpad', 'url': 'https://www.wattpad.com/user/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'doesn\'t exist']},
    {'name': 'Patreon', 'url': 'https://www.patreon.com/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found', 'this page does not exist']},
    {'name': 'Dribbble', 'url': 'https://dribbble.com/{username}', 'type': 'text', 'not_found': ['Whoops', 'not found', 'Page Not Found']},
    {'name': 'Behance', 'url': 'https://www.behance.net/{username}', 'type': 'text', 'not_found': ['Page Not Found', 'Not Found', 'couldn\'t find']},
    {'name': 'Goodreads', 'url': 'https://www.goodreads.com/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'SlideShare', 'url': 'https://slideshare.net/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'AngelList', 'url': 'https://angel.co/u/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'ProductHunt', 'url': 'https://producthunt.com/@{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'Scribd', 'url': 'https://scribd.com/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'Bandcamp', 'url': 'https://bandcamp.com/{username}', 'type': 'text', 'not_found': ['Page not found', 'Not Found']},
    {'name': 'HackerOne', 'url': 'https://hackerone.com/{username}', 'type': 'text', 'not_found': ['Not Found', 'Page not found']},
    {'name': 'Bugcrowd', 'url': 'https://bugcrowd.com/{username}', 'type': 'text', 'not_found': ['Not Found', 'Page not found']},
    {'name': 'Shutterstock', 'url': 'https://shutterstock.com/g/{username}', 'type': 'text', 'not_found': ['Not Found', 'Page not found']},

    {'name': 'Telegram', 'url': 'https://t.me/{username}', 'type': 'telegram'},
    {'name': 'Pinterest', 'url': 'https://www.pinterest.com/{username}', 'type': 'pinterest'},
    {'name': 'Reddit', 'url': 'https://www.reddit.com/user/{username}', 'type': 'reddit'},

    {'name': 'TikTok', 'url': 'https://www.tiktok.com/@{username}', 'type': 'spa'},
    {'name': 'Instagram', 'url': 'https://instagram.com/{username}', 'type': 'spa'},
    {'name': 'Twitch', 'url': 'https://www.twitch.tv/{username}', 'type': 'spa'},
    {'name': 'Spotify', 'url': 'https://open.spotify.com/user/{username}', 'type': 'spa'},
    {'name': 'Threads', 'url': 'https://www.threads.net/@{username}', 'type': 'spa'},
    {'name': 'VK', 'url': 'https://vk.com/{username}', 'type': 'spa'},
    {'name': 'Snapchat', 'url': 'https://www.snapchat.com/add/{username}', 'type': 'spa'},
    {'name': 'Tumblr', 'url': 'https://{username}.tumblr.com', 'type': 'spa'},

    {'name': 'GitHub API', 'url': 'https://api.github.com/users/{username}', 'type': 'api'},

    {'name': 'X (Twitter)', 'url': 'https://x.com/{username}', 'type': 'twitter'},

    {'name': 'Facebook', 'url': 'https://www.facebook.com/{username}', 'type': 'facebook'},

    {'name': 'LinkedIn', 'url': 'https://www.linkedin.com/in/{username}', 'type': 'linkedin'},
]

async def check_platform(client: httpx.AsyncClient, username: str, platform: dict) -> dict | None:
    url = platform['url'].format(username=username)
    ptype = platform.get('type', 'text')

    try:
        resp = await client.get(url, follow_redirects=True, timeout=12)

        if resp.status_code == 429:
            return {'platform': platform['name'], 'url': url, 'status': 'rate_limited'}
        if resp.status_code == 403:
            return {'platform': platform['name'], 'url': url, 'status': 'blocked'}
        if resp.status_code == 404:
            return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

        if ptype == '404':
            if resp.status_code == 200:
                return {'platform': platform['name'], 'url': url, 'status': 'found'}
            return None

        elif ptype == 'api':
            if resp.status_code == 200:
                data = resp.json()
                if data.get('message') == 'Not Found':
                    return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
                if data.get('login'):
                    return {'platform': platform['name'], 'url': url, 'status': 'found'}
            return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

        elif ptype == 'facebook':
            final_url_lower = str(resp.url).lower()
            if 'login' in final_url_lower or 'signup' in final_url_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'redirect_login'}
            if resp.status_code >= 400:
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            return {'platform': platform['name'], 'url': url, 'status': 'found'}

        elif ptype == 'linkedin':
            final_url_lower = str(resp.url).lower()
            if 'login' in final_url_lower or 'signup' in final_url_lower or '/auth/' in final_url_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'redirect_login'}
            if 'notfound' in final_url_lower or '/search/' in final_url_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            if resp.status_code >= 400:
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            return {'platform': platform['name'], 'url': url, 'status': 'found'}

        elif ptype == 'telegram':
            if resp.status_code == 200:
                body_text = resp.text
                if 'Telegram: View @' in body_text or 'Telegram: view @' in body_text.lower():
                    return {'platform': platform['name'], 'url': url, 'status': 'found'}
                if 'Contact @' in body_text:
                    return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
                if 'doesn\'t appear to exist' in body_text.lower():
                    return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
                return {'platform': platform['name'], 'url': url, 'status': 'unverified'}
            return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

        elif ptype == 'medium':
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string if soup.title else ''
                meta_title = soup.find('meta', property='og:title')
                og_title = meta_title.get('content', '') if meta_title else ''
                if username.lower() in title.lower() or username.lower() in og_title.lower():
                    return {'platform': platform['name'], 'url': url, 'status': 'found'}
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

        elif ptype == 'pinterest':
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string if soup.title else ''
                if username.lower() in title.lower() and 'profile' in title.lower():
                    return {'platform': platform['name'], 'url': url, 'status': 'found'}
                not_found_inds = ['couldn\'t find', 'not found', 'this profile doesn\'t exist']
                if any(ind in resp.text.lower()[:3000] for ind in not_found_inds):
                    return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
                if str(resp.url) != url and 'pinterest' not in str(resp.url).lower():
                    return {'platform': platform['name'], 'url': url, 'status': 'redirect_away'}
                return {'platform': platform['name'], 'url': url, 'status': 'unverified'}
            return None

        elif ptype == 'reddit':
            body_lower = resp.text.lower()[:3000]
            if 'please wait for verification' in body_lower or 'rate limit' in body_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'rate_limited'}
            not_found_inds = ['Page Not Found', 'page not found', 'this page does not exist', 'nobody']
            if any(ind.lower() in body_lower for ind in not_found_inds):
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            if str(resp.url) != url and 'reddit' not in str(resp.url).lower():
                return {'platform': platform['name'], 'url': url, 'status': 'redirect_away'}
            return {'platform': platform['name'], 'url': url, 'status': 'unverified'}

        elif ptype == 'twitter':
            body_lower = resp.text.lower()[:3000]
            not_found_inds = ['this account doesn', 'this page doesn', 'No one at this', 'account suspended', 'doesn\'t exist']
            if any(ind in body_lower for ind in not_found_inds):
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}
            final_url_lower = str(resp.url).lower()
            if 'login' in final_url_lower or 'i/flow' in final_url_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'redirect_login'}
            return {'platform': platform['name'], 'url': url, 'status': 'unverified'}

        elif ptype == 'spa':
            return {'platform': platform['name'], 'url': url, 'status': 'unverified'}

        else:
            body_lower = resp.text.lower()[:3000]

            final_url_lower = str(resp.url).lower()
            if 'login' in final_url_lower or 'signup' in final_url_lower or '/auth/' in final_url_lower:
                return {'platform': platform['name'], 'url': url, 'status': 'redirect_login'}

            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string.lower()[:100] if soup.title else ''
            if 'client challenge' in title or 'just a moment' in title:
                return {'platform': platform['name'], 'url': url, 'status': 'blocked'}

            not_found = platform.get('not_found', [])
            for ind in not_found:
                if ind.lower() in body_lower or ind.lower() in title:
                    return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

            if resp.status_code >= 400:
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

            if 'error' in title:
                return {'platform': platform['name'], 'url': url, 'status': 'not_found'}

            if str(resp.url) != url:
                path = final_url_lower.split('?')[0]
                if username.lower() not in path:
                    return {'platform': platform['name'], 'url': url, 'status': 'redirect_away'}

            return {'platform': platform['name'], 'url': url, 'status': 'found'}

    except httpx.TimeoutException:
        return {'platform': platform['name'], 'url': url, 'status': 'timeout'}
    except httpx.RequestError as e:
        return {'platform': platform['name'], 'url': url, 'status': 'error', 'detail': str(e)[:100]}
    except Exception as e:
        return {'platform': platform['name'], 'url': url, 'status': 'error', 'detail': str(e)[:100]}

async def search_username(username: str) -> dict:
    results = {'username': username, 'profiles': [], 'total_found': 0, 'total_unverified': 0, 'errors': []}

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    async with httpx.AsyncClient(headers=headers, timeout=15, verify=False) as client:
        tasks = [check_platform(client, username, p) for p in PLATFORMS]
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            responses = await asyncio.gather(*batch, return_exceptions=True)
            for resp in responses:
                if isinstance(resp, dict) and resp is not None:
                    results['profiles'].append(resp)
                    if resp['status'] == 'found':
                        results['total_found'] += 1
                    elif resp['status'] == 'unverified':
                        results['total_unverified'] += 1
                elif isinstance(resp, Exception):
                    results['errors'].append(str(resp)[:200])

    results['profiles'].sort(key=lambda x: x['platform'].lower())
    return results
