# Railway Deployment Guide for Shambit Travels API

## Current Issues Fixed

✅ **Root URL 404 Error** - Added root redirect to API docs  
✅ **Database Connection** - Configured Neon PostgreSQL properly  
✅ **Environment Variables** - Created Railway-specific config  
✅ **Static Files** - Configured WhiteNoise for static file serving  

## Quick Fix for Current Deployment

### 1. Set Environment Variables in Railway

Go to your Railway project dashboard and add these environment variables:

```bash
DATABASE_URL=postgresql://neondb_owner:npg_VyDnfoCEu46z@ep-solitary-cell-ahfvkw6i-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

DEBUG=False
SECRET_KEY=your-super-secret-production-key-change-this-immediately
ALLOWED_HOSTS=shambit.up.railway.app,*.railway.app

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CORS_ALLOW_ALL_ORIGINS=True

DJANGO_LOG_LEVEL=INFO
```

### 2. Generate a Strong Secret Key

Run this command locally to generate a secure secret key:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then update the `SECRET_KEY` environment variable in Railway.

### 3. Redeploy

After setting the environment variables, trigger a new deployment in Railway.

## What Was Fixed

### 1. Root URL Handler
- Added `/` route that redirects to API documentation
- Added `/api/` route with endpoint overview
- No more 404 errors on root access

### 2. Database Configuration
- Fixed production settings to handle missing DATABASE_URL gracefully
- Verified Neon database connection and tables
- All Django migrations are already applied

### 3. Environment Variables
- Created `.env.railway` with all required variables
- Updated production settings for Railway deployment
- Configured proper security settings

### 4. API Documentation
- Fixed DRF Spectacular warnings (these are just warnings, not errors)
- API docs available at `/api/docs/`
- Schema available at `/api/schema/`

## Available Endpoints

After deployment, your API will have:

- **Root**: `/` → Redirects to API docs
- **API Root**: `/api/` → Endpoint overview
- **Health Check**: `/health/` → Service status
- **Admin**: `/admin/` → Django admin
- **API Docs**: `/api/docs/` → Swagger UI
- **API Schema**: `/api/schema/` → OpenAPI schema

### API Endpoints:
- `/api/auth/` → Authentication
- `/api/cities/` → Cities and destinations
- `/api/articles/` → Travel articles
- `/api/packages/` → Travel packages
- `/api/bookings/` → Booking management
- `/api/payments/` → Payment processing
- `/api/notifications/` → User notifications
- `/api/seo/` → SEO metadata
- `/api/media/` → Media library
- `/api/pricing/` → Dynamic pricing

## Testing the Deployment

1. **Health Check**: `https://shambit.up.railway.app/health/`
2. **API Root**: `https://shambit.up.railway.app/api/`
3. **API Docs**: `https://shambit.up.railway.app/api/docs/`
4. **Admin**: `https://shambit.up.railway.app/admin/`

## Database Status

✅ **Database Connected**: Neon PostgreSQL  
✅ **Tables Created**: All Django models migrated  
✅ **Connection String**: Configured for Railway  

Your database has 35+ tables including:
- User management
- Cities and travel data
- Bookings and payments
- Media library
- SEO data
- Neon Auth integration

## Security Notes

🔒 **Important**: Update these in Railway environment variables:
- `SECRET_KEY` → Generate a new strong key
- `RAZORPAY_KEY_ID` → Your production Razorpay key
- `RAZORPAY_KEY_SECRET` → Your production Razorpay secret
- OAuth credentials for Google/GitHub if using

## Next Steps

1. **Set environment variables** in Railway dashboard
2. **Generate strong SECRET_KEY** 
3. **Redeploy** the application
4. **Test all endpoints** using the URLs above
5. **Configure OAuth** if needed for authentication
6. **Set up monitoring** for production use

## Troubleshooting

If you still see issues after setting environment variables:

1. Check Railway logs for specific errors
2. Verify DATABASE_URL is exactly as provided
3. Ensure all environment variables are set
4. Try a fresh deployment

The application should work perfectly once the environment variables are configured in Railway.