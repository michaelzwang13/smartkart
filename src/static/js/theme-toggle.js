// Theme management functionality
(function() {
    'use strict';
    
    // Get stored theme or default to system preference
    function getStoredTheme() {
        const stored = localStorage.getItem('theme');
        if (stored) {
            return stored;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }
    
    // Store theme preference
    function setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }
    
    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        updateToggleUI(theme);
    }
    
    // Update toggle button UI
    function updateToggleUI(theme) {
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        
        if (themeIcon && themeText) {
            if (theme === 'dark') {
                themeIcon.className = 'fas fa-sun';
                themeText.textContent = 'Light Mode';
            } else {
                themeIcon.className = 'fas fa-moon';
                themeText.textContent = 'Dark Mode';
            }
        }
    }
    
    // Toggle theme
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        setStoredTheme(newTheme);
        applyTheme(newTheme);
        
        // Add smooth transition for theme switch
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
        
        // Add visual feedback to toggle button
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.style.transform = 'scale(0.95)';
            setTimeout(() => {
                themeToggle.style.transform = '';
            }, 150);
        }
    }
    
    // Initialize theme on page load
    function initTheme() {
        const storedTheme = getStoredTheme();
        applyTheme(storedTheme);
        
        // Set up toggle button event listener
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function(e) {
                e.preventDefault();
                toggleTheme();
            });
        }
    }
    
    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
    
    // Also initialize immediately to prevent flash
    const storedTheme = getStoredTheme();
    document.documentElement.setAttribute('data-theme', storedTheme);
    
})();