# 🚀 Quick Deployment Checklist

Use this as a quick reference. See `PRODUCTION_DEPLOYMENT.md` for detailed instructions.

---

## Pre-Deployment

- [ ] All code tested locally
- [ ] GitHub account ready
- [ ] Digital Ocean account created
- [ ] Domain name purchased
- [ ] Credit card added to Digital Ocean

---

## GitHub Setup (10 min)

- [ ] Create GitHub repository (private recommended)
- [ ] Push code to GitHub:
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  git remote add origin https://github.com/USERNAME/trinity-training-guide.git
  git push -u origin main
  ```

---

## Digital Ocean Database (15 min)

- [ ] Create PostgreSQL database (Basic $15/mo)
- [ ] Choose same region as your future server
- [ ] Create database named `training_guide`
- [ ] Copy connection string (save it!)
- [ ] Wait for database to finish provisioning

---

## Digital Ocean Droplet (10 min)

- [ ] Create Ubuntu 22.04 droplet ($6/mo, 1GB RAM)
- [ ] Same region as database
- [ ] Add SSH key or set password
- [ ] Note the IP address
- [ ] SSH into server: `ssh root@YOUR_IP`

---

## Server Setup (15 min)

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install python3.11 python3.11-venv python3-pip nginx git postgresql-client -y

# Create app user
adduser --disabled-password --gecos "" appuser
su - appuser

# Clone repo
git clone https://github.com/USERNAME/trinity-training-guide.git
cd trinity-training-guide

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

---

## Configuration (10 min)

- [ ] Create `.env` file:
  ```bash
  nano .env
  ```
- [ ] Add:
  ```
  DATABASE_URL=postgresql://doadmin:PASSWORD@...
  SECRET_KEY=[run: python3 -c "import secrets; print(secrets.token_hex(32))"]
  FLASK_ENV=production
  ```
- [ ] Load variables: `export $(cat .env | xargs)`

---

## Database Setup (10 min)

```bash
# Initialize database
python init_db.py

# Migrate content
python db_migration.py

# Verify
python3 -c "from flask import Flask; from models import db, Chapter; from config import ProductionConfig; app = Flask(__name__); app.config.from_object(ProductionConfig); db.init_app(app); app.app_context().push(); print('Chapters:', Chapter.query.count())"
```

---

## Gunicorn Service (10 min)

- [ ] Test: `gunicorn --bind 0.0.0.0:8000 main:app`
- [ ] Exit (`Ctrl+C`), then `exit` back to root
- [ ] Create service file:
  ```bash
  nano /etc/systemd/system/training-app.service
  ```
- [ ] Paste service configuration (see full guide)
- [ ] Enable and start:
  ```bash
  systemctl daemon-reload
  systemctl enable training-app
  systemctl start training-app
  systemctl status training-app
  ```

---

## Nginx Setup (10 min)

- [ ] Remove default site: `rm /etc/nginx/sites-enabled/default`
- [ ] Create config:
  ```bash
  nano /etc/nginx/sites-available/training-app
  ```
- [ ] Paste Nginx config with your domain (see full guide)
- [ ] Enable site:
  ```bash
  ln -s /etc/nginx/sites-available/training-app /etc/nginx/sites-enabled/
  nginx -t
  systemctl restart nginx
  ```

---

## Domain Configuration (5 min)

In your domain registrar (Namecheap, GoDaddy, etc.):

- [ ] Add A record: `@` → Your Droplet IP
- [ ] Add CNAME record: `www` → yourdomain.com
- [ ] Wait 10-60 minutes for DNS propagation
- [ ] Test: Visit `http://yourdomain.com`

---

## SSL Certificate (10 min)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain/email)
certbot --nginx -d yourdomain.com -d www.yourdomain.com --email your@email.com --agree-tos --non-interactive --redirect

# Test renewal
certbot renew --dry-run
```

- [ ] Visit `https://yourdomain.com` - should see 🔒

---

## Security (10 min)

```bash
# Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status

# Backup script
mkdir -p /home/appuser/backups
nano /home/appuser/backup.sh
```

- [ ] Paste backup script (see full guide)
- [ ] Make executable: `chmod +x /home/appuser/backup.sh`
- [ ] Set up cron: 
  ```bash
  (crontab -l 2>/dev/null; echo "0 2 * * * /home/appuser/backup.sh") | crontab -u appuser -
  ```

---

## ✅ Final Verification

- [ ] Visit `https://yourdomain.com` - login page loads
- [ ] Create test account
- [ ] Navigate through a module
- [ ] Answer a quiz question
- [ ] Check logout button works
- [ ] Check `systemctl status training-app` - shows "active (running)"
- [ ] Check `systemctl status nginx` - shows "active (running)"

---

## 🎉 LIVE!

**Your app is now running at:** `https://yourdomain.com`

**Costs:** ~$22/month
- Droplet: $6/mo
- Database: $15/mo
- Domain: ~$1/mo
- SSL: FREE

---

## Quick Commands Reference

```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Check app status
systemctl status training-app

# View app logs
journalctl -u training-app -f

# Restart app
systemctl restart training-app

# Update app (after pushing to GitHub)
su - appuser
cd trinity-training-guide
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
systemctl restart training-app
```

---

## Need Help?

📖 See `PRODUCTION_DEPLOYMENT.md` for detailed instructions  
🔍 Check troubleshooting section in full guide  
💬 Digital Ocean Community: https://www.digitalocean.com/community

---

**Total Time:** ~90 minutes  
**Difficulty:** Intermediate  
**Result:** Production app with SSL on custom domain! 🚀

