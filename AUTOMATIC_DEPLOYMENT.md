# Automatic Deployment Guide

## How DigitalOcean App Platform Works

When you push to GitHub, DigitalOcean automatically:
1. ✅ Detects the push
2. ✅ Clones your repository
3. ✅ Builds your app (installs dependencies)
4. ✅ Deploys to production
5. ✅ Your site updates automatically!

## Current Setup Issue

Your build command is trying to run database migrations during build, but the database isn't accessible from the build environment.

## Quick Fix

### In DigitalOcean App Platform Dashboard:

1. Go to your app
2. Click **Settings** → **App-Level Settings**
3. Find **Build Command** or **Custom Build Command**
4. Change it from:
   ```
   pip install -r requirements.txt && pip install gunicorn psycopg2-binary && python migrate_users_schema.py && python db_migration.py
   ```
   
   To just:
   ```
   pip install -r requirements.txt
   ```

5. Save changes
6. Push a new commit to trigger rebuild:
   ```powershell
   git commit --allow-empty -m "Fix build command"
   git push origin main
   ```

## After Fix: Your Workflow

### For Code Changes (Automatic):
```powershell
# 1. Make changes locally
# 2. Test locally
# 3. Commit and push
git add .
git commit -m "Update main.py"
git push origin main

# 4. DigitalOcean automatically deploys!
# 5. Check your site - changes are live!
```

### For Database Changes (Manual):
```powershell
# 1. Update local SQLite database
# 2. Sync to production
python sync_to_production.py --skip-users

# 3. Code changes deploy automatically via git push
```

## One-Time Database Setup

After fixing the build command, run migrations once:

**In DigitalOcean App Platform Console:**
1. Go to your app → **Console** tab
2. Run:
   ```bash
   python migrate_users_schema.py --apply
   python db_migration.py
   ```

Or use the scripts with skip flag (they'll exit gracefully if DB unavailable):
```bash
python migrate_users_schema.py --skip-if-unavailable
python db_migration.py --skip-if-unavailable
```

## Verification

After fixing:
1. ✅ Build succeeds (no database connection errors)
2. ✅ App deploys successfully
3. ✅ Site is accessible
4. ✅ Code changes deploy automatically on git push

## Troubleshooting

### Build Still Failing?
- Check build logs in DigitalOcean dashboard
- Verify `requirements.txt` syntax is correct
- Make sure Python version matches (check `runtime.txt`)

### App Deployed But Database Errors?
- Run migrations manually (see One-Time Setup above)
- Verify `DATABASE_URI` environment variable is set in App Platform

### Changes Not Showing?
- Check deployment logs in DigitalOcean
- Verify git push succeeded
- Wait 1-2 minutes for deployment to complete

## Summary

**The Fix:** Remove database migrations from build command  
**The Result:** Automatic deployments on every GitHub push  
**Database Updates:** Use `sync_to_production.py` when needed

Your deployment is now fully automated! 🚀

