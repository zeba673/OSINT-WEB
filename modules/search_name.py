import httpx
from bs4 import BeautifulSoup
import urllib.parse

SEARCH_ENGINES = [
    {
        'name': 'Google',
        'url': 'https://www.google.com/search?q={query}',
        'selector': 'a[href^="/url?q="]',
        'link_extractor': lambda h: h.split('/url?q=')[1].split('&')[0] if '/url?q=' in h else h,
    },
    {
        'name': 'Bing',
        'url': 'https://www.bing.com/search?q={query}',
        'selector': 'a[href^="https://"]',
        'link_extractor': lambda h: h,
    },
    {
        'name': 'DuckDuckGo',
        'url': 'https://html.duckduckgo.com/html/?q={query}',
        'selector': 'a.result__a',
        'link_extractor': lambda h: h,
    },
]

async def search_name(name: str) -> dict:
    results = {
        'name': name,
        'profiles': [],
        'news_mentions': [],
        'web_results': [],
        'total_results': 0,
    }

    queries = [
        f'"{name}"',
        f'"{name}" linkedin',
        f'"{name}" twitter OR facebook OR instagram',
        f'"{name}" site:news.ycombinator.com',
    ]

    combined_results = {}
    for query in queries:
        for engine in SEARCH_ENGINES:
            try:
                url = engine['url'].format(query=urllib.parse.quote_plus(query))
                async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                    resp = await client.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    })
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        for link in soup.select(engine['selector'])[:5]:
                            href = link.get('href', '')
                            if href and href not in combined_results:
                                url_final = engine['link_extractor'](href)
                                if url_final.startswith('http'):
                                    combined_results[url_final] = {
                                        'title': link.get_text(strip=True) or url_final,
                                        'url': url_final,
                                        'source': engine['name'],
                                    }
            except Exception:
                continue

    all_links = list(combined_results.values())

    social_keywords = ['linkedin.com', 'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
                       'tiktok.com', 'youtube.com', 'github.com']
    for link in all_links:
        url_lower = link['url'].lower()
        if any(k in url_lower for k in social_keywords):
            results['profiles'].append(link)
        else:
            results['web_results'].append(link)

    results['total_results'] = len(all_links)
    return results
