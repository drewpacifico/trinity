# Fix DigitalOcean App Platform Deployment

## Problem

Your build is failing because the custom build command tries to run database migrations during the build phase, but the database isn't accessible from the build environment.

**Current build command (WRONG):**
```
pip install -r requirements.txt && pip install gunicorn psycopg2-binary && python migrate_users_schema.py && python db_migration.py
```

## Solution

### Step 1: Fix the Build Command

In your **DigitalOcean App Platform** dashboard:

1. Go to your app → **Settings** → **App-Level Environment Variables**
2. Find the **Build Command** or **Custom Build Command** setting
3. Change it to:

```
pip install -r requirements.txt
```

**That's it!** Just install dependencies. Don't run migrations during build.

### Step 2: Run Migrations Manually (One-Time Setup)

After deployment succeeds, run migrations manually using DigitalOcean's console or SSH:

**Option A: Using DigitalOcean Console**
1. Go to your app → **Console** tab
2. Run:
   ```bash
   python migrate_users_schema.py --apply
   python db_migration.py
   ```

**Option B: Using SSH (if enabled)**
```bash
# SSH into your app
doctl apps ssh YOUR_APP_ID

# Run migrations
python migrate_users_schema.py --apply
python db_migration.py
```

### Step 3: Verify Deployment

After fixing the build command:
1. Push your code to GitHub
2. DigitalOcean will automatically rebuild
3. Build should succeed ✅
4. App will deploy ✅

## Why This Happens

- **Build phase**: Code is compiled/installed (no database access needed)
- **Runtime phase**: App runs and can access database
- Migrations need database access, so they must run at runtime, not build time

## Automatic Deployment Workflow

Once fixed, your workflow is:

1. **Make changes locally**
2. **Test locally**
3. **Commit and push to GitHub:**
   ```powershell
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
4. **DigitalOcean automatically:**
   - Detects the push
   - Builds your app
   - Deploys to production
5. **Done!** Your site updates automatically 🎉

## Database Updates

For database changes (content, quizzes, etc.):

1. **Update local SQLite database**
2. **Sync to production:**
   ```powershell
   python sync_to_production.py --skip-users
   ```
3. **Code changes deploy automatically** (via GitHub push)

## Troubleshooting

### Build Still Failing?

Check the build logs in DigitalOcean dashboard:
- Look for specific error messages
- Verify `requirements.txt` is correct
- Make sure Python version matches (check `runtime.txt` or `.python-version`)

### App Deployed But Not Working?

1. Check app logs in DigitalOcean dashboard
2. Verify environment variables are set:
   - `DATABASE_URI` (should be set in App Platform settings)
   - `FLASK_ENV=production`
   - `SECRET_KEY` (if needed)

### Database Connection Issues?

- Verify `DATABASE_URI` is correct in App Platform settings
- Check database is running in DigitalOcean dashboard
- Verify database firewall allows App Platform IPs

## Summary

**Fix:** Remove migration scripts from build command  
**Result:** Automatic deployments on every GitHub push  
**Database:** Sync manually using `sync_to_production.py` when needed

