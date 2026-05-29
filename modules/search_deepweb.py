import asyncio
from stem import Signal
from stem.control import Controller
import httpx
from config import config

DARK_WEB_SITES = [
    'http://darkfailenbsdla5w.onion',
    'http://hacktowns3sba2xci6fq.onion',
    'http://torlinksd6p54x4ay4d.onion',
]

async def check_tor_available() -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            'which', 'tor',
            stdout=asyncio.DEVNULL, stderr=asyncio.DEVNULL
        )
        code = await proc.wait()
        return code == 0
    except Exception:
        return False

async def get_tor_session() -> httpx.AsyncClient | None:
    try:
        transport = httpx.AsyncHTTPTransport(
            proxy=f'socks5://{config.TOR_HOST}:{config.TOR_PORT}',
        )
        client = httpx.AsyncClient(transport=transport, timeout=30)
        resp = await client.get('http://check.torproject.org', follow_redirects=True)
        if 'Congratulations' in resp.text:
            return client
        await client.aclose()
        return None
    except Exception:
        return None

async def renew_tor_identity():
    try:
        controller = Controller.from_port(port=config.TOR_CONTROL_PORT)
        controller.authenticate(password=config.TOR_PASSWORD)
        controller.signal(Signal.NEWNYM)
        controller.close()
        return True
    except Exception:
        return False

async def search_deepweb(query: str) -> dict:
    results = {
        'query': query,
        'tor_available': False,
        'tor_connected': False,
        'dark_web_mentions': [],
        'scanned_onions': [],
        'error': None,
    }

    tor_available = await check_tor_available()
    results['tor_available'] = tor_available

    if not tor_available:
        results['error'] = 'Tor is not installed on this system. Install with: sudo apt install tor'
        return results

    tor_client = await get_tor_session()
    if not tor_client:
        results['error'] = 'Could not connect to Tor. Is the Tor service running?'
        return results

    results['tor_connected'] = True

    try:
        for site_url in DARK_WEB_SITES:
            try:
                resp = await tor_client.get(site_url, timeout=20)
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.get_text()
                    if query.lower() in text.lower():
                        snippet_start = max(0, text.lower().index(query.lower()) - 100)
                        snippet = text[snippet_start:snippet_start + 300]
                        results['dark_web_mentions'].append({
                            'url': site_url,
                            'snippet': snippet,
                        })
                    results['scanned_onions'].append({
                        'url': site_url,
                        'status': 'accessible',
                        'title': soup.title.string if soup.title else site_url,
                    })
                else:
                    results['scanned_onions'].append({
                        'url': site_url,
                        'status': f'error_{resp.status_code}',
                    })
            except Exception as e:
                results['scanned_onions'].append({
                    'url': site_url,
                    'status': 'timeout',
                    'error': str(e)[:100],
                })
    finally:
        await tor_client.aclose()

    return results
