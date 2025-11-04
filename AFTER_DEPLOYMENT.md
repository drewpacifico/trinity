# After Deployment - Next Steps & Maintenance

Your app is live! 🎉 Here's what to do next and how to maintain it.

---

## 🎯 Immediate Post-Deployment Tasks

### 1. Create Admin/Preview Account (5 minutes)

Visit: `https://yourdomain.com/preview`

This will:
- ✅ Create a `preview_user` account
- ✅ Enable preview mode (all content unlocked)
- ✅ Let you verify everything works

**Test thoroughly:**
- [ ] Navigate through all 6 chapters
- [ ] Complete several quiz questions
- [ ] Check glossary page
- [ ] Test logout and login again
- [ ] Try on mobile device
- [ ] Test in different browsers

### 2. Create Your First Real User

Visit: `https://yourdomain.com`

- [ ] Enter your name/username
- [ ] Complete Module 1.1 as a test
- [ ] Verify progress saves correctly
- [ ] Log out and log back in - progress should persist

### 3. Set Up Monitoring (10 minutes)

**Free Uptime Monitoring:**

1. **UptimeRobot** (https://uptimerobot.com)
   - Create free account
   - Add monitor: `https://yourdomain.com`
   - Set check interval: 5 minutes
   - Add your email for alerts
   - ✅ Get notified if site goes down!

2. **Digital Ocean Monitoring** (built-in)
   - Go to your droplet in DO dashboard
   - Click "Enable Monitoring"
   - View CPU, memory, disk usage graphs
   - Set up alerts for high resource usage

### 4. Document Admin Access (5 minutes)

Create a secure note with:
- 🔑 Digital Ocean login
- 🔑 GitHub repository URL
- 🔑 Domain registrar login
- 🔑 Server IP address: `YOUR_IP`
- 🔑 SSH connection: `ssh root@YOUR_IP`
- 🔑 Database connection string
- 📧 Email used for SSL certificate

**Store securely:** Use password manager (1Password, LastPass, Bitwarden)

---

## 📊 Daily Operations

### Checking Site Health

**Quick health check (30 seconds):**
```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Check everything is running
systemctl status training-app nginx

# Should see: ● training-app.service - Training Guide Application
#             Active: active (running)

# Exit
exit
```

### Viewing User Activity

**Check how many users signed up:**
```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide
source venv/bin/activate

python3 << EOF
from flask import Flask
from models import db, User
from config import ProductionConfig
import os

app = Flask(__name__)
app.config.from_object(ProductionConfig)
db.init_app(app)

with app.app_context():
    total_users = User.query.count()
    regular_users = User.query.filter_by(is_preview_mode=False).count()
    print(f"Total users: {total_users}")
    print(f"Regular users: {regular_users}")
    
    # Recent users
    print("\nRecent 5 users:")
    recent = User.query.order_by(User.created_at.desc()).limit(5).all()
    for user in recent:
        print(f"  - {user.username} (created: {user.created_at.strftime('%Y-%m-%d')})")
EOF
```

---

## 🔄 Making Updates

### Adding New Quiz Questions (AI-Generated)

**On your local machine:**

1. Generate questions with AI (see `AI_QUIZ_WORKFLOW.md`)
2. Save to file: `new_quiz.txt`
3. Test import locally:
   ```bash
   python import_quizzes.py
   # Choose option 3, enter: new_quiz.txt
   ```
4. Commit to GitHub:
   ```bash
   git add new_quiz.txt
   git commit -m "Added Module 7.1 quiz questions"
   git push
   ```

**On your server:**

```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide
git pull
source venv/bin/activate
python import_quizzes.py
# Choose option 3, enter: new_quiz.txt
```

Done! New questions are live instantly. ✨

### Updating Code/Features

**On your local machine:**

1. Make changes to code
2. Test thoroughly locally
3. Commit and push:
   ```bash
   git add .
   git commit -m "Fixed bug in quiz navigation"
   git push
   ```

**On your server:**

```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide

# Pull latest code
git pull

# Activate environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Exit back to root
exit

# Restart app (as root)
systemctl restart training-app

# Verify it's running
systemctl status training-app
```

**Changes are live!** ⚡

### Emergency Rollback

If an update breaks something:

```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide

# Go back to previous commit
git log  # Find the commit hash
git checkout PREVIOUS_COMMIT_HASH

exit
systemctl restart training-app
```

---

## 🗄️ Database Management

### Backup Database Manually

```bash
ssh root@YOUR_DROPLET_IP
su - appuser

# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Download to your computer (from your local machine)
# scp appuser@YOUR_DROPLET_IP:/home/appuser/backup_*.sql ./backups/
```

### Restore from Backup

```bash
ssh root@YOUR_DROPLET_IP
su - appuser

# Restore from backup file
psql $DATABASE_URL < backup_20240115.sql
```

### View Database Directly

```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide

# Connect to database
psql $DATABASE_URL

# Useful queries:
# SELECT * FROM users;
# SELECT * FROM quiz_questions WHERE module_id = '7.1';
# SELECT COUNT(*) FROM user_quiz_answers;

# Exit database
\q
```

### Reset User Progress (Admin Task)

```bash
ssh root@YOUR_DROPLET_IP
su - appuser
cd trinity-training-guide
source venv/bin/activate

python3 << EOF
from flask import Flask
from models import db, User, UserQuizAnswer, UserProgress
from config import ProductionConfig

app = Flask(__name__)
app.config.from_object(ProductionConfig)
db.init_app(app)

with app.app_context():
    # Reset specific user
    username = input("Enter username to reset: ")
    user = User.query.filter_by(username=username).first()
    
    if user:
        UserQuizAnswer.query.filter_by(user_id=user.id).delete()
        UserProgress.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        print(f"✅ Reset progress for {username}")
    else:
        print(f"❌ User {username} not found")
EOF
```

---

## 📈 Scaling & Performance

### When to Upgrade

**Upgrade Droplet if:**
- CPU consistently > 80% (check DO monitoring)
- Memory > 90% used
- App feels slow
- Supporting 50+ concurrent users

**Upgrade Database if:**
- Queries taking > 1 second
- Database size > 8 GB
- Supporting 100+ users

### Upgrade Droplet

In Digital Ocean dashboard:
1. Click your droplet
2. Click "Resize"
3. Choose larger size (e.g., $12/mo for 2 GB RAM)
4. Click "Resize Droplet"
5. Takes ~2 minutes, minimal downtime

After resize, increase Gunicorn workers:

```bash
ssh root@YOUR_DROPLET_IP
nano /etc/systemd/system/training-app.service

# Change: --workers 3
# To: --workers 5

systemctl daemon-reload
systemctl restart training-app
```

### Add Redis Caching (Advanced)

If app still slow after upgrading:

```bash
# Install Redis
apt install redis-server -y

# Install Python Redis
su - appuser
cd trinity-training-guide
source venv/bin/activate
pip install redis flask-caching

# Update config.py to use Redis
# (See Flask-Caching documentation)
```

---

## 🔒 Security Maintenance

### Weekly Security Updates

```bash
ssh root@YOUR_DROPLET_IP

# Update packages
apt update
apt upgrade -y

# Restart if kernel updated
# (Digital Ocean will notify you)
```

### Check Failed Login Attempts

```bash
ssh root@YOUR_DROPLET_IP

# View SSH login attempts
journalctl -u ssh | grep "Failed password"

# If many failed attempts, consider fail2ban:
apt install fail2ban -y
```

### Rotate Database Password (Quarterly)

In Digital Ocean dashboard:
1. Go to your database
2. Click "Users & Databases"
3. Reset `doadmin` password
4. Update `.env` file on server with new connection string
5. Restart app: `systemctl restart training-app`

---

## 💰 Cost Optimization

### Current Costs: ~$22/month

**Ways to reduce:**

1. **Use smaller database** (~$15 → $7)
   - If < 20 users, shared database is fine
   - In DO dashboard: downgrade to shared PostgreSQL

2. **Single droplet with local PostgreSQL** (~$22 → $12)
   - Less reliable, but works for small teams
   - Install PostgreSQL on droplet instead of managed DB
   - Not recommended for production

3. **Annual domain payment** ($12/year upfront)
   - Small savings vs monthly

### Monitor Costs

Digital Ocean dashboard → Billing → View current month charges

---

## 📞 Getting Help

### Check Logs First

```bash
# App logs
ssh root@YOUR_DROPLET_IP
journalctl -u training-app -n 100

# Nginx logs
tail -f /var/log/nginx/error.log
```

### Common Issues & Solutions

**Issue: "502 Bad Gateway"**
```bash
systemctl restart training-app
```

**Issue: "Can't connect to database"**
```bash
# Check connection string
su - appuser
cat ~/trinity-training-guide/.env | grep DATABASE_URL
```

**Issue: "SSL certificate expired"**
```bash
certbot renew
systemctl restart nginx
```

**Issue: "Disk full"**
```bash
# Check disk usage
df -h

# Clean old logs
journalctl --vacuum-time=7d

# Clean old backups
find /home/appuser/backups -mtime +30 -delete
```

### Support Resources

- 📖 **Digital Ocean Docs:** https://docs.digitalocean.com
- 💬 **DO Community:** https://www.digitalocean.com/community
- 📚 **Flask Docs:** https://flask.palletsprojects.com
- 🐛 **GitHub Issues:** Create issue in your repo

---

## 📝 Maintenance Checklist

### Daily (1 minute)
- [ ] Check UptimeRobot - site is up
- [ ] Spot check: visit site, looks good

### Weekly (10 minutes)
- [ ] Check Digital Ocean monitoring - no alerts
- [ ] Review app logs: `journalctl -u training-app -n 100`
- [ ] Run security updates: `apt update && apt upgrade`
- [ ] Check backup ran successfully: `ls -lh /home/appuser/backups/`

### Monthly (30 minutes)
- [ ] Review user count and usage
- [ ] Check database size
- [ ] Review costs in DO dashboard
- [ ] Test site on mobile/desktop
- [ ] Update any Python packages: `pip install --upgrade -r requirements.txt`
- [ ] Verify SSL certificate auto-renewal: `certbot renew --dry-run`

### Quarterly (1 hour)
- [ ] Full database backup to local machine
- [ ] Review and optimize slow queries
- [ ] Consider password rotation
- [ ] Plan feature improvements based on feedback

---

## 🎓 Training Your Team

### For Content Creators (Adding Quizzes)

1. Send them: `AI_QUIZ_WORKFLOW.md`
2. Give them GitHub access
3. Show them how to use `import_quizzes.py`
4. They can add questions without touching server!

### For Admins (Managing Site)

1. Send them this file: `AFTER_DEPLOYMENT.md`
2. Give them server SSH access
3. Walk through basic commands:
   - Check status
   - View logs
   - Restart app
   - Pull updates

### For End Users (Trainees)

Create a simple guide:
- Visit https://yourdomain.com
- Enter your name (no password needed)
- Complete modules in order
- Take quizzes to unlock next content
- Your progress saves automatically

---

## 🚀 Future Enhancements

**Easy wins:**
- Add more chapters/modules
- Improve quiz questions based on feedback
- Add certificate generation on completion
- Email notifications for progress

**Medium effort:**
- Admin dashboard to view user progress
- Export progress reports to CSV
- Add discussion forum
- Gamification (points, badges)

**Advanced:**
- Video content integration
- Interactive simulations
- Mobile app
- Multi-language support

---

## ✅ You're All Set!

Your training platform is **production-ready** and **easy to maintain**.

**Key URLs:**
- 🌐 **App:** https://yourdomain.com
- 👀 **Preview Mode:** https://yourdomain.com/preview
- 🔧 **Server:** ssh root@YOUR_DROPLET_IP
- 💾 **GitHub:** https://github.com/USERNAME/trinity-training-guide

**Monthly Tasks:**
- Keep system updated
- Monitor usage
- Back up database
- Improve content

**You've got this!** 💪

Questions? Review:
- `PRODUCTION_DEPLOYMENT.md` - Full deployment guide
- `AI_QUIZ_WORKFLOW.md` - Adding quiz questions
- `deployment.md` - Database migration details

---

**Last Updated:** {{ date }}  
**App Version:** 1.0  
**Status:** ✅ Production Ready

