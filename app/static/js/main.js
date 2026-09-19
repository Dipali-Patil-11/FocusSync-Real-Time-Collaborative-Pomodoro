document.addEventListener('DOMContentLoaded', () => {
    // Check if on Room page
    if (document.querySelector('.room-container')) {
        window.RoomManager.init();
        return;
    }

    // Otherwise, on Landing page
    initLandingPage();
});

function initLandingPage() {
    // Check URL parameters for errors
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const code = urlParams.get('code');

    if (error === 'room_not_found') {
        window.NotificationManager.showToast(`Room ${code || ''} not found. Please check the room code.`, 'error');
    } else if (error === 'name_required') {
        window.NotificationManager.showToast('Display name is required to join a room.', 'error');
    }

    // Auto uppercase room code input
    const joinCodeInput = document.getElementById('join-room-code');
    if (joinCodeInput) {
        joinCodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });

        if (code) {
            joinCodeInput.value = code.toUpperCase();
            // Switch to Join tab
            const joinTab = document.getElementById('join-tab');
            if (joinTab) {
                const tab = new bootstrap.Tab(joinTab);
                tab.show();
            }
        }
    }

    // Create Room Form Submission
    const createForm = document.getElementById('create-room-form');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('create-username');
            const btn = document.getElementById('btn-create-room');
            const alertEl = document.getElementById('create-error-alert');

            alertEl.classList.add('d-none');
            const username = usernameInput.value.trim();

            if (!username) {
                alertEl.textContent = 'Please enter a display name.';
                alertEl.classList.remove('d-none');
                return;
            }

            setLoading(btn, true);

            const res = await window.ApiClient.createRoom(username);
            setLoading(btn, false);

            if (res.success && res.data) {
                const roomCode = res.data.room_code;
                const token = res.data.participant_token;

                sessionStorage.setItem(`focussync_token_${roomCode}`, token);
                sessionStorage.setItem(`focussync_user_${roomCode}`, username);
                localStorage.setItem('focussync_username', username);

                window.location.href = `/room/${roomCode}`;
            } else {
                alertEl.textContent = res.message || 'Failed to create room.';
                alertEl.classList.remove('d-none');
            }
        });
    }

    // Join Room Form Submission
    const joinForm = document.getElementById('join-room-form');
    if (joinForm) {
        joinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('join-username');
            const codeInput = document.getElementById('join-room-code');
            const btn = document.getElementById('btn-join-room');
            const alertEl = document.getElementById('join-error-alert');

            alertEl.classList.add('d-none');
            const username = usernameInput.value.trim();
            const roomCode = codeInput.value.trim().toUpperCase();

            if (!username || !roomCode) {
                alertEl.textContent = 'Please fill in all fields.';
                alertEl.classList.remove('d-none');
                return;
            }

            setLoading(btn, true);

            const res = await window.ApiClient.joinRoom(roomCode, username);
            setLoading(btn, false);

            if (res.success && res.data) {
                const token = res.data.participant_token;

                sessionStorage.setItem(`focussync_token_${roomCode}`, token);
                sessionStorage.setItem(`focussync_user_${roomCode}`, username);
                localStorage.setItem('focussync_username', username);

                window.location.href = `/room/${roomCode}`;
            } else {
                if (res.error_code === 'FULL') {
                    showLandingErrorModal('Room Full', `Focus room ${roomCode} has reached its maximum capacity of 2 participants.`);
                } else if (res.error_code === 'NOT_FOUND') {
                    alertEl.textContent = `Focus room ${roomCode} does not exist. Please check the code.`;
                    alertEl.classList.remove('d-none');
                } else {
                    alertEl.textContent = res.message || 'Failed to join room.';
                    alertEl.classList.remove('d-none');
                }
            }
        });
    }
}

function setLoading(button, isLoading) {
    const textEl = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner-border');

    if (isLoading) {
        button.disabled = true;
        if (spinner) spinner.classList.remove('d-none');
    } else {
        button.disabled = false;
        if (spinner) spinner.classList.add('d-none');
    }
}

function showLandingErrorModal(title, message) {
    const titleEl = document.getElementById('landingErrorTitle');
    const msgEl = document.getElementById('landingErrorMessage');
    const modalEl = document.getElementById('landingErrorModal');

    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;
    if (modalEl) {
        const bsModal = new bootstrap.Modal(modalEl);
        bsModal.show();
    }
}
