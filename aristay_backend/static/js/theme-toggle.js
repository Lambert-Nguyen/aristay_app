// Theme Toggle JavaScript
(function() {
    'use strict';
    
    // Theme storage key
    const THEME_KEY = 'aristay-theme';
    
    // Initialize theme on page load
    function initTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        
        applyTheme(theme);
        updateToggleButton(theme);
    }
    
    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
    }
    
    // Update toggle button appearance
    function updateToggleButton(theme) {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.classList.toggle('dark', theme === 'dark');
            
            // Update ARIA attributes for accessibility
            toggle.setAttribute('aria-pressed', theme === 'dark');
            toggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        }
    }
    
    // Toggle theme function
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        applyTheme(newTheme);
        updateToggleButton(newTheme);
        
        // Add pulse effect on theme change
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.classList.add('pulse');
            setTimeout(() => {
                toggle.classList.remove('pulse');
            }, 2000);
        }
        
        // Dispatch custom event for other scripts
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: newTheme }
        }));
    }
    
    // Create theme toggle button
    function createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.id = 'theme-toggle';
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.setAttribute('title', 'Toggle light/dark mode');
        
        // Add icons
        const sunIcon = document.createElement('span');
        sunIcon.className = 'theme-toggle-icon sun-icon';
        sunIcon.innerHTML = '☀️';
        
        const moonIcon = document.createElement('span');
        moonIcon.className = 'theme-toggle-icon moon-icon';
        moonIcon.innerHTML = '🌙';
        
        toggle.appendChild(sunIcon);
        toggle.appendChild(moonIcon);
        
        // Add click event
        toggle.addEventListener('click', toggleTheme);
        
        return toggle;
    }
    
    // Insert toggle into admin header
    function insertThemeToggle() {
        // Check if toggle already exists
        if (document.getElementById('theme-toggle')) {
            return; // Toggle already exists, don't create another one
        }
        
        // Try to find the branding div or user info area
        const branding = document.querySelector('.branding');
        const userInfo = document.querySelector('.branding > div:last-child');
        
        if (userInfo) {
            // Insert before user info
            const toggle = createThemeToggle();
            userInfo.insertBefore(toggle, userInfo.firstChild);
        } else if (branding) {
            // Insert at the end of branding
            const toggle = createThemeToggle();
            branding.appendChild(toggle);
        }
    }
    
    // Attach event listeners to existing toggle buttons
    function attachEventListeners() {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            // Remove any existing event listeners
            toggle.removeEventListener('click', toggleTheme);
            // Add the event listener
            toggle.addEventListener('click', toggleTheme);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            attachEventListeners();
        });
    } else {
        initTheme();
        attachEventListeners();
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem(THEME_KEY)) {
            const theme = e.matches ? 'dark' : 'light';
            applyTheme(theme);
            updateToggleButton(theme);
        }
    });
    
})();
