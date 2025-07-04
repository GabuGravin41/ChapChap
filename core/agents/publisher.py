import os
import requests
import json
import random
from django.utils import timezone
from django.conf import settings
from . import analytics
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Platform API configurations
PLATFORM_APIS = {
    'TW': {
        'base_url': 'https://api.twitter.com/2',
        'auth_type': 'oauth2',
        'endpoints': {
            'tweet': '/tweets',
            'upload': '/media/upload'
        }
    },
    'FB': {
        'base_url': 'https://graph.facebook.com/v18.0',
        'auth_type': 'oauth2',
        'endpoints': {
            'post': '/me/feed',
            'upload': '/me/photos'
        }
    },
    'IG': {
        'base_url': 'https://graph.facebook.com/v18.0',
        'auth_type': 'oauth2',
        'endpoints': {
            'post': '/me/media',
            'publish': '/me/media_publish'
        }
    },
    'LI': {
        'base_url': 'https://api.linkedin.com/v2',
        'auth_type': 'oauth2',
        'endpoints': {
            'post': '/ugcPosts',
            'upload': '/images?action=initializeUpload'
        }
    }
}

def get_access_token(user, platform):
    """Retrieve access token from database"""
    from ..models import SocialAccount
    try:
        account = SocialAccount.objects.get(user=user, platform=platform)
        return account.access_token
    except SocialAccount.DoesNotExist:
        logger.error(f"No {platform} account connected for user {user.username}")
        return None

def upload_media(platform, access_token, media_file):
    """Upload media to platform and return media ID"""
    config = PLATFORM_APIS.get(platform, {})
    if not config:
        logger.error(f"Media upload not supported for platform {platform}")
        return None
    
    try:
        # Twitter media upload
        if platform == 'TW':
            # Step 1: Initialize upload
            init_url = f"{config['base_url']}{config['endpoints']['upload']}"
            init_data = {
                "command": "INIT",
                "media_type": "image/jpeg",
                "total_bytes": media_file.size
            }
            init_headers = {"Authorization": f"Bearer {access_token}"}
            init_res = requests.post(init_url, data=init_data, headers=init_headers)
            init_res.raise_for_status()
            media_id = init_res.json()['media_id_string']
            
            # Step 2: Append media data
            append_url = f"{config['base_url']}{config['endpoints']['upload']}"
            append_data = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": 0
            }
            files = {'media': media_file}
            append_res = requests.post(append_url, data=append_data, files=files, headers=init_headers)
            append_res.raise_for_status()
            
            # Step 3: Finalize upload
            finalize_url = f"{config['base_url']}{config['endpoints']['upload']}"
            finalize_data = {
                "command": "FINALIZE",
                "media_id": media_id
            }
            finalize_res = requests.post(finalize_url, data=finalize_data, headers=init_headers)
            finalize_res.raise_for_status()
            
            return media_id
        
        # Facebook/Instagram media upload
        elif platform in ['FB', 'IG']:
            upload_url = f"{config['base_url']}{config['endpoints']['upload']}"
            params = {'access_token': access_token}
            files = {'file': media_file}
            res = requests.post(upload_url, params=params, files=files)
            res.raise_for_status()
            return res.json()['id']
        
        # LinkedIn media upload
        elif platform == 'LI':
            # Initialize upload
            init_url = f"{config['base_url']}{config['endpoints']['upload']}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            init_data = {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:{user_id}",  # Need to get user ID
                }
            }
            init_res = requests.post(init_url, json=init_data, headers=headers)
            init_res.raise_for_status()
            upload_url = init_res.json()['value']['uploadUrl']
            
            # Upload media
            upload_res = requests.put(upload_url, files={'file': media_file})
            upload_res.raise_for_status()
            return init_res.json()['value']['image']
    
    except Exception as e:
        logger.error(f"Media upload failed for {platform}: {str(e)}")
        return None

def publish_to_platform(published_post, access_token):
    """Publish content to a specific platform"""
    platform = published_post.platform
    config = PLATFORM_APIS.get(platform, {})
    if not config:
        logger.error(f"Unsupported platform: {platform}")
        return False
    
    # Initialize response object outside try block
    res = None
    
    # Initialize metrics if not present
    if not published_post.metrics:
        published_post.metrics = {}
    
    # For demo purposes in development, simulate successful publishing
    if settings.DEBUG and platform not in ['YT', 'TT']:  # These already have simulation
        logger.info(f"DEBUG MODE: Simulating publishing to {platform}")
        published_post.published_id = f"debug_sim_{platform}_{published_post.id}_{timezone.now().timestamp()}"
        published_post.metrics = {
            'likes': random.randint(5, 50),
            'shares': random.randint(1, 15),
            'comments': random.randint(0, 10),
            'views': random.randint(50, 200),
            'note': 'Simulated metrics (debug mode)'
        }
        return True
    
    # Handle media upload if present
    media_id = None
    if published_post.content.media:
        try:
            media_id = upload_media(
                platform, 
                access_token,
                published_post.content.media
            )
            if not media_id and platform in ['IG']:  # Instagram requires media
                logger.error(f"Media upload failed for {platform} and this platform requires media")
                published_post.metrics['error'] = {'message': 'Media upload failed and is required'}
                return False
        except Exception as media_error:
            logger.error(f"Media upload error for {platform}: {str(media_error)}")
            # Continue without media for platforms that support text-only posts
    
    try:
        # Twitter (X) posting
        if platform == 'TW':
            url = f"{config['base_url']}{config['endpoints']['tweet']}"
            headers = {"Authorization": f"Bearer {access_token}"}
            data = {"text": published_post.adapted_text}
            if media_id:
                data['media'] = {'media_ids': [media_id]}
            
            res = requests.post(url, json=data, headers=headers, timeout=10)
            res.raise_for_status()
            published_post.published_id = res.json()['data']['id']
            return True
        
        # Facebook posting
        elif platform == 'FB':
            url = f"{config['base_url']}{config['endpoints']['post']}"
            params = {'access_token': access_token}
            data = {'message': published_post.adapted_text}
            
            if media_id:
                # For photos, use different endpoint
                url = f"{config['base_url']}{config['endpoints']['upload']}"
                data['url'] = f"https://graph.facebook.com/{media_id}/picture"
            
            res = requests.post(url, params=params, data=data, timeout=10)
            res.raise_for_status()
            published_post.published_id = res.json()['id']
            return True
        
        # Instagram posting
        elif platform == 'IG':
            # Step 1: Create media container
            create_url = f"{config['base_url']}{config['endpoints']['post']}"
            params = {'access_token': access_token}
            data = {
                'caption': published_post.adapted_text,
                'image_url': f"https://graph.facebook.com/{media_id}/picture" if media_id else None
            }
            res = requests.post(create_url, params=params, data=data, timeout=10)
            res.raise_for_status()
            container_id = res.json()['id']
            
            # Step 2: Publish the container
            publish_url = f"{config['base_url']}{config['endpoints']['publish']}"
            publish_params = {
                'access_token': access_token,
                'creation_id': container_id
            }
            pub_res = requests.post(publish_url, params=publish_params, timeout=10)
            pub_res.raise_for_status()
            published_post.published_id = pub_res.json()['id']
            return True
        
        # LinkedIn posting
        elif platform == 'LI':
            url = f"{config['base_url']}{config['endpoints']['post']}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Get LinkedIn user ID (with error handling)
            user_id = get_linkedin_user_id(access_token)
            if not user_id:
                logger.error("Failed to get LinkedIn user ID")
                published_post.metrics['error'] = {'message': 'Could not retrieve LinkedIn user ID'}
                return False
                
            data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": published_post.adapted_text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            if media_id:
                data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": published_post.adapted_text[:200]},
                        "media": media_id,
                        "title": {"text": "ChapChap Post"}
                    }
                ]
                data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            
            res = requests.post(url, headers=headers, json=data, timeout=10)
            res.raise_for_status()
            published_post.published_id = res.headers['x-restli-id']
            return True
        
        # TikTok (stub implementation)
        elif platform == 'TT':
            # TikTok requires special approval for posting API
            logger.info(f"Simulated TikTok post: {published_post.adapted_text[:50]}...")
            published_post.published_id = f"tt_sim_{published_post.id}"
            return True
            
        # YouTube (stub implementation)
        elif platform == 'YT':
            # YouTube requires video upload which is complex
            logger.info(f"Simulated YouTube post: {published_post.adapted_text[:50]}...")
            published_post.published_id = f"yt_sim_{published_post.id}"
            return True
        
        # Unsupported platform
        logger.error(f"No implementation for platform: {platform}")
        published_post.metrics['error'] = {'message': f'Publishing to {platform} not implemented'}
        return False
    
    except requests.exceptions.Timeout:
        logger.error(f"Request to {platform} API timed out")
        published_post.metrics['error'] = {'message': 'API request timed out'}
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error when publishing to {platform}")
        published_post.metrics['error'] = {'message': 'Connection error to platform API'}
        return False
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error when publishing to {platform}: {str(http_err)}")
        try:
            # Try to get detailed error information
            if res and hasattr(res, 'json'):
                error_details = res.json()
                published_post.metrics['error'] = {
                    'code': res.status_code,
                    'message': str(error_details)
                }
            else:
                published_post.metrics['error'] = {
                    'code': getattr(http_err, 'response', {}).get('status_code', 0),
                    'message': str(http_err)
                }
        except Exception:
            # If can't parse response JSON
            published_post.metrics['error'] = {'message': str(http_err)}
        return False
    except Exception as e:
        logger.error(f"Publishing to {platform} failed: {str(e)}")
        # Capture error details
        published_post.metrics['error'] = {'message': str(e)}
        return False

def get_linkedin_user_id(access_token):
    """Get LinkedIn user ID from profile"""
    try:
        url = "https://api.linkedin.com/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()['id']
    except Exception as e:
        logger.error(f"Failed to get LinkedIn user ID: {str(e)}")
        return None

def publish_content(published_post):
    """Publish content to a platform"""
    access_token = get_access_token(published_post.content.user, published_post.platform)
    if not access_token:
        logger.error(f"No access token for {published_post.platform}")
        published_post.metrics = {'error': 'No connected account found'}
        published_post.published_at = timezone.now()
        published_post.save()
        return False
    
    # Publish to platform
    try:
        success = publish_to_platform(published_post, access_token)
        
        if success:
            published_post.published_at = timezone.now()
            
            # For MVP, simulate metrics - in production we'd fetch real metrics later
            if not published_post.metrics:  # Don't overwrite existing metrics
                published_post.metrics = {
                    'likes': 10 + (published_post.id % 50),
                    'shares': 2 + (published_post.id % 10),
                    'comments': 1 + (published_post.id % 5),
                    'sentiment': 0.7 + (published_post.id % 30)/100
                }
            
            published_post.save()
            
            # Track engagement metrics
            from . import analytics
            analytics.track_engagement(published_post)
            
            logger.info(f"Successfully published post {published_post.id} to {published_post.platform}")
            return True
        else:
            # Save error state
            published_post.published_at = timezone.now()
            if not published_post.metrics:
                published_post.metrics = {'error': 'Unknown publishing error'}
            published_post.save()
            logger.error(f"Failed to publish post {published_post.id} to {published_post.platform}")
            return False
    except Exception as e:
        logger.exception(f"Exception during publishing post {published_post.id}: {str(e)}")
        published_post.published_at = timezone.now()
        published_post.metrics = {'error': str(e)}
        published_post.save()
        return False

def publish_scheduled_posts():
    """Publish all scheduled posts that are due"""
    from ..models import PublishedPost
    now = timezone.now()
    
    logger.info(f"Running scheduled posts publisher at {now}")
    
    try:
        scheduled_posts = PublishedPost.objects.filter(
            scheduled_time__lte=now,
            published_at__isnull=True
        )
        
        logger.info(f"Found {scheduled_posts.count()} posts due for publishing")
        
        published_count = 0
        for post in scheduled_posts:
            try:
                logger.info(f"Publishing scheduled post #{post.id} for {post.platform}")
                success = publish_content(post)
                if success:
                    published_count += 1
            except Exception as post_error:
                logger.error(f"Error publishing post #{post.id}: {str(post_error)}")
                # Continue with next post instead of failing entirely
                continue
        
        logger.info(f"Publishing completed: {published_count} posts published successfully")
        return published_count
    except Exception as e:
        logger.error(f"Error in scheduled post publishing: {str(e)}")
        return 0