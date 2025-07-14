# GitHub Setup Guide for ChapChap

This guide ensures your ChapChap project is properly configured for GitHub deployment while protecting sensitive information.

## 🔒 Security Checklist

### 1. Environment Variables Protection
✅ **`.env` file is in `.gitignore`** - This prevents your API keys from being committed
✅ **Enhanced `.gitignore`** - Comprehensive protection for all sensitive files

### 2. Required Steps Before Pushing to GitHub

#### Step 1: Check if .env is already tracked
```bash
git ls-files | grep .env
```

If `.env` appears in the output, remove it from tracking:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking for security"
```

#### Step 2: Create a template file for other developers
Create `.env.example` with placeholder values:
```bash
cp .env .env.example
```

Then edit `.env.example` to replace real values with placeholders:
```env
# ChapChap Environment Configuration Template
# Copy this file to .env and fill in your actual values

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///db.sqlite3

# X (Twitter) API
X_API_KEY=your-x-api-key
X_API_SECRET=your-x-api-secret
X_ACCESS_TOKEN=your-x-access-token
X_ACCESS_TOKEN_SECRET=your-x-access-token-secret
X_BEARER_TOKEN=your-x-bearer-token

# X OAuth 2.0 Configuration
X_CLIENT_ID=your-x-oauth-client-id
X_CLIENT_SECRET=your-x-oauth-client-secret

# Other API credentials (fill as needed)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# AI Model API Keys
OPENAI_API_KEY=your-openai-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key
OPENROUTER_API_KEY=your-openrouter-api-key

# Additional settings
REDIS_URL=redis://localhost:6379
```

#### Step 3: Add .env.example to git
```bash
git add .env.example
git commit -m "Add environment template file"
```

#### Step 4: Verify sensitive files are ignored
```bash
git status
```

You should NOT see `.env` in the output.

### 3. GitHub Repository Setup

#### Step 1: Initialize git (if not already done)
```bash
git init
git add .
git commit -m "Initial commit: ChapChap social media management platform"
```

#### Step 2: Create GitHub repository
1. Go to GitHub.com
2. Click "New repository"
3. Name it "ChapChap" or "chapchap-social-media"
4. Make it public or private (your choice)
5. Don't initialize with README (we already have one)

#### Step 3: Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 4. Deployment Considerations

#### For Render.com (recommended)
1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard:
   - Go to your service settings
   - Add all variables from your `.env` file
   - Never commit the actual `.env` file

#### For other platforms
- **Heroku**: Use `heroku config:set` for each variable
- **Railway**: Set environment variables in dashboard
- **DigitalOcean**: Use App Platform environment variables

### 5. Security Best Practices

#### ✅ What's Protected
- API keys and secrets
- Database credentials
- OAuth client secrets
- Django secret key
- Personal access tokens

#### ✅ What's Safe to Commit
- Code files (`.py`, `.js`, `.html`, etc.)
- Configuration templates (`.env.example`)
- Documentation files
- Static assets
- Requirements files

### 6. Team Development

#### For new developers:
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Fill in their own API keys
4. Never commit their `.env` file

#### For production deployment:
1. Set environment variables in hosting platform
2. Use production database (PostgreSQL recommended)
3. Set `DEBUG=False` in production
4. Use strong `SECRET_KEY`

### 7. Verification Commands

Run these commands to verify everything is secure:

```bash
# Check if .env is ignored
git check-ignore .env

# Check if any sensitive files are tracked
git ls-files | grep -E "\.(env|key|secret|pem|p12)"

# Verify .gitignore is working
git status
```

### 8. Troubleshooting

#### If .env is still being tracked:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

#### If you accidentally committed sensitive data:
1. **IMMEDIATELY** rotate all API keys
2. Remove the commit from history:
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch .env' \
   --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push to GitHub:
   ```bash
   git push origin --force
   ```

## 🚀 Ready to Deploy!

After following these steps, your ChapChap project will be:
- ✅ Secure (no sensitive data in git)
- ✅ Ready for team collaboration
- ✅ Properly configured for deployment
- ✅ Following best practices

Your API keys and secrets will remain private while your code can be safely shared on GitHub! 