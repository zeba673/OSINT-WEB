import httpx
import re
from bs4 import BeautifulSoup
from modules.accounts_config import get_platform_accounts

async def scrape_linkedin(target: str, search_type: str = 'people') -> dict:
    result = {
        'target': target,
        'search_type': search_type,
        'authenticated': False,
        'profiles': [],
        'jobs': [],
        'companies': [],
        'articles': [],
        'error': None,
    }

    accounts = get_platform_accounts('linkedin')
    cookies = {}

    if accounts and accounts.get('enabled') and accounts.get('li_at'):
        cookies['li_at'] = accounts['li_at']
        result['authenticated'] = True
    else:
        result['error'] = 'No LinkedIn session cookie configured'
        return result

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Csrf-Token': 'ajax:123456',
        'X-Requested-With': 'XMLHttpRequest',
    }

    async with httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=20) as client:
        try:
            encoded_target = target.replace(' ', '%20')
            search_url = f'https://www.linkedin.com/search/results/people/?keywords={encoded_target}'
            resp = await client.get(search_url)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/in/' in href and 'search' not in href:
                        name = link.get_text(strip=True)
                        if name and len(name) > 2:
                            profile_url = href if href.startswith('http') else f'https://www.linkedin.com{href}'
                            result['profiles'].append({
                                'name': name,
                                'url': profile_url.split('?')[0],
                            })

                text = soup.get_text()
                emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text))
                if emails:
                    result['emails_found'] = list(emails)[:5]

            if result['profiles']:
                profile_url = result['profiles'][0]['url']
                try:
                    resp = await client.get(profile_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        page_text = soup.get_text()

                        sections = re.split(r'\n{2,}', page_text)
                        result['page_sections'] = [s.strip() for s in sections if len(s.strip()) > 50][:5]

                        phones = set(re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}', page_text))
                        if phones:
                            result['phones_found'] = list(phones)[:3]

                except Exception:
                    pass
            else:
                result['info'] = 'No profiles found in search results'

        except Exception as e:
            result['error'] = str(e)[:300]

    if not result['profiles'] and not result['error']:
        result['info'] = 'No results found. Cookie may be expired.'

    return result
