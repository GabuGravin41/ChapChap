#!/usr/bin/env python3
"""
Debug script for X OAuth flow
This script helps identify issues with the OAuth implementation
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chapchap.settings')
django.setup()

from django.test import RequestFactory
from django.urls import reverse
from core.agents.oauth_service import x_oauth_service

def test_oauth_service():
    """Test the OAuth service configuration"""
    print("🔍 Testing X OAuth Service Configuration")
    print("=" * 50)
    
    # Test credentials
    print(f"Client ID: {x_oauth_service.client_id[:10]}..." if x_oauth_service.client_id else "Client ID: None")
    print(f"Client Secret: {x_oauth_service.client_secret[:10]}..." if x_oauth_service.client_secret else "Client Secret: None")
    print(f"Authorization URL: {x_oauth_service.authorization_base_url}")
    print(f"Token URL: {x_oauth_service.token_url}")
    print(f"Scopes: {x_oauth_service.scopes}")
    
    if not x_oauth_service.client_id or not x_oauth_service.client_secret:
        print("\n❌ ERROR: OAuth credentials not configured!")
        print("   Please check your .env file and make sure X_CLIENT_ID and X_CLIENT_SECRET are set.")
        return False
    
    return True

def test_authorization_url():
    """Test authorization URL generation"""
    print("\n🔗 Testing Authorization URL Generation")
    print("=" * 50)
    
    try:
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        request.META['wsgi.url_scheme'] = 'http'
        
        # Generate authorization URL
        auth_url, state, code_verifier = x_oauth_service.get_authorization_url(request)
        
        print("✅ Authorization URL generated successfully!")
        print(f"URL Length: {len(auth_url)}")
        print(f"State: {state[:10]}...")
        print(f"Code Verifier Length: {len(code_verifier)}")
        
        # Check URL components
        print("\n📋 URL Components Check:")
        print(f"Contains client_id: {'client_id=' in auth_url}")
        print(f"Contains redirect_uri: {'redirect_uri=' in auth_url}")
        print(f"Contains scope: {'scope=' in auth_url}")
        print(f"Contains code_challenge: {'code_challenge=' in auth_url}")
        print(f"Contains state: {'state=' in auth_url}")
        print(f"Contains response_type: {'response_type=' in auth_url}")
        
        # Show the actual URL
        print(f"\n🔗 Authorization URL:")
        print(auth_url)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR generating authorization URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_callback_url():
    """Test callback URL generation"""
    print("\n🔄 Testing Callback URL Generation")
    print("=" * 50)
    
    try:
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        request.META['wsgi.url_scheme'] = 'http'
        
        callback_url = request.build_absolute_uri(reverse('x_oauth_callback'))
        print(f"✅ Callback URL: {callback_url}")
        
        # Check if this matches what should be in X app settings
        expected_callback = "http://localhost:8000/x-oauth/callback/"
        if callback_url == expected_callback:
            print("✅ Callback URL matches expected format")
        else:
            print(f"⚠️  Callback URL doesn't match expected: {expected_callback}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR generating callback URL: {str(e)}")
        return False

def check_x_app_requirements():
    """Check X app configuration requirements"""
    print("\n⚙️  X App Configuration Requirements")
    print("=" * 50)
    
    print("Make sure your X app has these settings:")
    print("✅ App Type: 'Web App, Automated App or Bot' (NOT 'Native App')")
    print("✅ Callback URL: 'http://localhost:8000/x-oauth/callback/'")
    print("✅ Website URL: 'https://chapchap-on-render.com/' (NOT the callback URL)")
    print("✅ Scopes enabled:")
    for scope in x_oauth_service.scopes:
        print(f"   - {scope}")
    
    print("\n🔗 Go to: https://developer.x.com/en/portal/dashboard")
    print("   → Your App → Settings → Authentication settings")
    print("   → Update the settings above")

def main():
    """Main debug function"""
    print("🐦 X OAuth Debug Tool")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_oauth_service,
        test_authorization_url,
        test_callback_url,
        check_x_app_requirements
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! OAuth should work correctly.")
        print("\nNext steps:")
        print("1. Make sure your X app settings match the requirements above")
        print("2. Start your Django server: python manage.py runserver")
        print("3. Go to /accounts/ and try connecting your X account")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 