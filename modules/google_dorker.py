import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

DORK_CATEGORIES = {
    'emails': [
        '"{query}" email',
        '"{query}" @gmail.com OR @hotmail.com OR @outlook.com',
        '"{query}" "email address"',
        '"{query}" contact',
    ],
    'documents': [
        '"{query}" filetype:pdf',
        '"{query}" filetype:doc OR filetype:docx',
        '"{query}" filetype:xls OR filetype:xlsx',
    ],
    'social': [
        '"{query}" site:linkedin.com/in',
        '"{query}" site:facebook.com',
        '"{query}" site:twitter.com OR site:x.com',
        '"{query}" site:instagram.com',
        '"{query}" site:tiktok.com/@',
    ],
    'data_leaks': [
        '"{query}" "password" OR "pass" OR "credential"',
        '"{query}" "leaked" OR "breach" OR "dump"',
        '"{query}" "api_key" OR "api-key" OR "apikey"',
        '"{query}" "token" OR "secret" OR "private"',
    ],
    'code_repos': [
        '"{query}" site:github.com',
        '"{query}" site:gitlab.com',
        '"{query}" site:bitbucket.org',
        '"{query}" site:pastebin.com',
    ],
    'personal_info': [
        '"{query}" phone OR "cell" OR "mobile" OR "whatsapp"',
        '"{query}" address OR "street" OR "city" OR "zip"',
        '"{query}" "date of birth" OR "birthday" OR "born"',
    ],
}

async def google_dork_search(query: str, categories: list = None) -> dict:
    result = {
        'query': query,
        'categories': {},
        'total_results': 0,
    }

    if categories is None:
        categories = list(DORK_CATEGORIES.keys())

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for cat in categories:
            dorks = DORK_CATEGORIES.get(cat, [])
            cat_results = []
            for dork in dorks:
                formatted_dork = dork.format(query=quote_plus(query))
                try:
                    search_url = f'https://www.google.com/search?q={quote_plus(formatted_dork)}&num=5'
                    resp = await client.get(search_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        for link in soup.select('a[href^="/url?q="]')[:3]:
                            href = link.get('href', '')
                            if '/url?q=' in href:
                                url = href.split('/url?q=')[1].split('&')[0]
                                cat_results.append({
                                    'dork': dork,
                                    'url': url,
                                    'title': link.get_text(strip=True)[:100],
                                })
                except Exception:
                    continue

            if cat_results:
                result['categories'][cat] = cat_results
                result['total_results'] += len(cat_results)

    return result
