# Theme Toggle Feature

## Overview
The training manual now includes two visual themes that users can switch between:

1. **Classic Theme** (Default) - Dark modern theme with indigo/purple accents
2. **Modern Theme** - Clean, professional LMS-style theme inspired by modern online learning platforms

## How It Works

### For Users
- A floating button appears in the bottom-right corner of every page
- Click the button to toggle between themes
- Your preference is saved in browser localStorage
- The theme persists across page navigation and browser sessions

### Button Icons
- `✨` - Switch to Modern Theme (when Classic is active)
- `🎨` - Switch to Classic Theme (when Modern is active)

## Technical Implementation

### Files Created
1. **static/style-modern.css** - Complete modern theme stylesheet
2. **static/theme-toggle.js** - Theme switching logic and persistence
3. **templates/page.html** - Updated to include theme toggle

### Modern Theme Design Features
- Clean, light color scheme inspired by professional LMS platforms
- Cyan/teal primary colors (#00bcd4)
- Improved whitespace and readability
- Gradient backgrounds for hero sections
- Professional card-based layouts
- Smooth transitions and hover effects
- Modern navigation tabs
- Enhanced quiz styling
- Better tag and badge designs
- Responsive design for mobile devices

### Theme Colors (Modern)
```css
--modern-primary: #00bcd4 (Cyan)
--modern-primary-dark: #0097a7
--modern-secondary: #1e88e5 (Blue)
--modern-accent: #26c6da
--modern-bg: #f8f9fa (Light Gray)
--modern-surface: #ffffff (White)
--modern-text: #2c3e50 (Dark Text)
--modern-text-light: #546e7a (Muted Text)
```

### How It Works Technically
1. The modern CSS file is loaded but initially disabled
2. JavaScript checks localStorage for user's theme preference
3. If "modern" is selected, the modern CSS is enabled
4. The toggle button dynamically updates its icon and title
5. User preference is saved on every toggle

### Browser Compatibility
- Works in all modern browsers
- Uses localStorage API (supported since IE8+)
- Gracefully degrades if JavaScript is disabled (defaults to Classic theme)

## Customization

### Adding More Themes
To add additional themes:
1. Create a new CSS file in `static/` (e.g., `style-theme3.css`)
2. Update `theme-toggle.js` to include the new theme
3. Add logic to cycle through themes or provide a dropdown selector

### Modifying Existing Themes
- **Classic Theme**: Edit inline styles in `templates/page.html`
- **Modern Theme**: Edit `static/style-modern.css`

### Disabling Theme Toggle
To remove the theme toggle:
1. Remove the script tag from `templates/page.html`: 
   ```html
   <script src="{{ url_for('static', filename='theme-toggle.js') }}"></script>
   ```
2. Remove the modern CSS link from `templates/page.html`

## Design Philosophy

### Classic Theme
- Immersive, distraction-free reading experience
- Dark mode optimized for extended reading sessions
- Focus on content with minimal UI chrome
- Vibrant accent colors for engagement

### Modern Theme
- Professional, corporate training aesthetic
- Bright, energetic design for daytime learning
- Clear visual hierarchy
- Optimized for scannability and quick navigation
- Inspired by platforms like Coursera, Udemy, and LinkedIn Learning

## Future Enhancements
- [ ] Auto-detect system preference (prefers-color-scheme)
- [ ] Add more theme options (e.g., high contrast, sepia)
- [ ] Theme preview before switching
- [ ] Admin panel to customize theme colors
- [ ] Export/import custom themes

