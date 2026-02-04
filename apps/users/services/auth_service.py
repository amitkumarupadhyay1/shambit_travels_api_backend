import os
import requests
import logging
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

class OAuthTokenVerifier:
    """Verify OAuth tokens from external providers"""
    
    PROVIDER_CONFIGS = {
        'google': {
            'token_endpoint': 'https://www.googleapis.com/oauth2/v1/tokeninfo',
            'issuer': 'https://accounts.google.com',
        },
        'github': {
            'token_endpoint': 'https://api.github.com/user',
            'headers_prefix': 'token',
        }
    }
    
    @staticmethod
    def verify_google_token(token):
        """Verify Google OAuth token"""
        try:
            response = requests.get(
                OAuthTokenVerifier.PROVIDER_CONFIGS['google']['token_endpoint'],
                params={'id_token': token},
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Verify token not expired
            if 'expires_in' in data and int(data.get('expires_in', 0)) <= 0:
                logger.warning(f"Google token expired: {data}")
                return None
            
            return {
                'email': data.get('email'),
                'email_verified': data.get('email_verified', False),
                'provider': 'google',
                'uid': data.get('user_id'),
            }
        except Exception as e:
            logger.error(f"Google token verification failed: {str(e)}")
            return None
    
    @staticmethod
    def verify_github_token(token):
        """Verify GitHub OAuth token"""
        try:
            headers = {'Authorization': f'token {token}'}
            response = requests.get(
                OAuthTokenVerifier.PROVIDER_CONFIGS['github']['token_endpoint'],
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'email': data.get('email'),
                'email_verified': True,
                'provider': 'github',
                'uid': str(data.get('id')),
            }
        except Exception as e:
            logger.error(f"GitHub token verification failed: {str(e)}")
            return None
    
    @staticmethod
    def verify_token(provider, token):
        """Main verification dispatcher"""
        if provider == 'google':
            return OAuthTokenVerifier.verify_google_token(token)
        elif provider == 'github':
            return OAuthTokenVerifier.verify_github_token(token)
        else:
            logger.warning(f"Unknown OAuth provider: {provider}")
            return None


class AuthService:
    @staticmethod
    def sync_oauth_user(email, first_name, last_name, provider, uid, oauth_token=None):
        """
        Syncs a user from NextAuth OAuth provider.
        NOW REQUIRES TOKEN VERIFICATION.
        """
        # Verify token if provided
        if not oauth_token:
            raise ValueError("OAuth token is required for security verification")
        
        verified_data = OAuthTokenVerifier.verify_token(provider, oauth_token)
        if not verified_data:
            raise PermissionError(f"Failed to verify {provider} token")
        
        # Verify email matches
        if verified_data['email'] != email:
            logger.warning(
                f"Email mismatch: token has {verified_data['email']}, "
                f"request has {email}"
            )
            raise PermissionError("Email mismatch in OAuth token")
        
        # Verify email is verified by provider
        if not verified_data.get('email_verified', False):
            raise PermissionError(f"Email not verified by {provider}")
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
                'oauth_provider': provider,
                'oauth_uid': uid,
            }
        )
        
        if not created:
            # Update info if changed
            user.first_name = first_name
            user.last_name = last_name
            user.oauth_provider = provider
            user.oauth_uid = uid
            user.save()
            
            logger.info(f"Updated OAuth user {email}")
        else:
            logger.info(f"Created new OAuth user {email}")
        
        return user

    @staticmethod
    def get_tokens_for_user(user):
        """Get JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
