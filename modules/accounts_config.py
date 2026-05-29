import json
import os
from pathlib import Path

ACCOUNTS_FILE = Path(__file__).parent.parent / 'social_accounts.json'

def load_accounts() -> dict:
    if not ACCOUNTS_FILE.exists():
        return {}
    try:
        with open(ACCOUNTS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_accounts(data: dict):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_platform_accounts(platform: str) -> dict | None:
    accounts = load_accounts()
    return accounts.get(platform)

def get_all_configured() -> list:
    accounts = load_accounts()
    return [{'platform': k, 'configured': bool(v.get('enabled', False))} for k, v in accounts.items()]

def is_configured(platform: str) -> bool:
    data = get_platform_accounts(platform)
    return bool(data and data.get('enabled'))

ACCOUNT_SCHEMAS = {
    'instagram': {
        'fields': [
            {'key': 'username', 'label': 'Instagram Username', 'type': 'text', 'required': True},
            {'key': 'password', 'label': 'Instagram Password', 'type': 'password', 'required': True},
        ],
        'description': 'Scrape followers, following, stories, posts, bio, email, phone',
    },
    'twitter': {
        'fields': [
            {'key': 'bearer_token', 'label': 'Twitter Bearer Token', 'type': 'password', 'required': True},
            {'key': 'cookie_auth', 'label': 'Twitter Auth Cookie (auth_token)', 'type': 'password', 'required': False},
        ],
        'description': 'Search tweets, followers, following, likes, media',
    },
    'facebook': {
        'fields': [
            {'key': 'cookie_c_user', 'label': 'Facebook c_user cookie', 'type': 'password', 'required': True},
            {'key': 'cookie_xs', 'label': 'Facebook xs cookie', 'type': 'password', 'required': True},
            {'key': 'user_agent', 'label': 'Your Browser User-Agent', 'type': 'text', 'required': False},
        ],
        'description': 'Search profiles, friends, groups, photos, check-ins',
    },
    'linkedin': {
        'fields': [
            {'key': 'li_at', 'label': 'LinkedIn session cookie (li_at)', 'type': 'password', 'required': True},
        ],
        'description': 'Search profiles, company info, connections, work history',
    },
    'telegram': {
        'fields': [
            {'key': 'api_id', 'label': 'Telegram API ID', 'type': 'text', 'required': True},
            {'key': 'api_hash', 'label': 'Telegram API Hash', 'type': 'password', 'required': True},
            {'key': 'phone', 'label': 'Phone number (+1234567890)', 'type': 'text', 'required': True},
        ],
        'description': 'Search groups, channels, messages, user info',
    },
    'discord': {
        'fields': [
            {'key': 'user_token', 'label': 'Discord User Token', 'type': 'password', 'required': True},
        ],
        'description': 'Search servers, messages, friends, user info',
    },
    'github': {
        'fields': [
            {'key': 'token', 'label': 'GitHub Personal Token', 'type': 'password', 'required': False},
        ],
        'description': 'Search repos, commits, emails, private info (optional - public API works without)',
    },
}

def get_account_schema(platform: str) -> dict | None:
    return ACCOUNT_SCHEMAS.get(platform)
