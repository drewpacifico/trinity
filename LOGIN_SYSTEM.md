# Login System Documentation

## Overview
A simple username-based authentication system has been added to the training manual. Users can log in to save their progress, or continue as a guest.

## Features

### 1. **Login Page** (`/login`)
- Clean, modern login interface
- Username-only authentication (no password required)
- "Continue as Guest" option for anonymous access
- Theme toggle available on login page
- Responsive design

### 2. **User Display in Header**
When logged in, the header shows:
- **Username badge**: `👤 YourUsername` in a rounded badge
- **Logout button**: Red logout icon (door with arrow)
- Positioned in the top-right of the progress header

### 3. **Logout Functionality** (`/logout`)
- Clicking the logout button clears the session
- Redirects to the login page
- All progress is saved to the database

## Routes

### `/login` (GET/POST)
- **GET**: Shows the login page
- **POST**: Processes username submission
  - Creates new user or retrieves existing user
  - Sets session variables: `user_id`, `username`, `logged_in`
  - Redirects to Table of Contents

### `/logout` (GET)
- Clears the session
- Redirects to login page
- Progress is preserved in database

## How It Works

### For New Users
1. Visit `http://127.0.0.1:5000/login`
2. Enter any username (e.g., "john", "mary", etc.)
3. Click "Start Training"
4. Progress is automatically saved to that username

### For Returning Users
1. Go to login page
2. Enter your previous username
3. Your progress is restored from the database

### For Guests
1. Click "Continue as Guest" on login page
2. Or go directly to `http://127.0.0.1:5000/`
3. Progress saves to an anonymous user session

## UI Elements

### Login Page
```
🚛 Training Manual
Your journey to becoming a freight agent

[Username Input Field]
[Start Training Button]

Continue as Guest

💡 Enter any username to save your progress. No password required!
```

### Header (When Logged In)
```
[Breadcrumb] | [Progress Bar] | 👤 username [🚪 Logout]
```

### Logout Button
- **Icon**: Door with exit arrow (SVG)
- **Color**: Red (#ef4444)
- **Hover**: Fills with red background
- **Size**: 36x36px compact button

## Database Integration

The system uses the existing `User` table:
- `id`: Auto-increment primary key
- `username`: Unique username
- `is_preview`: Boolean for preview mode users
- `created_at`: Timestamp

User progress is tracked via:
- `UserProgress` table (module completion)
- `UserQuizAnswer` table (quiz responses)

## Session Management

### Session Variables
- `user_id`: Database ID of the current user
- `username`: Display name
- `logged_in`: Boolean flag (True for named users)
- `preview_mode`: Boolean for preview access

### Anonymous Users
- Created automatically if accessing without login
- Username: "anonymous_user"
- Progress is still saved, but tied to the session

## Security Notes

**Current Implementation**:
- No passwords (username-only)
- No email verification
- Simple session-based auth

**Good For**:
- Internal training systems
- Trusted environments
- MVP/prototype phase

**Future Enhancements** (if needed):
- Add password authentication
- Email-based signup
- Role-based access control
- OAuth integration (Google, Microsoft, etc.)

## Styling

### Classic Theme
- Dark background (#0f0f10)
- Purple accents (#6366f1)
- Gold highlights (#fbbf24)
- Username badge: Purple background with light border

### Modern Theme
- Light background (#f8f9fa)
- Cyan accents (#00bcd4)
- Username badge: Cyan background
- Clean, minimalist design

Both themes have smooth transitions and hover effects.

## Testing

### Test Login
1. Go to `http://127.0.0.1:5000/login`
2. Enter username: "test_user"
3. Complete a module
4. Click logout
5. Log back in with "test_user"
6. Progress should be preserved

### Test Guest Mode
1. Go to `http://127.0.0.1:5000/`
2. Browse content without logging in
3. Progress saves to anonymous session

### Test Logout
1. Log in with a username
2. See username in header
3. Click red logout button
4. Should return to login page
5. Session cleared

## File Changes

### New Files
- `templates/login.html`: Login page template
- `LOGIN_SYSTEM.md`: This documentation

### Modified Files
- `main.py`: Added `/login` and `/logout` routes
- `templates/page.html`: Added username display and logout button in header
- `static/style-modern.css`: Added logout button styling

### Routes Added
```python
@app.route("/login", methods=["GET", "POST"])
@app.route("/logout")
```

## Usage Examples

### Direct to Login
```
http://127.0.0.1:5000/login
```

### Direct to Content (Creates Guest)
```
http://127.0.0.1:5000/
http://127.0.0.1:5000/page/1
```

### Logout
```
http://127.0.0.1:5000/logout
```

## Benefits

1. **User Tracking**: Know who's using the system
2. **Progress Persistence**: Users can return anytime
3. **Multi-Device**: Login from anywhere with your username
4. **Analytics**: Track completion rates per user
5. **Flexibility**: Guest mode still available

## Next Steps (Optional)

If you want to enhance the system:

1. **Add Password Protection**
   - Update User model with password hash field
   - Use `werkzeug.security` for password hashing
   - Add password field to login form

2. **Add User Registration**
   - Separate registration page
   - Email verification
   - Password strength requirements

3. **Add User Profile**
   - Profile page showing progress
   - Achievement badges
   - Completion certificates

4. **Add Admin Panel**
   - View all users
   - Reset user progress
   - View completion statistics

5. **Add Social Login**
   - Google OAuth
   - Microsoft OAuth
   - LinkedIn OAuth

