# Deployment Instructions for MEKAN Admin Interface

## Deploying to Render (Free Hosting)

This application is configured to deploy on Render's free tier. Follow these steps:

### 1. Prerequisites
- GitHub account
- Render account (sign up at https://render.com)
### 2. Push Code to GitHub

First, create a new GitHub repository and push your code:

```bash
cd /Users/enzo/Desktop/SYSTEM_Hybrid_Kultepe/admin_interface
git init
git add .
git commit -m "Initial commit - MEKAN Admin Interface"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mekan-admin.git
git push -u origin main
```

### 3. Deploy on Render

1. Go to https://dashboard.render.com
2. Click "New +" and select "Web Service"
3. Connect your GitHub account if not already connected
4. Select your `mekan-admin` repository
5. Configure the service:
   - **Name**: mekan-admin (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free

6. The environment variables are already configured in `render.yaml`, but you can also set them manually in the Render dashboard if needed:
   - `SECRET_KEY`: (auto-generated)
   - `POSTGRES_HOST`: aws-0-eu-central-1.pooler.supabase.com
   - `POSTGRES_PORT`: 5432
   - `POSTGRES_DATABASE`: postgres
   - `POSTGRES_USER`: postgres.ctlqtgwyuknxpkssidcd
   - `POSTGRES_PASSWORD`: 6pRZELCQUoGFIcf

7. Click "Create Web Service"

### 4. Access Your Application

After deployment (usually takes 2-5 minutes), your application will be available at:
```
https://mekan-admin.onrender.com
```
(The exact URL will be shown in your Render dashboard)

### Default Login Credentials
- Username: `admin`
- Password: `admin123`

⚠️ **Important**: Change the admin password immediately after first login!

### 5. Monitoring

- View logs in the Render dashboard
- The free tier includes 750 hours/month
- The app may spin down after 15 minutes of inactivity (cold starts)

## Alternative: Railway Deployment

If you prefer Railway (also has a free tier):

1. Install Railway CLI:
```bash
brew install railway
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Deploy:
```bash
railway up
```

4. Add environment variables in Railway dashboard

## Features Available Online

Once deployed, you'll have access to:
- User authentication and management
- Archaeological data viewing (MEKAN, Birim, Walls, Graves, Finds)
- Parent-child relationship navigation
- Media indicators (green = has photos, gray = no photos)
- Statistics and visualizations
- Activity logging

## Troubleshooting

If you encounter issues:
1. Check Render logs for errors
2. Verify database connection (Supabase must allow connections from Render IPs)
3. Ensure all environment variables are correctly set
4. Check that the Python version matches (3.11.6)

## Security Notes

- Change default admin password immediately
- Consider using environment variables for sensitive data
- Enable HTTPS (automatic on Render)
- Regularly update dependencies