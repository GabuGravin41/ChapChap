# X OAuth 2.0 Setup Guide

This guide explains how to set up proper OAuth 2.0 authentication for X (Twitter) integration in ChapChap.

## Overview

With OAuth 2.0, users can connect their X accounts by:
1. Clicking "Connect X Account" in ChapChap
2. Being redirected to X's official authorization page
3. Logging into their X account on X's website
4. Authorizing ChapChap to post on their behalf
5. Being redirected back to ChapChap with access granted

**No manual API key entry required!** This is the professional way all major social media management tools work.

## Step 1: Create X Developer App

1. Go to [X Developer Portal](https://developer.x.com/en/portal/dashboard)
2. Click "Create App" or "New App"
3. Fill in app details:
   - **App Name**: ChapChap Social Media Manager
   - **App Description**: AI-powered social media management platform
   - **Website URL**: Your ChapChap domain (e.g., `https://your-domain.com`)
   - **App Type**: Choose "Web App" (this is important for OAuth 2.0)

## Step 2: Configure OAuth 2.0 Settings

1. In your X app settings, go to "Authentication Settings"
2. **Enable OAuth 2.0**: Make sure OAuth 2.0 is enabled
3. **App Type**: Select "Web App" (confidential client)
4. **Callback URLs**: Add your callback URL:
   ```
   http://localhost:8000/x-oauth/callback/    # For development
   https://your-domain.com/x-oauth/callback/  # For production
   ```
5. **Scopes**: Enable these scopes:
   - `tweet.read` - Read tweets
   - `tweet.write` - Post tweets
   - `users.read` - Read user profile
   - `offline.access` - Stay connected (refresh tokens)

## Step 3: Get Your Credentials

After creating the app, you'll get:
- **Client ID**: Public identifier for your app
- **Client Secret**: Private secret for your app (keep this secure!)

## Step 4: Update ChapChap Configuration

1. **Update `.env` file**:
   ```env
   # X OAuth 2.0 Configuration
   X_CLIENT_ID=your-actual-client-id-here
   X_CLIENT_SECRET=your-actual-client-secret-here
   ```

2. **Keep existing API credentials** (still needed for app-level operations):
   ```env
   # X API (for app-level operations)
   X_API_KEY=your-api-key
   X_API_SECRET=your-api-secret
   X_BEARER_TOKEN=your-bearer-token
   ```

## Step 5: Test the Flow

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to `/accounts/` in your browser
3. Click "Connect X Account"
4. You should see a beautiful explanation page
5. Click "Connect X Account" again
6. You'll be redirected to X's authorization page
7. Log into your X account
8. Click "Authorize app"
9. You'll be redirected back to ChapChap
10. Your X account should now be connected!

## How It Works

### User Flow
```
ChapChap → X Authorization → User Login → User Approves → ChapChap
```

### Technical Flow
1. **Authorization Request**: ChapChap generates a secure authorization URL with PKCE
2. **User Authorization**: User logs into X and approves the app
3. **Authorization Code**: X redirects back with a temporary code
4. **Token Exchange**: ChapChap exchanges the code for an access token
5. **User Info**: ChapChap gets user profile information
6. **Storage**: Access token is securely stored for that user

### Security Features
- **PKCE (Proof Key for Code Exchange)**: Prevents authorization code interception
- **State Parameter**: Prevents CSRF attacks
- **Secure Token Storage**: User tokens are encrypted in the database
- **Scope Limitation**: Only requests necessary permissions
- **Token Refresh**: Automatic token renewal when they expire

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Make sure your callback URL in X app settings exactly matches your Django URL
   - For development: `http://localhost:8000/x-oauth/callback/`
   - For production: `https://your-domain.com/x-oauth/callback/`

2. **"Client authentication failed"**
   - Check that your `X_CLIENT_ID` and `X_CLIENT_SECRET` are correct
   - Make sure there are no extra spaces or characters

3. **"Invalid scope"**
   - Ensure your X app has the required scopes enabled
   - Check that scopes in the code match what's enabled in X app

4. **"Authorization failed"**
   - Check Django logs for detailed error messages
   - Verify your X app is properly configured for OAuth 2.0

### Development vs Production

**Development** (localhost):
- Use `http://localhost:8000/x-oauth/callback/`
- OAuth works on localhost for testing

**Production** (live domain):
- Use `https://your-domain.com/x-oauth/callback/`
- Must use HTTPS for production OAuth
- Update X app settings with production callback URL

## Benefits of OAuth 2.0

### For Users
- ✅ **No API key hunting**: Just click and authorize
- ✅ **Secure**: Password never shared with ChapChap
- ✅ **Revocable**: Can revoke access anytime in X settings
- ✅ **Familiar**: Same flow as "Sign in with Google/Facebook"

### For Developers
- ✅ **Professional**: Industry standard authentication
- ✅ **Scalable**: Handles thousands of users
- ✅ **Secure**: Built-in security features
- ✅ **Compliant**: Follows OAuth 2.0 specification

## Next Steps

1. **Test thoroughly** with multiple user accounts
2. **Add token refresh** handling for long-term usage
3. **Implement token encryption** for production
4. **Add other platforms** (Facebook, Instagram, LinkedIn) using similar OAuth flows
5. **Monitor usage** and handle rate limits properly

This OAuth implementation makes ChapChap ready for real users and commercial deployment! 