# ChapChap Deployment Guide for Render

## Prerequisites
1. GitHub account with your ChapChap repository
2. Render account (free tier available)

## Deployment Steps

### 1. Push your code to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a new Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository (GabuGravin41/ChapChap)
4. Configure the service:
   - **Name**: chapchap
   - **Environment**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn chapchap.wsgi:application`
   - **Instance Type**: Free (or paid for better performance)

### 3. Environment Variables
Add these environment variables in Render:
- `DEBUG`: `False`
- `SECRET_KEY`: Generate a new secure key
- `TWITTER_API_KEY`: Your Twitter API key (optional)
- `FACEBOOK_APP_ID`: Your Facebook App ID (optional)
- `FACEBOOK_APP_SECRET`: Your Facebook App Secret (optional)
- `LINKEDIN_CLIENT_ID`: Your LinkedIn Client ID (optional)
- `LINKEDIN_CLIENT_SECRET`: Your LinkedIn Client Secret (optional)

### 4. Database (Optional)
For production, consider using Render's PostgreSQL:
1. Create a PostgreSQL database on Render
2. Render will automatically set the `DATABASE_URL` environment variable

### 5. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. The build process will:
   - Install dependencies
   - Collect static files
   - Run migrations
   - Create a default superuser

### 6. Access your application
- Your app will be available at: `https://chapchap.onrender.com` (or similar)
- Admin panel: `https://chapchap.onrender.com/admin/`

## Post-Deployment
1. Test all functionality
2. Set up custom domain (if desired)
3. Configure monitoring and logging
4. Set up backup strategies for your database

## Troubleshooting
- Check build logs in Render dashboard
- Ensure all environment variables are set
- Verify that build.sh is executable
- Check that all dependencies are in requirements.txt

## Production Considerations
- Use a paid Render plan for better performance
- Set up a PostgreSQL database for production
- Enable SSL/HTTPS (automatic with Render)
- Configure proper logging and monitoring
- Set up automated backups
