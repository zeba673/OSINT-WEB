import httpx
from bs4 import BeautifulSoup

LEAK_SITES = [
    {'name': 'IntelX', 'url': 'https://intelx.io/?s={query}', 'type': 'search'},
    {'name': 'DeHashed', 'url': 'https://dehashed.com/search?query={query}', 'type': 'search'},
    {'name': 'LeakCheck', 'url': 'https://leakcheck.io/search?query={query}', 'type': 'search'},
    {'name': 'SnusBase', 'url': 'https://snusbase.com/search?query={query}', 'type': 'search'},
]

PUBLIC_PASTE_SITES = [
    {'name': 'Pastebin', 'url': 'https://pastebin.com/search?q={query}'},
    {'name': 'Ghostbin', 'url': 'https://ghostbin.com/search?term={query}'},
]

async def check_breaches(query: str, query_type: str = 'email') -> dict:
    result = {
        'query': query,
        'query_type': query_type,
        'leak_sites': [],
        'paste_sites': [],
        'total_leaks': 0,
        'error': None,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for site in LEAK_SITES:
            try:
                url = site['url'].format(query=query)
                resp = await client.get(url)
                result['leak_sites'].append({
                    'site': site['name'],
                    'url': url,
                    'status': 'found' if resp.status_code == 200 else f'error_{resp.status_code}',
                    'content_length': len(resp.text),
                })
                if resp.status_code == 200:
                    result['total_leaks'] += 1
            except Exception as e:
                result['leak_sites'].append({
                    'site': site['name'],
                    'status': 'error',
                    'error': str(e)[:100],
                })

    return result
