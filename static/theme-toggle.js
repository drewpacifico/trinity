// Theme Toggle Functionality
(function() {
    'use strict';
    
    // Get or set theme preference
    function getTheme() {
        return localStorage.getItem('theme') || 'classic';
    }
    
    function setTheme(theme) {
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    }
    
    function applyTheme(theme) {
        const body = document.body;
        const modernStyleLink = document.getElementById('modern-style');
        
        if (theme === 'modern') {
            body.classList.add('modern-theme');
            if (modernStyleLink) {
                modernStyleLink.disabled = false;
            }
            // Update toggle button
            updateToggleButton('modern');
        } else {
            body.classList.remove('modern-theme');
            if (modernStyleLink) {
                modernStyleLink.disabled = true;
            }
            // Update toggle button
            updateToggleButton('classic');
        }
    }
    
    function updateToggleButton(currentTheme) {
        const toggleBtn = document.getElementById('theme-toggle-btn');
        if (!toggleBtn) return;
        
        if (currentTheme === 'modern') {
            toggleBtn.innerHTML = '🎨';
            toggleBtn.title = 'Switch to Classic Theme';
        } else {
            toggleBtn.innerHTML = '✨';
            toggleBtn.title = 'Switch to Modern Theme';
        }
    }
    
    function toggleTheme() {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'classic' ? 'modern' : 'classic';
        setTheme(newTheme);
        
        // Add a subtle animation
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    // Apply theme immediately to body (if it exists)
    if (document.body) {
        applyTheme(getTheme());
    }
    
    // Initialize theme on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Apply saved theme (in case body wasn't ready earlier)
        applyTheme(getTheme());
        
        // Create toggle button if it doesn't exist
        if (!document.getElementById('theme-toggle-btn')) {
            const toggleButton = document.createElement('button');
            toggleButton.id = 'theme-toggle-btn';
            toggleButton.className = 'theme-toggle';
            toggleButton.setAttribute('aria-label', 'Toggle Theme');
            toggleButton.onclick = toggleTheme;
            document.body.appendChild(toggleButton);
            
            // Update button appearance
            updateToggleButton(getTheme());
        }
        
        // Bind toggle button if it exists in the page
        const existingToggle = document.getElementById('theme-toggle-btn');
        if (existingToggle) {
            existingToggle.onclick = toggleTheme;
        }
    });
    
    // Export functions for external use
    window.themeToggle = {
        get: getTheme,
        set: setTheme,
        toggle: toggleTheme
    };
})();

