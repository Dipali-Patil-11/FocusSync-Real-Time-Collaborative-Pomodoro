window.ApiClient = {
    csrfToken: null,

    getCsrfToken: function() {
        if (this.csrfToken) return this.csrfToken;
        const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/);
        return match ? decodeURIComponent(match[1]) : '';
    },

    request: async function(url, options = {}) {
        options.headers = options.headers || {};
        const method = (options.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            options.headers['Content-Type'] = options.headers['Content-Type'] || 'application/json';
            const csrf = this.getCsrfToken();
            if (csrf) {
                options.headers['X-CSRF-Token'] = csrf;
            }
        }
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            if (data && data.data && data.data.csrf_token) {
                this.csrfToken = data.data.csrf_token;
            }
            return data;
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            return { success: false, message: 'Network request failed.' };
        }
    },

    getMe: async function() {
        return await this.request('/api/auth/me');
    },

    register: async function(username, email, password) {
        return await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
    },

    login: async function(usernameOrEmail, password) {
        return await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username_or_email: usernameOrEmail, password })
        });
    },

    logout: async function() {
        return await this.request('/api/auth/logout', { method: 'POST' });
    },

    getHistory: async function(limit = 50, offset = 0) {
        return await this.request(`/api/user/history?limit=${limit}&offset=${offset}`);
    },

    getDashboard: async function() {
        return await this.request('/api/user/dashboard');
    },

    createSession: async function(username) {
        return await this.request('/api/sessions/create', {
            method: 'POST',
            body: JSON.stringify({ username: username })
        });
    },

    joinSession: async function(sessionCode, username, participantToken = null) {
        return await this.request('/api/sessions/join', {
            method: 'POST',
            body: JSON.stringify({
                session_code: sessionCode,
                username: username,
                participant_token: participantToken
            })
        });
    },

    getSessionInfo: async function(sessionCode) {
        return await this.request(`/api/sessions/${sessionCode}`);
    }
};

