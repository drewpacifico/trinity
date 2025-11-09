# Setting Up New Authentication System

Your training app now has a **professional registration and login system** with:
- ✅ First name, last name, employee ID fields
- ✅ Secure password hashing
- ✅ Registration page
- ✅ Updated login page with password
- ✅ New home page with Login/Register options

---

## 🚀 Setup Steps

### Step 1: Run Database Migration (5 minutes)

The database schema needs to be updated to add the new user fields.

```bash
# Stop your Flask app if it's running (Ctrl+C)

# Run the migration script
python migrate_users_schema.py
```

**What this does:**
- Adds `first_name`, `last_name`, `employee_id` columns to users table
- Makes `password_hash` required
- Updates existing users with default values
- Preserves all existing user progress and quiz answers

**Expected output:**
```
🔄 Starting user schema migration...
📊 Database: SQLite
...
✅ SQLite migration complete!
✅ Found X users in migrated table
🎉 Migration completed successfully!
```

### Step 2: Start Your App

```bash
python main.py
```

### Step 3: Test the New System

Visit: `http://localhost:5000`

You should see a **new home page** with two cards:
- 🔑 **Login** - For existing users
- 📝 **Register** - For new users

---

## ✅ Testing the Registration Flow

### Register a New User

1. Click **"Register"** on home page
2. Fill out the form:
   - **First Name:** John
   - **Last Name:** Doe
   - **Employee ID:** EMP001
   - **Username:** johndoe
   - **Email:** john@example.com (optional)
   - **Password:** TestPassword123
   - **Confirm Password:** TestPassword123
3. Click **"Create Account"**
4. You'll be automatically logged in and taken to the training content!

### Test Login

1. Logout (top right corner)
2. Go to home page
3. Click **"Login"**
4. Enter:
   - **Username:** johndoe
   - **Password:** TestPassword123
5. Click **"Sign In"**
6. Should log you in successfully!

---

## 📋 What Changed

### Database (`models.py`)
- ✅ Added `first_name`, `last_name`, `employee_id` to User model
- ✅ Made `password_hash` required
- ✅ Added `set_password()` method (hashes passwords securely)
- ✅ Added `check_password()` method (validates passwords)

### Routes (`main.py`)
- ✅ **New route:** `/` redirects to home if not logged in
- ✅ **New route:** `/home` - Landing page with Login/Register
- ✅ **New route:** `/register` - Registration form
- ✅ **Updated route:** `/login` - Now checks passwords
- ✅ **Updated route:** `/logout` - Redirects to home page

### Templates
- ✅ **New:** `templates/home.html` - Beautiful landing page
- ✅ **New:** `templates/register.html` - Registration form
- ✅ **Updated:** `templates/login.html` - Added password field

---

## 🔐 Security Features

### Password Hashing
Passwords are **never stored in plain text**. They're hashed using Werkzeug's secure password hashing:

```python
user.set_password("MyPassword123")  # Stores hash, not plain text
user.check_password("MyPassword123")  # Returns True
```

### Validation
- ✅ First name: min 2 characters
- ✅ Last name: min 2 characters
- ✅ Employee ID: min 3 characters, unique
- ✅ Username: min 3 characters, unique
- ✅ Password: min 8 characters
- ✅ Email: optional, but must be unique if provided

### Session Management
- ✅ Login required for all pages (except home, login, register)
- ✅ Sessions persist across browser restarts
- ✅ Logout clears all session data

---

## 👥 Existing Users

### What Happens to Old Users?

The migration script updates existing users with **default values**:
- `first_name` = "User"
- `last_name` = their username
- `employee_id` = "EMP" + their user ID (e.g., "EMP1", "EMP2")
- `password_hash` = "legacy_user_no_password"

**Important:** Existing users **cannot login** with old credentials!

### Solutions for Existing Users:

**Option 1: Manual Database Update** (if you have important users)
```python
python
>>> from flask import Flask
>>> from models import db, User
>>> from config import DevelopmentConfig
>>> app = Flask(__name__)
>>> app.config.from_object(DevelopmentConfig)
>>> db.init_app(app)
>>> with app.app_context():
...     user = User.query.filter_by(username='preview_user').first()
...     user.first_name = 'Preview'
...     user.last_name = 'User'
...     user.employee_id = 'PREVIEW001'
...     user.set_password('preview123')
...     db.session.commit()
```

**Option 2: Have Users Re-register** (easiest)
- They register with new form
- All their progress transfers if they use same username
- Actually, no - progress is tied to user ID, so they'd lose progress
- **Use Option 1 for important users!**

---

## 🎨 Customization

### Change Required Password Length

In `templates/register.html` and `main.py`, find:

```python
if not password or len(password) < 8:
```

Change `8` to your desired minimum length.

### Make Email Required

In `models.py`:
```python
email = db.Column(db.String(255), unique=True, nullable=False)  # Add nullable=False
```

In `main.py` register route:
```python
if not email or len(email) < 5:
    errors.append("Email is required")
```

### Custom Employee ID Format

In registration validation:
```python
import re
if not re.match(r'^EMP\d{3}$', employee_id):
    errors.append("Employee ID must be in format: EMP001")
```

---

## 🐛 Troubleshooting

### Error: "no such column: users.first_name"

**Solution:** Run the migration script:
```bash
python migrate_users_schema.py
```

### Error: "NOT NULL constraint failed: users.password_hash"

**Solution:** The migration didn't complete. Delete `training_guide.db` and run:
```bash
python init_db.py
python db_migration.py
```

Then register new users from scratch.

### Can't Login After Migration

**Solution:** Existing users have invalid passwords. Either:
1. Register a new account
2. Manually update user passwords (see "Existing Users" section above)

### Registration Form Shows Errors

Check browser console for JavaScript errors. The form has client-side validation that might conflict with server validation.

---

## 📊 Database Schema

### New `users` Table Structure:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_preview_mode BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

---

## 🚀 Production Deployment

When deploying to production (Digital Ocean), you'll need to:

1. **Run migration on production database:**
```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Switch to app user
su - appuser
cd trinity-training-guide

# Activate virtual environment
source venv/bin/activate

# Run migration
export $(cat .env | xargs)
python migrate_users_schema.py

# Restart app
exit
systemctl restart training-app
```

2. **Update any existing production users** with proper credentials

3. **Test registration** on production site

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Home page loads at `http://localhost:5000`
- [ ] Click "Register" - form loads
- [ ] Fill out registration form - submits successfully
- [ ] Automatically logged in after registration
- [ ] Can access training content
- [ ] Logout button appears in top right
- [ ] Click logout - returns to home page
- [ ] Click "Login" - form loads
- [ ] Login with registered credentials - works
- [ ] Invalid password shows error message
- [ ] Duplicate username/employee ID shows error

---

## 🎉 You're Done!

Your training app now has a **professional authentication system**!

### Key Features:
- ✅ Secure password hashing (industry standard)
- ✅ User profiles with names and employee IDs
- ✅ Beautiful registration and login pages
- ✅ Proper session management
- ✅ Password validation
- ✅ Duplicate prevention

### Next Steps:
- Add password reset functionality
- Add email verification
- Add "Remember me" checkbox
- Add password strength indicator (already in register form!)
- Export user list to CSV

---

**Questions?** Check `main.py` routes or `models.py` User model for implementation details.

**Need help?** All the code is documented and follows Flask best practices!

