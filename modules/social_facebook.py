import httpx
import re
from bs4 import BeautifulSoup
from modules.accounts_config import get_platform_accounts

async def scrape_facebook(target: str, search_type: str = 'profile') -> dict:
    result = {
        'target': target,
        'search_type': search_type,
        'authenticated': False,
        'profiles_found': [],
        'pages_found': [],
        'groups_found': [],
        'posts': [],
        'photos': [],
        'places': [],
        'error': None,
    }

    accounts = get_platform_accounts('facebook')
    cookies = {}
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    if accounts and accounts.get('enabled'):
        if accounts.get('cookie_c_user') and accounts.get('cookie_xs'):
            cookies['c_user'] = accounts['cookie_c_user']
            cookies['xs'] = accounts['cookie_xs']
            result['authenticated'] = True
        if accounts.get('user_agent'):
            user_agent = accounts['user_agent']

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    async with httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=20) as client:
        try:
            search_urls = [
                f'https://www.facebook.com/search/top?q={target}',
                f'https://www.facebook.com/public/{target}',
            ]

            for url in search_urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')

                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            text = link.get_text(strip=True)
                            if '/profile.php' in href or '/people/' in href:
                                result['profiles_found'].append({
                                    'name': text or 'Profile',
                                    'url': f'https://www.facebook.com{href}' if href.startswith('/') else href,
                                })
                            elif '/groups/' in href and 'groups/feed' not in href:
                                result['groups_found'].append({
                                    'name': text or 'Group',
                                    'url': f'https://www.facebook.com{href}' if href.startswith('/') else href,
                                })
                            elif 'facebook.com' in href and '/photos/' in href:
                                result['photos'].append({
                                    'url': href if href.startswith('http') else f'https://www.facebook.com{href}',
                                })

                except Exception:
                    continue

            if result['profiles_found']:
                profile_url = result['profiles_found'][0]['url']
                try:
                    resp = await client.get(profile_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        page_text = soup.get_text()

                        name_patterns = [
                            r'([A-Z][a-z]+ [A-Z][a-z]+)',
                        ]
                        found_names = set()
                        for p in name_patterns:
                            for m in re.finditer(p, page_text):
                                name = m.group(1)
                                if len(name) > 3 and len(name) < 50:
                                    found_names.add(name)

                        emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', page_text))
                        phones = set(re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}', page_text))

                        result['posts'] = found_names
                        if emails:
                            result['emails_found'] = list(emails)[:5]
                        if phones:
                            result['phones_found'] = list(phones)[:5]

                except Exception:
                    pass

        except Exception as e:
            result['error'] = str(e)[:300]

    return result
