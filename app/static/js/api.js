window.ApiClient = {
    createRoom: async function(username) {
        try {
            const response = await fetch('/api/rooms/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username })
            });
            return await response.json();
        } catch (error) {
            console.error('API createRoom error:', error);
            return { success: false, message: 'Network error creating room.' };
        }
    },

    joinRoom: async function(roomCode, username, participantToken = null) {
        try {
            const response = await fetch('/api/rooms/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    room_code: roomCode,
                    username: username,
                    participant_token: participantToken
                })
            });
            return await response.json();
        } catch (error) {
            console.error('API joinRoom error:', error);
            return { success: false, message: 'Network error joining room.' };
        }
    },

    getRoomInfo: async function(roomCode) {
        try {
            const response = await fetch(`/api/rooms/${roomCode}`);
            return await response.json();
        } catch (error) {
            console.error('API getRoomInfo error:', error);
            return { success: false, message: 'Network error fetching room info.' };
        }
    }
};
