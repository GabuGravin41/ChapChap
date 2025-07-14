import os
import secrets
import hashlib
import base64
import requests
import logging
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)

class XOAuthService:
    """
    X (Twitter) OAuth 2.0 service for user authentication
    Implements Authorization Code Flow with PKCE
    """
    
    def __init__(self):
        self.client_id = getattr(settings, 'X_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'X_CLIENT_SECRET', '')
        
        # X OAuth 2.0 endpoints - Updated to correct URLs
        self.authorization_base_url = 'https://twitter.com/i/oauth2/authorize'
        self.token_url = 'https://api.twitter.com/2/oauth2/token'
        self.user_info_url = 'https://api.twitter.com/2/users/me'
        
        # Required scopes for posting tweets
        self.scopes = ['tweet.read', 'tweet.write', 'users.read', 'offline.access']
        
        if not self.client_id or not self.client_secret:
            logger.warning("X OAuth credentials not configured. Please set X_CLIENT_ID and X_CLIENT_SECRET in settings.")
        else:
            logger.info(f"X OAuth service initialized with client_id: {self.client_id[:10]}...")
    
    def generate_pkce_pair(self):
        """Generate PKCE code verifier and challenge"""
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, request):
        """
        Generate authorization URL for user to authorize the application
        Returns: (authorization_url, state, code_verifier)
        """
        try:
            logger.info("Starting authorization URL generation...")
            
            # Generate PKCE parameters
            code_verifier, code_challenge = self.generate_pkce_pair()
            logger.info(f"Generated PKCE - verifier length: {len(code_verifier)}, challenge length: {len(code_challenge)}")
            
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)
            logger.info(f"Generated state: {state[:10]}...")
            
            # Build redirect URI
            redirect_uri = request.build_absolute_uri(reverse('x_oauth_callback'))
            logger.info(f"Redirect URI: {redirect_uri}")
            
            # Create OAuth2 session
            oauth = OAuth2Session(
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                scope=self.scopes,
                state=state
            )
            logger.info(f"Created OAuth2Session with client_id: {self.client_id[:10]}...")
            
            # Generate authorization URL with PKCE
            authorization_url, state = oauth.authorization_url(
                self.authorization_base_url,
                state=state,
                code_challenge=code_challenge,
                code_challenge_method='S256'
            )
            
            logger.info(f"Generated authorization URL: {authorization_url[:100]}...")
            logger.info(f"Authorization URL length: {len(authorization_url)}")
            logger.info(f"Contains client_id: {'client_id=' in authorization_url}")
            logger.info(f"Contains redirect_uri: {'redirect_uri=' in authorization_url}")
            logger.info(f"Contains scope: {'scope=' in authorization_url}")
            logger.info(f"Contains code_challenge: {'code_challenge=' in authorization_url}")
            
            return authorization_url, state, code_verifier
            
        except Exception as e:
            logger.error(f"Error generating X authorization URL: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def exchange_code_for_token(self, request, authorization_code, state, code_verifier):
        """
        Exchange authorization code for access token
        Returns: token_data dict or None if failed
        """
        try:
            redirect_uri = request.build_absolute_uri(reverse('x_oauth_callback'))
            
            # Prepare token request data
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier
            }
            
            # Make token request
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info("Successfully exchanged authorization code for access token")
                return token_data
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    def get_user_info(self, access_token):
        """
        Get user information using access token
        Returns: user_info dict or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                self.user_info_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_info = {
                    'id': user_data['data']['id'],
                    'username': user_data['data']['username'],
                    'name': user_data['data']['name'],
                    'verified': user_data['data'].get('verified', False)
                }
                logger.info(f"Successfully retrieved user info for @{user_info['username']}")
                return user_info
            else:
                logger.error(f"User info request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token):
        """
        Refresh access token using refresh token
        Returns: new_token_data dict or None if failed
        """
        try:
            token_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                new_token_data = response.json()
                logger.info("Successfully refreshed access token")
                return new_token_data
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    def is_token_valid(self, access_token):
        """
        Check if access token is still valid
        Returns: True if valid, False otherwise
        """
        try:
            user_info = self.get_user_info(access_token)
            return user_info is not None
        except Exception as e:
            logger.error(f"Error checking token validity: {str(e)}")
            return False

# Initialize the service
x_oauth_service = XOAuthService() 