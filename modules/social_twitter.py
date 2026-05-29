import httpx
import asyncio
from modules.accounts_config import get_platform_accounts

TWITTER_AVAILABLE = False
try:
    import snscrape.modules.twitter as sntwitter
    TWITTER_AVAILABLE = True
except Exception:
    pass

async def scrape_twitter(target_username: str) -> dict:
    result = {
        'target': target_username,
        'authenticated': False,
        'profile': None,
        'tweets': [],
        'mentions': [],
        'followers_count': 0,
        'following_count': 0,
        'error': None,
    }

    accounts = get_platform_accounts('twitter')
    token = None
    if accounts and accounts.get('enabled'):
        token = accounts.get('bearer_token')
        result['authenticated'] = bool(token)

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        try:
            api_url = f'https://api.twitter.com/2/users/by/username/{target_username}'
            if token:
                api_url += '?user.fields=created_at,description,public_metrics,location,profile_image_url,verified,protected,url,name,entities'
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json().get('data', {})
                    metrics = data.get('public_metrics', {})
                    result['profile'] = {
                        'id': data.get('id'),
                        'username': data.get('username'),
                        'name': data.get('name'),
                        'description': data.get('description'),
                        'location': data.get('location'),
                        'url': data.get('url'),
                        'profile_image_url': data.get('profile_image_url'),
                        'verified': data.get('verified', False),
                        'protected': data.get('protected', False),
                        'created_at': data.get('created_at'),
                        'followers_count': metrics.get('followers_count', 0),
                        'following_count': metrics.get('following_count', 0),
                        'tweet_count': metrics.get('tweet_count', 0),
                        'listed_count': metrics.get('listed_count', 0),
                    }
                    result['followers_count'] = metrics.get('followers_count', 0)
                    result['following_count'] = metrics.get('following_count', 0)
            else:
                resp = await client.get(f'https://nitter.net/{target_username}')
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    name_el = soup.select_one('.profile-card-fullname')
                    bio_el = soup.select_one('.profile-bio')
                    result['profile'] = {
                        'username': target_username,
                        'name': name_el.get_text(strip=True) if name_el else '',
                        'description': bio_el.get_text(strip=True) if bio_el else '',
                    }
        except Exception as e:
            result['error'] = str(e)[:200]

    if TWITTER_AVAILABLE:
        try:
            loop = asyncio.get_event_loop()
            tweets = []
            scraper = sntwitter.TwitterSearchScraper(f'from:{target_username}')
            for i, tweet in enumerate(scraper.get_items()):
                if i >= 20:
                    break
                tweets.append({
                    'id': tweet.id,
                    'url': tweet.url,
                    'content': tweet.rawContent[:300] if tweet.rawContent else '',
                    'date': str(tweet.date),
                    'likes': tweet.likeCount,
                    'retweets': tweet.retweetCount,
                    'replies': tweet.replyCount,
                    'media': [m.fullUrl for m in (tweet.media or []) if hasattr(m, 'fullUrl')],
                    'mentioned_users': list(tweet.mentionedUsers or []),
                    'hashtags': tweet.hashtags if tweet.hashtags else [],
                })
            result['tweets'] = tweets
        except Exception as e:
            if not result['error']:
                result['error'] = str(e)[:200]

    return result
