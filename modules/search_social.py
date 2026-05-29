import httpx
from bs4 import BeautifulSoup
import re

SOCIAL_SITES = [
    {'name': 'Twitter/X', 'url_tmpl': 'https://nitter.net/{username}', 'bio_selector': 'div.profile-bio'},
    {'name': 'Instagram', 'url_tmpl': 'https://imginn.com/{username}/', 'bio_selector': 'div.bio'},
    {'name': 'Reddit', 'url_tmpl': 'https://old.reddit.com/user/{username}/about.json', 'is_json': True},
    {'name': 'GitHub', 'url_tmpl': 'https://api.github.com/users/{username}', 'is_json': True},
]

async def analyze_social_profiles(username: str, found_profiles: list) -> dict:
    results = {
        'username': username,
        'profiles_analyzed': [],
        'common_info': {},
        'connections': [],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        for profile in found_profiles[:10]:
            platform = profile.get('platform', '')
            url = profile.get('url', '')
            site = next((s for s in SOCIAL_SITES if s['name'] == platform), None)
            if not site:
                continue

            profile_data = {'platform': platform, 'url': url, 'bio': None, 'info': {}}
            try:
                if site.get('is_json'):
                    resp = await client.get(site['url_tmpl'].format(username=username))
                    if resp.status_code == 200:
                        data = resp.json()
                        if platform == 'GitHub':
                            profile_data['info'] = {
                                'name': data.get('name'),
                                'company': data.get('company'),
                                'location': data.get('location'),
                                'blog': data.get('blog'),
                                'bio': data.get('bio'),
                                'public_repos': data.get('public_repos'),
                                'followers': data.get('followers'),
                                'following': data.get('following'),
                                'created_at': data.get('created_at'),
                            }
                        elif platform == 'Reddit':
                            reddit_data = data.get('data', {})
                            profile_data['info'] = {
                                'created_utc': reddit_data.get('created_utc'),
                                'link_karma': reddit_data.get('link_karma'),
                                'comment_karma': reddit_data.get('comment_karma'),
                                'is_mod': reddit_data.get('is_mod'),
                                'is_gold': reddit_data.get('is_gold'),
                                'has_verified_email': reddit_data.get('has_verified_email'),
                            }
                else:
                    resp = await client.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    })
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        bio_el = soup.select_one(site['bio_selector'])
                        if bio_el:
                            profile_data['bio'] = bio_el.get_text(strip=True)[:500]
            except Exception:
                pass

            results['profiles_analyzed'].append(profile_data)

    locations = []
    names = []
    for p in results['profiles_analyzed']:
        info = p.get('info', {})
        if info.get('location'):
            locations.append(info['location'])
        if info.get('name'):
            names.append(info['name'])
        if p.get('bio'):
            names.extend(re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', p['bio']))

    if locations:
        from collections import Counter
        results['common_info']['locations'] = [loc for loc, _ in Counter(locations).most_common(3)]
    if names:
        from collections import Counter
        results['common_info']['possible_names'] = [n for n, _ in Counter(names).most_common(5)]

    return results
