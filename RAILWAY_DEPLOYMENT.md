# Railway Deployment Guide

## Prerequisites
1. Create a Railway account at https://railway.app
2. Install Railway CLI (optional): `npm install -g @railway/cli`

## Deployment Steps

### 1. Create New Project on Railway
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select this repository

### 2. Add PostgreSQL Database
1. In your Railway project dashboard
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway will automatically create DATABASE_URL environment variable

### 3. Configure Environment Variables
Go to your web service → Variables tab and add these:

```
DJANGO_SETTINGS_MODULE=backend.settings.production
SECRET_KEY=your-super-secret-key-here-change-this-to-something-random
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOW_ALL_ORIGINS=True
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
RAZORPAY_KEY_ID=rzp_test_placeholder
RAZORPAY_KEY_SECRET=placeholder_secret
DJANGO_LOG_LEVEL=INFO
```

### 4. Deploy
1. Railway will automatically deploy when you push to your main branch
2. Monitor deployment in the Railway dashboard
3. Check logs for any issues

### 5. Access Your Application
- Your app will be available at: `https://your-app-name.up.railway.app`
- API docs: `https://your-app-name.up.railway.app/api/docs/`
- Admin: `https://your-app-name.up.railway.app/admin/`
- Health check: `https://your-app-name.up.railway.app/health/`

### 6. Create Superuser (After First Deployment)
1. Go to Railway dashboard → your service → Settings
2. Use the "One-Click Deploy" or connect via Railway CLI:
   ```bash
   railway login
   railway link
   railway run python manage.py createsuperuser
   ```

## Important Notes

### Free Tier Limitations
- $5 free credit per month
- Apps sleep after 30 minutes of inactivity
- 500MB RAM limit
- 1GB disk space

### Production Checklist (After Testing)
1. Generate a strong SECRET_KEY
2. Set SECURE_SSL_REDIRECT=True
3. Set SESSION_COOKIE_SECURE=True
4. Set CSRF_COOKIE_SECURE=True
5. Configure proper CORS_ALLOWED_ORIGINS
6. Set up proper email backend
7. Configure Razorpay with real keys

### Monitoring
- Use Railway's built-in metrics
- Check logs regularly: Railway dashboard → Service → Logs
- Health check endpoint: `/health/`

### Scaling
- Railway automatically handles basic scaling
- Monitor usage in dashboard
- Upgrade plan when needed

## Troubleshooting

### Common Issues
1. **Build fails**: Check requirements.txt and Dockerfile
2. **Database connection**: Ensure PostgreSQL service is running
3. **Static files**: Whitenoise should handle this automatically
4. **Environment variables**: Double-check all required vars are set

### Getting Help
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- Check Railway status: https://status.railway.app