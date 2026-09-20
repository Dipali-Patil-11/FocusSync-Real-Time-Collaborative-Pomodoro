window.ThemeManager = {
    init: function() {
        const savedTheme = localStorage.getItem('focussync_theme');
        const theme = savedTheme || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
        
        this.setTheme(theme, false);
        this.bindEvents();
    },

    getTheme: function() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    },

    setTheme: function(theme, save = true) {
        const validTheme = theme === 'light' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', validTheme);
        
        if (save) {
            localStorage.setItem('focussync_theme', validTheme);
        }

        this.updateToggleIcons(validTheme);
    },

    toggleTheme: function() {
        const currentTheme = this.getTheme();
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(nextTheme, true);
    },

    updateToggleIcons: function(theme) {
        const toggleBtns = document.querySelectorAll('.btn-theme-toggle');
        toggleBtns.forEach(btn => {
            const sunIcon = btn.querySelector('.theme-icon-sun');
            const moonIcon = btn.querySelector('.theme-icon-moon');
            
            if (theme === 'dark') {
                if (sunIcon) sunIcon.classList.remove('d-none');
                if (moonIcon) moonIcon.classList.add('d-none');
                btn.setAttribute('aria-label', 'Switch to light theme');
                btn.setAttribute('title', 'Switch to light theme');
            } else {
                if (sunIcon) sunIcon.classList.add('d-none');
                if (moonIcon) moonIcon.classList.remove('d-none');
                btn.setAttribute('aria-label', 'Switch to dark theme');
                btn.setAttribute('title', 'Switch to dark theme');
            }
        });
    },

    bindEvents: function() {
        document.querySelectorAll('.btn-theme-toggle').forEach(btn => {
            btn.removeEventListener('click', this._onToggleClick);
            btn.addEventListener('click', this._onToggleClick);
        });

        // Listen for OS theme changes if user hasn't explicitly set preference
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('focussync_theme')) {
                this.setTheme(e.matches ? 'dark' : 'light', false);
            }
        });
    },

    _onToggleClick: function(e) {
        e.preventDefault();
        window.ThemeManager.toggleTheme();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.ThemeManager.init();
});
