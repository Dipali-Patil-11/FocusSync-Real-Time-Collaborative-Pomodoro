window.ApiClient = {
    createSession: async function(username) {
        try {
            const response = await fetch('/api/sessions/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username })
            });
            return await response.json();
        } catch (error) {
            console.error('API createSession error:', error);
            return { success: false, message: 'Network error creating session.' };
        }
    },

    joinSession: async function(sessionCode, username, participantToken = null) {
        try {
            const response = await fetch('/api/sessions/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_code: sessionCode,
                    username: username,
                    participant_token: participantToken
                })
            });
            return await response.json();
        } catch (error) {
            console.error('API joinSession error:', error);
            return { success: false, message: 'Network error joining session.' };
        }
    },

    getSessionInfo: async function(sessionCode) {
        try {
            const response = await fetch(`/api/sessions/${sessionCode}`);
            return await response.json();
        } catch (error) {
            console.error('API getSessionInfo error:', error);
            return { success: false, message: 'Network error fetching session info.' };
        }
    }
};
