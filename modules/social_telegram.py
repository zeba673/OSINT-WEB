from modules.accounts_config import get_platform_accounts

TELEGRAM_AVAILABLE = False
try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
    TELEGRAM_AVAILABLE = True
except ImportError:
    pass

async def scrape_telegram(target: str, search_type: str = 'user') -> dict:
    result = {
        'target': target,
        'search_type': search_type,
        'authenticated': False,
        'user_info': None,
        'groups': [],
        'messages': [],
        'contacts': [],
        'channels': [],
        'error': None,
    }

    if not TELEGRAM_AVAILABLE:
        result['error'] = 'Telethon not installed'
        return result

    accounts = get_platform_accounts('telegram')
    if not accounts or not accounts.get('enabled'):
        result['error'] = 'No Telegram account configured'
        return result

    api_id = accounts.get('api_id')
    api_hash = accounts.get('api_hash')
    phone = accounts.get('phone')

    if not all([api_id, api_hash, phone]):
        result['error'] = 'Telegram API ID, Hash, and Phone required'
        return result

    session_path = '/tmp/telegram_osint_session'
    client = TelegramClient(session_path, int(api_id), api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            result['auth_code_sent'] = True
            result['error'] = 'Auth code sent to Telegram. Please add code to accounts_config.'
            return result
        result['authenticated'] = True

        me = await client.get_me()
        result['my_account'] = {
            'id': me.id,
            'username': me.username,
            'first_name': me.first_name,
            'last_name': me.last_name,
            'phone': me.phone,
        }

        try:
            entity = await client.get_entity(target)
            if hasattr(entity, 'username'):
                result['user_info'] = {
                    'id': entity.id,
                    'username': entity.username,
                    'first_name': getattr(entity, 'first_name', None),
                    'last_name': getattr(entity, 'last_name', None),
                    'phone': getattr(entity, 'phone', None),
                    'is_bot': getattr(entity, 'bot', False),
                    'is_verified': getattr(entity, 'verified', False),
                    'is_scam': getattr(entity, 'scam', False),
                    'is_fake': getattr(entity, 'fake', False),
                }
        except ValueError:
            result['info'] = f'Username/entity @{target} not found on Telegram'

        async for dialog in client.iter_dialogs(limit=30):
            entry = {
                'name': dialog.name,
                'id': dialog.id,
                'type': 'chat',
                'unread': dialog.unread_count,
            }
            if dialog.is_group:
                entry['type'] = 'group'
                try:
                    participants = []
                    async for user in client.iter_participants(dialog.entity, limit=10):
                        participants.append({
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': user.phone,
                            'is_bot': user.bot,
                        })
                    entry['participants'] = participants
                    result['groups'].append(entry)
                except Exception:
                    result['groups'].append(entry)
            elif dialog.is_channel:
                entry['type'] = 'channel'
                result['channels'].append(entry)
            else:
                result['contacts'].append(entry)

    except SessionPasswordNeededError:
        result['error'] = '2FA enabled. Password required.'
    except Exception as e:
        result['error'] = str(e)[:300]
    finally:
        await client.disconnect()

    return result
