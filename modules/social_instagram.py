import asyncio
from modules.accounts_config import get_platform_accounts

INSTAGRAM_AVAILABLE = False
try:
    import instaloader
    INSTAGRAM_AVAILABLE = True
except ImportError:
    pass

async def scrape_instagram(target_username: str) -> dict:
    result = {
        'target': target_username,
        'authenticated': False,
        'profile': None,
        'followers': [],
        'following': [],
        'posts': [],
        'stories': [],
        'error': None,
    }

    if not INSTAGRAM_AVAILABLE:
        result['error'] = 'instaloader not installed'
        return result

    accounts = get_platform_accounts('instagram')
    if not accounts or not accounts.get('enabled'):
        result['error'] = 'No Instagram account configured'
        return result

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        compress_json=False,
        save_metadata_only=True,
        max_connection_attempts=2,
    )

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: loader.login(accounts['username'], accounts['password']))
        result['authenticated'] = True
    except Exception as e:
        result['error'] = f'Login failed: {str(e)[:200]}'
        return result

    try:
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(None, lambda: instaloader.Profile.from_username(loader.context, target_username))

        result['profile'] = {
            'username': profile.username,
            'full_name': profile.full_name,
            'biography': profile.biography,
            'external_url': profile.external_url,
            'profile_pic_url': profile.profile_pic_url,
            'business_category': profile.business_category_name,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'is_business': profile.is_business_account,
            'followers_count': profile.followers,
            'followees_count': profile.followees,
            'media_count': profile.mediacount,
            'igtv_count': profile.igtvcount,
            'highlight_reel_count': profile.highlight_reel_count,
            'has_public_story': profile.has_public_story,
            'has_public_highlights': profile.has_public_highlights,
            'has_highlight_reels': profile.has_highlight_reels,
            'has_igtv': profile.has_igtv,
        }

        if not profile.is_private:
            followers_iter = profile.get_followers()
            for _ in range(min(50, profile.followers)):
                try:
                    f = next(followers_iter)
                    result['followers'].append({
                        'username': f.username,
                        'full_name': f.full_name,
                        'is_private': f.is_private,
                        'is_verified': f.is_verified,
                        'bio': f.biography[:100] if f.biography else '',
                    })
                except StopIteration:
                    break

            followees_iter = profile.get_followees()
            for _ in range(min(50, profile.followees)):
                try:
                    f = next(followees_iter)
                    result['following'].append({
                        'username': f.username,
                        'full_name': f.full_name,
                        'is_private': f.is_private,
                        'is_verified': f.is_verified,
                    })
                except StopIteration:
                    break

            posts_iter = profile.get_posts()
            for _ in range(min(12, profile.mediacount)):
                try:
                    p = next(posts_iter)
                    result['posts'].append({
                        'shortcode': p.shortcode,
                        'url': f'https://instagram.com/p/{p.shortcode}/',
                        'caption': p.caption[:200] if p.caption else '',
                        'likes': p.likes,
                        'comments': p.comments,
                        'date': str(p.date),
                        'is_video': p.is_video,
                        'location': str(p.location) if p.location else None,
                        'tagged_users': [u.username for u in p.tagged_users if hasattr(u, 'username')][:10],
                    })
                except StopIteration:
                    break

    except instaloader.exceptions.ProfileNotExistsException:
        result['error'] = f'Profile @{target_username} does not exist'
    except Exception as e:
        result['error'] = str(e)[:300]

    return result
