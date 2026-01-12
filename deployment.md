# Trinity Training Guide - Hostinger VPS Deployment Guide

This guide walks you through deploying the Flask application to a Hostinger VPS with MySQL.

## Prerequisites

- Hostinger VPS with Ubuntu (20.04 or 22.04 recommended)
- SSH access to your VPS
- Domain name (optional, can use IP address)
- Local development environment with the app running

## Part 1: Export Data from Local SQLite

Run this on your **local machine** before deploying:

```bash
# Navigate to your project directory
cd Trinity-Training-Guide_main

# Export all data to JSON files
python export_data.py

# This creates an 'exports' folder with JSON files for each table
```

## Part 2: Initial VPS Setup

SSH into your Hostinger VPS:

```bash
ssh root@your-vps-ip
```

### 2.1 Update System

```bash
apt update && apt upgrade -y
```

### 2.2 Install Required Packages

```bash
apt install -y python3 python3-pip python3-venv nginx mysql-server git
```

### 2.3 Create Application User

```bash
# Create a non-root user for the app
useradd -m -s /bin/bash trinity
usermod -aG sudo trinity

# Set password
passwd trinity
```

## Part 3: MySQL Setup

### 3.1 Secure MySQL Installation

```bash
mysql_secure_installation
```

Follow the prompts:
- Set root password: Yes
- Remove anonymous users: Yes
- Disallow root login remotely: Yes
- Remove test database: Yes
- Reload privilege tables: Yes

### 3.2 Create Database and User

```bash
mysql -u root -p
```

Run these SQL commands:

```sql
-- Create database
CREATE DATABASE trinity_training CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (replace 'your_secure_password' with a strong password)
CREATE USER 'trinity_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON trinity_training.* TO 'trinity_user'@'localhost';
FLUSH PRIVILEGES;

-- Verify
SHOW DATABASES;
SELECT User, Host FROM mysql.user;

EXIT;
```

## Part 4: Deploy Application

### 4.1 Clone Repository

```bash
# Switch to trinity user
su - trinity

# Create app directory
mkdir -p /home/trinity/apps
cd /home/trinity/apps

# Clone your repository (replace with your actual repo URL)
git clone https://github.com/your-username/Trinity-Training-Guide.git
cd Trinity-Training-Guide
```

### 4.2 Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Configure Environment Variables

```bash
# Copy template
cp .env.production.template .env

# Edit with your values
nano .env
```

Update these values in `.env`:

```
FLASK_ENV=production
SECRET_KEY=generate-a-random-32-char-string
DATABASE_URI=mysql+pymysql://trinity_user:your_secure_password@localhost:3306/trinity_training
PREVIEW_MODE_PASSWORD=your-preview-password
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4.4 Initialize Database Tables

```bash
source venv/bin/activate
python init_db.py
```

### 4.5 Import Data

Upload the `exports` folder from your local machine:

```bash
# From your LOCAL machine:
scp -r exports trinity@your-vps-ip:/home/trinity/apps/Trinity-Training-Guide/
```

Then on the VPS:

```bash
cd /home/trinity/apps/Trinity-Training-Guide
source venv/bin/activate
python import_data.py --input exports --create-tables
```

### 4.6 Test Application

```bash
# Quick test
python -c "from main import app; print('App loads successfully')"

# Run development server to verify
python main.py
# Press Ctrl+C to stop
```

## Part 5: Set Up Gunicorn (Production Server)

### 5.1 Test Gunicorn

```bash
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 main:app
# Press Ctrl+C to stop
```

### 5.2 Create Systemd Service

Switch to root:
```bash
exit  # Back to root
```

Create service file:
```bash
nano /etc/systemd/system/trinity.service
```

Add this content:

```ini
[Unit]
Description=Trinity Training Guide Flask Application
After=network.target mysql.service

[Service]
User=trinity
Group=trinity
WorkingDirectory=/home/trinity/apps/Trinity-Training-Guide
Environment="PATH=/home/trinity/apps/Trinity-Training-Guide/venv/bin"
EnvironmentFile=/home/trinity/apps/Trinity-Training-Guide/.env
ExecStart=/home/trinity/apps/Trinity-Training-Guide/venv/bin/gunicorn --workers 3 --bind unix:/home/trinity/apps/Trinity-Training-Guide/trinity.sock main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl daemon-reload
systemctl enable trinity
systemctl start trinity
systemctl status trinity
```

## Part 6: Configure Nginx

### 6.1 Create Nginx Configuration

```bash
nano /etc/nginx/sites-available/trinity
```

Add this content (replace `yourdomain.com` with your domain or server IP):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://unix:/home/trinity/apps/Trinity-Training-Guide/trinity.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/trinity/apps/Trinity-Training-Guide/static;
        expires 30d;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 6.2 Enable Site

```bash
ln -s /etc/nginx/sites-available/trinity /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
nginx -t

# Restart nginx
systemctl restart nginx
```

## Part 7: SSL Certificate (HTTPS)

### 7.1 Install Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### 7.2 Obtain Certificate

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to configure HTTPS.

### 7.3 Auto-Renewal

Certbot sets up auto-renewal automatically. Test it:

```bash
certbot renew --dry-run
```

## Part 8: Firewall Setup

```bash
# Allow SSH, HTTP, HTTPS
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# Verify
ufw status
```

## Maintenance Commands

### View Application Logs

```bash
journalctl -u trinity -f
```

### Restart Application

```bash
systemctl restart trinity
```

### Update Application

```bash
su - trinity
cd /home/trinity/apps/Trinity-Training-Guide
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
exit
systemctl restart trinity
```

### Database Backup

```bash
mysqldump -u trinity_user -p trinity_training > backup_$(date +%Y%m%d).sql
```

### Database Restore

```bash
mysql -u trinity_user -p trinity_training < backup_file.sql
```

## Troubleshooting

### Check Service Status

```bash
systemctl status trinity
systemctl status nginx
systemctl status mysql
```

### Check Logs

```bash
# Application logs
journalctl -u trinity --since "1 hour ago"

# Nginx error logs
tail -f /var/log/nginx/error.log

# MySQL logs
tail -f /var/log/mysql/error.log
```

### Test Database Connection

```bash
su - trinity
cd /home/trinity/apps/Trinity-Training-Guide
source venv/bin/activate
python test_db_connection.py
```

### Permission Issues

```bash
# Fix socket permissions
chown trinity:www-data /home/trinity/apps/Trinity-Training-Guide
chmod 755 /home/trinity/apps
```

## Quick Reference

| Task | Command |
|------|---------|
| Start app | `systemctl start trinity` |
| Stop app | `systemctl stop trinity` |
| Restart app | `systemctl restart trinity` |
| View logs | `journalctl -u trinity -f` |
| MySQL console | `mysql -u trinity_user -p trinity_training` |
| Nginx reload | `systemctl reload nginx` |
| Check status | `systemctl status trinity nginx mysql` |
