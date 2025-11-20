# Database Sync Guide

This guide explains how to sync your local SQLite database to the production PostgreSQL database on the server.

## Overview

The `sync_to_production.py` script transfers all data from your local SQLite database (`training_guide.db`) to your production PostgreSQL database. It maintains referential integrity and handles updates intelligently.

## ⚠️ Important: Where to Run This Script

**Run the script LOCALLY on your development machine**, not on the server.

**Why?**
- The script reads from your **local SQLite file** (`training_guide.db`) which is on your computer
- It connects to the **remote PostgreSQL database** via the connection string
- You don't need to push anything to the server or SSH into it
- The script acts as a bridge: Local SQLite → Remote PostgreSQL

**Workflow:**
1. Make changes locally (add content, update quizzes, etc.)
2. Test locally with SQLite database
3. Run `sync_to_production.py` locally to push changes to production PostgreSQL
4. Done! No need to SSH or deploy anything

## Prerequisites

1. **Local SQLite database** must exist and contain the data you want to sync
2. **Production database credentials** must be configured via environment variables:
   - `DATABASE_URI` or `DATABASE_URL` - PostgreSQL connection string
   - Example: `postgresql://user:password@host:port/database?sslmode=require`

## Setup (On Your Local Machine)

1. **Set production database environment variable** (Windows PowerShell):
   ```powershell
   # Set the connection string to your remote PostgreSQL database
   $env:DATABASE_URI = "postgresql://user:password@host:port/database?sslmode=require"
   ```

   Or create a `.env` file in the project root (if using python-dotenv):
   ```
   DATABASE_URI=postgresql://user:password@host:port/database?sslmode=require
   ```

   **Note:** Get this connection string from your hosting provider (Digital Ocean, Heroku, etc.)

2. **Verify local database exists**:
   ```powershell
   python check_db.py
   ```

3. **Make sure you're in the project directory**:
   ```powershell
   cd C:\Trinity-Training-Guide_main
   ```

## Usage

### Basic Sync (Full Database)

Sync all tables from local to production:

```powershell
python sync_to_production.py
```

### Dry Run (Preview Changes)

Preview what would be synced without making any changes:

```powershell
python sync_to_production.py --dry-run
```

### Skip User Data

Sync only content (chapters, modules, quizzes) without user data:

```powershell
python sync_to_production.py --skip-users
```

### Sync Specific Tables Only

Sync only specific tables:

```powershell
python sync_to_production.py --tables chapters modules quiz_questions
```

Available tables:
- `chapters`
- `modules`
- `chapter_sections`
- `quiz_questions`
- `glossary_terms`
- `users`
- `user_progress`
- `user_quiz_answers`

### Combined Options

```powershell
# Preview sync of only content (no users)
python sync_to_production.py --dry-run --skip-users

# Preview sync of specific tables
python sync_to_production.py --dry-run --tables chapters modules
```

## How It Works

The script syncs data in dependency order:

1. **Chapters** (no dependencies)
2. **Modules** (depends on chapters)
3. **Chapter Sections** (depends on chapters)
4. **Quiz Questions** (depends on modules)
5. **Glossary Terms** (no dependencies)
6. **Users** (no dependencies) - skipped if `--skip-users`
7. **User Progress** (depends on users and modules) - skipped if `--skip-users`
8. **User Quiz Answers** (depends on users and quiz questions) - skipped if `--skip-users`

### Update Strategy

- **Existing records**: Updated with data from local database
- **New records**: Created in production database
- **Missing dependencies**: Skipped with warning (e.g., module without chapter)
- **User passwords**: Preserved if user already exists in production (won't overwrite)

## Output

The script provides detailed output:

```
[*] Syncing Chapters...
   Found 5 chapters in local database
   ✓ Updated Chapter 1: Understanding Your Role
   + Created Chapter 6: Advanced Topics
   ...

[*] Syncing Modules...
   Found 25 modules in local database
   ✓ Updated Module 1.1: Your Role as a Freight Agent
   ...

SYNC SUMMARY
============================================================
Created: 15
   • chapters: 1
   • modules: 5
   • quiz_questions: 9

Updated: 45
   • chapters: 4
   • modules: 20
   • quiz_questions: 21

✅ Sync completed!
```

## Troubleshooting

### Error: "Production database URI not configured"

**Solution**: Set the `DATABASE_URI` or `DATABASE_URL` environment variable:
```powershell
$env:DATABASE_URI = "your-connection-string"
```

### Error: Connection refused or timeout

**Possible causes**:
- Database server is not accessible
- Firewall blocking connection
- Incorrect host/port in connection string
- SSL mode mismatch

**Solution**: Verify connection string and network access.

### Error: Foreign key constraint violation

**Possible causes**:
- Trying to sync dependent data before parent data
- Missing parent records in production

**Solution**: Run full sync (not selective tables) to ensure proper order.

### Warning: "Skipping Module X: Chapter Y not found"

**Cause**: The module references a chapter that doesn't exist in production.

**Solution**: 
1. Sync chapters first: `python sync_to_production.py --tables chapters`
2. Then sync modules: `python sync_to_production.py --tables modules`

## Best Practices

1. **Always do a dry run first**:
   ```powershell
   python sync_to_production.py --dry-run
   ```

2. **Backup production database** before syncing (if possible)

3. **Sync content separately from user data**:
   - Content: `python sync_to_production.py --skip-users`
   - Users: `python sync_to_production.py --tables users user_progress user_quiz_answers`

4. **Verify sync results**:
   ```powershell
   # Check production database
   $env:FLASK_ENV = "production"
   python check_db.py
   ```

5. **Sync regularly** to keep production up to date with local changes

## Example Workflow (All Commands Run Locally)

```powershell
# Make sure you're in the project directory
cd C:\Trinity-Training-Guide_main

# 1. Set your production database connection string
$env:DATABASE_URI = "postgresql://user:password@host:port/database?sslmode=require"

# 2. Preview what will be synced (dry-run)
python sync_to_production.py --dry-run

# 3. Sync only content (safe, no user data)
python sync_to_production.py --skip-users

# 4. Verify content synced correctly (checks production DB)
$env:FLASK_ENV = "production"
python check_db.py

# 5. If needed, sync user data separately
python sync_to_production.py --tables users user_progress user_quiz_answers
```

**Remember:** All of these commands run on your local machine. The script connects to the remote PostgreSQL database automatically.

## Security Notes

- **Never commit** database connection strings to version control
- Use environment variables or secure credential management
- Consider using read-only database user for sync operations
- User passwords are preserved in production (not overwritten)

## Related Scripts

- `init_db.py` - Initialize production database schema
- `db_migration.py` - Migrate data from files to database
- `check_db.py` - Check database contents

