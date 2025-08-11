// Theme management functionality
(function() {
    'use strict';
    
    let userThemePreference = 'system'; // system, light, dark
    
    // Get effective theme based on user preference
    function getEffectiveTheme(preference = userThemePreference) {
        if (preference === 'system') {
            // Check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return 'dark';
            }
            return 'light';
        }
        return preference; // 'light' or 'dark'
    }
    
    // Load theme preference from backend
    async function loadThemePreference() {
        try {
            const response = await fetch('/api/user/preferences');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.preferences.theme_preference) {
                    userThemePreference = data.preferences.theme_preference;
                }
            }
        } catch (error) {
            console.log('Could not load theme preference, using system default');
        }
        
        return getEffectiveTheme();
    }
    
    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }
    
    // Apply theme from preference setting
    function applyThemeFromPreference(preference) {
        userThemePreference = preference;
        const effectiveTheme = getEffectiveTheme(preference);
        applyTheme(effectiveTheme);
    }
    
    // Expose function globally for settings page
    window.applyThemeFromPreference = applyThemeFromPreference;
    
    // Initialize theme on page load
    async function initTheme() {
        // Load theme preference from backend and apply
        const effectiveTheme = await loadThemePreference();
        applyTheme(effectiveTheme);
        
        // Add smooth transition for theme switches
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
    
    // Also initialize immediately to prevent flash (use system default)
    const systemTheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', systemTheme);
    
})();