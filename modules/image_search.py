import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

async def reverse_image_search(image_url: str = None, image_path: str = None) -> dict:
    result = {
        'search_type': 'url' if image_url else 'file' if image_path else None,
        'google_results': [],
        'yandex_results': [],
        'tineye_results': [],
        'total_found': 0,
        'error': None,
    }

    if not image_url and not image_path:
        result['error'] = 'No image provided'
        return result

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20) as client:
        if image_url:
            try:
                search_url = f'https://lens.google.com/uploadbyurl?url={quote_plus(image_url)}'
                resp = await client.get(search_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if 'google.com' in href and '/imgres' in href:
                            result['google_results'].append({
                                'url': href,
                                'text': link.get_text(strip=True)[:100],
                            })

                search_url = f'https://yandex.com/images/search?url={quote_plus(image_url)}&rpt=imageview'
                resp = await client.get(search_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for link in soup.find_all('a', href=True)[:10]:
                        href = link['href']
                        if 'http' in href and 'yandex' not in href:
                            result['yandex_results'].append({
                                'url': href,
                                'text': link.get_text(strip=True)[:100],
                            })
            except Exception as e:
                result['error'] = str(e)[:200]

    result['total_found'] = len(result['google_results']) + len(result['yandex_results']) + len(result['tineye_results'])
    return result

FACEBOOK_DOWNLOADER_URLS = [
    'https://mbasic.facebook.com',
    'https://www.facebook.com/people',
]

PAID_PEOPLE_SEARCH = [
    {'name': 'Pipl', 'url': 'https://pipl.com/search/?q={query}', 'type': 'people_search'},
    {'name': 'Spokeo', 'url': 'https://www.spokeo.com/{query}', 'type': 'people_search'},
    {'name': 'BeenVerified', 'url': 'https://www.beenverified.com/people/{query}/', 'type': 'people_search'},
    {'name': 'PeekYou', 'url': 'https://peekyou.com/{query}', 'type': 'people_search'},
    {'name': 'Whitepages', 'url': 'https://www.whitepages.com/name/{query}', 'type': 'people_search'},
]

async def search_people_engines(query: str) -> dict:
    result = {
        'query': query,
        'results': [],
        'error': None,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for engine in PAID_PEOPLE_SEARCH:
            try:
                url = engine['url'].format(query=quote_plus(query))
                resp = await client.get(url)
                result['results'].append({
                    'engine': engine['name'],
                    'url': url,
                    'status': 'accessible' if resp.status_code == 200 else f'blocked_{resp.status_code}',
                    'size': len(resp.text),
                })
            except Exception as e:
                result['results'].append({
                    'engine': engine['name'],
                    'url': url,
                    'status': 'error',
                    'error': str(e)[:100],
                })

    return result
