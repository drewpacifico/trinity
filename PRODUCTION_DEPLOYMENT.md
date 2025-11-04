# Production Deployment Guide
## Deploy to Digital Ocean with PostgreSQL & Custom Domain

This guide will walk you through deploying your training app to production using GitHub, Digital Ocean, and a custom domain.

---

## 📋 Prerequisites

Before you begin, make sure you have:

- ✅ GitHub account
- ✅ Digital Ocean account
- ✅ Domain name purchased (e.g., from Namecheap, GoDaddy, Google Domains)
- ✅ All code committed to your local Git repository
- ✅ Local version tested and working

**Estimated Time:** 60-90 minutes  
**Cost:** ~$12-18/month (Digital Ocean droplet + managed database)

---

## Phase 1: Push Code to GitHub (10 minutes)

### Step 1.1: Create GitHub Repository

1. Go to https://github.com
2. Click the **+** icon → **New repository**
3. Name it: `trinity-training-guide` (or your preferred name)
4. Choose **Private** (recommended for business apps)
5. **Don't** initialize with README (you already have code)
6. Click **Create repository**

### Step 1.2: Push Your Code

Open terminal/PowerShell in your project folder:

```bash
# Initialize git if you haven't already
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - training app ready for production"

# Connect to GitHub (replace YOUR-USERNAME and YOUR-REPO)
git remote add origin https://github.com/YOUR-USERNAME/trinity-training-guide.git

# Push to GitHub
git branch -M main
git push -u origin main
```

✅ **Verify:** Visit your GitHub repository - you should see all your files!

---

## Phase 2: Set Up Digital Ocean Managed PostgreSQL (15 minutes)

### Step 2.1: Create PostgreSQL Database

1. Log into Digital Ocean: https://cloud.digitalocean.com
2. Click **Create** → **Databases**
3. Select **PostgreSQL** (version 14 or 15)
4. Choose a plan:
   - **Basic** plan: $15/month (1 GB RAM, 10 GB storage) - good for small teams
   - **Recommended:** Start with Basic, can upgrade later
5. Choose datacenter region: Pick closest to your users (e.g., New York, San Francisco)
6. Choose database name: `training-guide-db`
7. Click **Create Database Cluster**

⏱️ Database creation takes ~5-10 minutes

### Step 2.2: Configure Database Settings

While waiting for database:

1. Once created, click on your database cluster
2. Go to **Users & Databases** tab
3. Database user `doadmin` is created automatically
4. Click **Add database** button
5. Name it: `training_guide`
6. Click **Save**

### Step 2.3: Get Connection String

1. Click on **Connection Details**
2. Select **Connection string**
3. Copy the connection string - looks like:
   ```
   postgresql://doadmin:PASSWORD@db-postgresql-nyc1-12345.ondigitalocean.com:25060/training_guide?sslmode=require
   ```
4. **Save this somewhere safe** - you'll need it soon!

---

## Phase 3: Create Digital Ocean Droplet (Server) (10 minutes)

### Step 3.1: Create Droplet

1. Click **Create** → **Droplets**
2. Choose image: **Ubuntu 22.04 LTS**
3. Choose plan:
   - **Basic** → **Regular** 
   - **$6/month** (1 GB RAM, 25 GB SSD) - sufficient for small teams
   - Can upgrade later if needed
4. Choose datacenter: **Same region as your database** (important!)
5. Authentication: Choose **SSH keys** (recommended) or **Password**
6. Hostname: `training-app-server`
7. Click **Create Droplet**

⏱️ Droplet creation takes ~1 minute

### Step 3.2: Connect to Droplet

Copy your droplet's IP address (e.g., `164.90.123.45`)

**On Windows (PowerShell or use PuTTY):**
```bash
ssh root@YOUR_DROPLET_IP
```

**On Mac/Linux:**
```bash
ssh root@YOUR_DROPLET_IP
```

Type `yes` when asked about authenticity, then enter your password if using password auth.

✅ You should now see the Ubuntu command prompt!

---

## Phase 4: Set Up Server Environment (15 minutes)

Copy and paste these commands one by one:

### Step 4.1: Update System

```bash
# Update package list
apt update

# Upgrade packages
apt upgrade -y
```

### Step 4.2: Install Python and Dependencies

```bash
# Install Python 3.11
apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx (web server)
apt install nginx -y

# Install Git
apt install git -y

# Install PostgreSQL client (for connecting to database)
apt install postgresql-client -y
```

### Step 4.3: Create Application User

```bash
# Create a user for running the app (security best practice)
adduser --disabled-password --gecos "" appuser

# Switch to app user
su - appuser
```

### Step 4.4: Clone Your Repository

```bash
# Clone from GitHub (replace with your repo URL)
git clone https://github.com/YOUR-USERNAME/trinity-training-guide.git

# Enter directory
cd trinity-training-guide

# Verify files are there
ls -la
```

You should see your files: `main.py`, `models.py`, `requirements.txt`, etc.

---

## Phase 5: Configure Application (10 minutes)

### Step 5.1: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 5.2: Install Requirements

```bash
# Install all Python packages
pip install -r requirements.txt

# Install production server (Gunicorn)
pip install gunicorn

# Install PostgreSQL adapter
pip install psycopg2-binary
```

### Step 5.3: Set Environment Variables

```bash
# Create environment file
nano .env
```

Paste this content (replace with your actual values):

```bash
# Database connection (paste your connection string from Step 2.3)
DATABASE_URL=postgresql://doadmin:PASSWORD@db-postgresql-nyc1-12345.ondigitalocean.com:25060/training_guide?sslmode=require

# Flask secret key (generate a random string)
SECRET_KEY=your-very-secret-random-string-here-change-this

# Environment
FLASK_ENV=production
```

**To generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### Step 5.4: Load Environment Variables

```bash
# Install python-dotenv if not in requirements
pip install python-dotenv

# Test connection
export $(cat .env | xargs)
python3 -c "import os; print('DB URL:', os.environ.get('DATABASE_URL')[:30] + '...')"
```

---

## Phase 6: Initialize Database (10 minutes)

### Step 6.1: Run Database Initialization

```bash
# Initialize database schema
python init_db.py

# You should see: ✅ Database initialized successfully!
```

### Step 6.2: Run Migration (Import Content)

```bash
# Migrate all content from project.md and quiz questions
python db_migration.py

# This may take 1-2 minutes
# You should see progress messages for chapters, modules, quizzes, glossary
```

### Step 6.3: Verify Database

```bash
# Check that data loaded correctly
python3 << EOF
from flask import Flask
from models import db, Chapter, Module, QuizQuestion
from config import ProductionConfig
import os

app = Flask(__name__)
app.config.from_object(ProductionConfig)
db.init_app(app)

with app.app_context():
    chapters = Chapter.query.count()
    modules = Module.query.count()
    quizzes = QuizQuestion.query.count()
    print(f"✅ Chapters: {chapters}")
    print(f"✅ Modules: {modules}")
    print(f"✅ Quiz Questions: {quizzes}")
EOF
```

You should see counts for chapters, modules, and quizzes!

---

## Phase 7: Set Up Gunicorn (Production Server) (10 minutes)

### Step 7.1: Test Gunicorn

```bash
# Test that Gunicorn can run your app
gunicorn --bind 0.0.0.0:8000 main:app

# You should see: [INFO] Listening at: http://0.0.0.0:8000
```

Press `Ctrl+C` to stop it.

### Step 7.2: Create Systemd Service (Auto-start on boot)

Exit back to root user:
```bash
exit  # Exit from appuser
```

Now as root, create the service file:

```bash
nano /etc/systemd/system/training-app.service
```

Paste this content:

```ini
[Unit]
Description=Training Guide Application
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/home/appuser/trinity-training-guide
Environment="PATH=/home/appuser/trinity-training-guide/venv/bin"
EnvironmentFile=/home/appuser/trinity-training-guide/.env
ExecStart=/home/appuser/trinity-training-guide/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 main:app

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 7.3: Enable and Start Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable training-app

# Start service now
systemctl start training-app

# Check status
systemctl status training-app

# You should see "active (running)" in green!
```

---

## Phase 8: Configure Nginx (Web Server) (10 minutes)

### Step 8.1: Remove Default Site

```bash
# Remove default Nginx site
rm /etc/nginx/sites-enabled/default
```

### Step 8.2: Create Nginx Configuration

```bash
# Create new site config (replace yourdomain.com with your actual domain)
nano /etc/nginx/sites-available/training-app
```

Paste this (replace `yourdomain.com` with your actual domain):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/appuser/trinity-training-guide/static;
        expires 30d;
    }
}
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 8.3: Enable Site

```bash
# Create symbolic link
ln -s /etc/nginx/sites-available/training-app /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# You should see: "syntax is ok" and "test is successful"

# Restart Nginx
systemctl restart nginx

# Check status
systemctl status nginx
```

---

## Phase 9: Configure Domain Name (5 minutes)

### Step 9.1: Point Domain to Droplet

Go to your domain registrar (Namecheap, GoDaddy, etc.):

1. Find **DNS Management** or **DNS Settings**
2. Add/Edit these records:

**A Record:**
- **Type:** A
- **Host:** @ (or blank)
- **Value:** Your Droplet IP (e.g., `164.90.123.45`)
- **TTL:** 300 (5 minutes)

**CNAME Record:**
- **Type:** CNAME
- **Host:** www
- **Value:** yourdomain.com (your main domain)
- **TTL:** 300

3. Save changes

⏱️ **Wait 5-60 minutes** for DNS propagation (usually ~10 minutes)

### Step 9.2: Test Domain

After waiting, visit your domain:
```
http://yourdomain.com
```

You should see your login page! 🎉

---

## Phase 10: Set Up SSL (HTTPS) (10 minutes)

### Step 10.1: Install Certbot

```bash
# Install Certbot (Let's Encrypt)
apt install certbot python3-certbot-nginx -y
```

### Step 10.2: Get SSL Certificate

```bash
# Get certificate (replace with your domain and email)
certbot --nginx -d yourdomain.com -d www.yourdomain.com --email your-email@example.com --agree-tos --non-interactive --redirect
```

This will:
- Get a free SSL certificate
- Automatically configure Nginx
- Redirect HTTP → HTTPS

✅ **Test:** Visit `https://yourdomain.com` - you should see the 🔒 lock icon!

### Step 10.3: Set Up Auto-Renewal

```bash
# Test auto-renewal
certbot renew --dry-run

# You should see: "Congratulations, all simulated renewals succeeded"
```

Certbot automatically sets up a cron job for renewal. No action needed!

---

## Phase 11: Final Configuration & Security (10 minutes)

### Step 11.1: Set Up Firewall

```bash
# Enable UFW firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# Type 'y' when prompted

# Check status
ufw status

# You should see: 22/tcp, 80/tcp, 443/tcp ALLOW
```

### Step 11.2: Create Backup Script

```bash
# Create backup directory
mkdir -p /home/appuser/backups

# Create backup script
nano /home/appuser/backup.sh
```

Paste:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/appuser/backups"

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql"
```

Save and make executable:

```bash
chmod +x /home/appuser/backup.sh
chown appuser:appuser /home/appuser/backup.sh

# Test backup
su - appuser -c "/home/appuser/backup.sh"
```

### Step 11.3: Set Up Automatic Daily Backups

```bash
# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/appuser/backup.sh") | crontab -u appuser -
```

---

## ✅ Deployment Complete!

Your app is now live at: **https://yourdomain.com**

### What You Have:

✅ Production app running on Digital Ocean  
✅ PostgreSQL database  
✅ SSL certificate (HTTPS)  
✅ Custom domain  
✅ Auto-restart on server reboot  
✅ Daily backups  
✅ Firewall protection  

---

## 🔄 Updating Your App (Future Updates)

When you make changes to your code:

### On Your Local Machine:

```bash
# Make your changes
# Test locally
# Commit changes
git add .
git commit -m "Added new feature"
git push
```

### On Your Server:

```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Switch to app user
su - appuser

# Go to app directory
cd trinity-training-guide

# Pull latest code
git pull

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart app
exit  # Back to root
systemctl restart training-app
```

Changes go live immediately! ⚡

---

## 📊 Monitoring & Maintenance

### Check App Status

```bash
systemctl status training-app
```

### View App Logs

```bash
# Real-time logs
journalctl -u training-app -f

# Last 100 lines
journalctl -u training-app -n 100
```

### Check Nginx Logs

```bash
# Error log
tail -f /var/log/nginx/error.log

# Access log
tail -f /var/log/nginx/access.log
```

### Restart Services

```bash
# Restart app
systemctl restart training-app

# Restart Nginx
systemctl restart nginx

# Restart both
systemctl restart training-app nginx
```

---

## 🆘 Troubleshooting

### Problem: "502 Bad Gateway"

**Solution:**
```bash
# Check if app is running
systemctl status training-app

# If not running, check logs
journalctl -u training-app -n 50

# Restart app
systemctl restart training-app
```

### Problem: "Can't connect to database"

**Solution:**
```bash
# Verify environment variables
su - appuser
cd trinity-training-guide
cat .env | grep DATABASE_URL

# Test database connection
psql "$DATABASE_URL" -c "SELECT 1;"
```

### Problem: "SSL certificate not working"

**Solution:**
```bash
# Renew certificate
certbot renew --force-renewal

# Restart Nginx
systemctl restart nginx
```

### Problem: "Domain not working"

**Solution:**
1. Check DNS propagation: https://dnschecker.org
2. Verify A record points to correct IP
3. Wait up to 48 hours for full propagation
4. Check Nginx config: `nginx -t`

---

## 💰 Cost Breakdown

**Monthly Costs:**

- Droplet (1 GB RAM): **$6/month**
- Managed PostgreSQL (Basic): **$15/month**
- Domain name: **~$12/year** ($1/month)
- SSL certificate: **FREE** (Let's Encrypt)

**Total: ~$22/month**

### Cost Optimization:

- Start with $6 droplet, upgrade if needed
- Consider shared database initially (~$15 → ~$7 with DO Postgres shared)
- Use single droplet with local PostgreSQL: **~$12/month total** (less reliable)

---

## 📈 Scaling Up (When You Grow)

### More Users (100+ concurrent)

1. Upgrade droplet to 2 GB RAM ($12/month)
2. Increase Gunicorn workers: `--workers 5`

### More Database Queries

1. Upgrade database plan to larger size
2. Add Redis caching layer
3. Optimize database queries

### Multiple Servers (High Availability)

1. Add load balancer
2. Deploy multiple droplets
3. Use managed PostgreSQL cluster

---

## 🔐 Security Checklist

✅ Firewall enabled (UFW)  
✅ Non-root user for app  
✅ SSL/HTTPS enabled  
✅ Database connection over SSL  
✅ Environment variables secure  
✅ Daily backups configured  
✅ Strong SECRET_KEY set  

### Additional Recommendations:

- Set up fail2ban (blocks brute force attacks)
- Enable Digital Ocean monitoring
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Regular security updates: `apt update && apt upgrade`

---

## 📞 Getting Help

**Digital Ocean Documentation:**
- https://docs.digitalocean.com

**Flask Deployment:**
- https://flask.palletsprojects.com/en/latest/deploying/

**Let's Encrypt:**
- https://letsencrypt.org/docs/

**Community:**
- Digital Ocean Community Forums
- Stack Overflow
- Reddit: r/webdev, r/flask

---

## 🎉 You're Live!

Congratulations! Your training app is now running in production.

**Share your URL with your team:**
- https://yourdomain.com

**What's Next?**
- Add more quiz questions (use `import_quizzes.py`)
- Monitor usage and performance
- Gather user feedback
- Iterate and improve!

**Good luck! 🚀**

