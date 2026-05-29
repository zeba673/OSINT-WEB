import httpx
import phonenumbers
from phonenumbers import carrier, geocoder, timezone

async def search_phone(phone: str) -> dict:
    results = {
        'phone': phone,
        'valid': False,
        'formatted': '',
        'country': '',
        'carrier': '',
        'timezones': [],
        'location': '',
        'web_results': [],
    }

    try:
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            results['valid'] = True
            results['formatted'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            results['country'] = geocoder.description_for_number(parsed, 'en') or ''
            results['carrier'] = carrier.name_for_number(parsed, 'en') or ''
            results['timezones'] = timezone.time_zones_for_number(parsed) or []
            results['location'] = geocoder.description_for_number(parsed, 'en') or ''
    except phonenumbers.NumberParseException:
        results['error'] = 'Invalid phone number format'

    if results['valid']:
        try:
            search_query = results['formatted'].replace(' ', '')
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(
                    f'https://www.google.com/search?q=%2B{search_query}',
                    headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
                )
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for link in soup.select('a[href^="/url?q="]')[:5]:
                        href = link.get('href', '')
                        if '/url?q=' in href:
                            url = href.split('/url?q=')[1].split('&')[0]
                            results['web_results'].append({
                                'title': link.get_text(strip=True) or url,
                                'url': url,
                            })
        except Exception:
            pass

    return results
