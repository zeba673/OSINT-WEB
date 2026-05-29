import httpx
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

async def analyze_url(url: str) -> dict:
    result = {
        'url': url,
        'parsed': None,
        'whois_info': None,
        'tech_stack': [],
        'screenshot_available': False,
        'page_title': None,
        'page_text_snippet': None,
        'links_found': [],
        'emails_found': [],
        'error': None,
    }

    try:
        parsed = urlparse(url)
        result['parsed'] = {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
        }
    except Exception as e:
        result['error'] = f'Parse error: {e}'
        return result

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                if soup.title:
                    result['page_title'] = soup.title.string[:200]

                text = soup.get_text()
                result['page_text_snippet'] = text[:500]

                emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text))
                result['emails_found'] = list(emails)[:10]

                for link in soup.find_all('a', href=True)[:20]:
                    href = link['href']
                    if href.startswith('http'):
                        result['links_found'].append({
                            'url': href[:200],
                            'text': link.get_text(strip=True)[:100],
                        })

                for script in soup.find_all('script', src=True):
                    src = script['src']
                    if 'jquery' in src.lower():
                        result['tech_stack'].append('jQuery')
                    elif 'react' in src.lower():
                        result['tech_stack'].append('React')
                    elif 'angular' in src.lower():
                        result['tech_stack'].append('Angular')
                    elif 'vue' in src.lower():
                        result['tech_stack'].append('Vue.js')
                    elif 'bootstrap' in src.lower():
                        result['tech_stack'].append('Bootstrap')
                    elif 'tailwind' in src.lower():
                        result['tech_stack'].append('Tailwind CSS')

                for meta in soup.find_all('meta', attrs={'name': 'generator'}):
                    gen = meta.get('content', '')
                    if gen:
                        result['tech_stack'].append(gen)

        except httpx.TimeoutException:
            result['error'] = 'Timeout loading page'
        except Exception as e:
            result['error'] = str(e)[:200]

    return result
