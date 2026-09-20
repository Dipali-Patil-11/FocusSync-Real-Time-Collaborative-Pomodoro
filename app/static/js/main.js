document.addEventListener('DOMContentLoaded', () => {
    // Check if on Session page
    if (document.querySelector('.session-container')) {
        window.SessionManager.init();
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

    if (error === 'session_not_found') {
        window.NotificationManager.showToast(`Session ${code || ''} not found. Please check the session code.`, 'error');
    } else if (error === 'name_required') {
        window.NotificationManager.showToast('Display name is required to join a session.', 'error');
    }

    // Auto uppercase session code input
    const joinCodeInput = document.getElementById('join-session-code');
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

    // Create Session Form Submission
    const createForm = document.getElementById('create-session-form');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('create-username');
            const btn = document.getElementById('btn-create-session');
            const alertEl = document.getElementById('create-error-alert');

            alertEl.classList.add('d-none');
            const username = usernameInput.value.trim();

            if (!username) {
                alertEl.textContent = 'Please enter a display name.';
                alertEl.classList.remove('d-none');
                return;
            }

            setLoading(btn, true);

            const res = await window.ApiClient.createSession(username);
            setLoading(btn, false);

            if (res.success && res.data) {
                const sessionCode = res.data.session_code;
                const token = res.data.participant_token;

                sessionStorage.setItem(`focussync_token_${sessionCode}`, token);
                sessionStorage.setItem(`focussync_user_${sessionCode}`, username);
                localStorage.setItem('focussync_username', username);

                window.location.href = `/session/${sessionCode}`;
            } else {
                alertEl.textContent = res.message || 'Failed to create session.';
                alertEl.classList.remove('d-none');
            }
        });
    }

    // Join Session Form Submission
    const joinForm = document.getElementById('join-session-form');
    if (joinForm) {
        joinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('join-username');
            const codeInput = document.getElementById('join-session-code');
            const btn = document.getElementById('btn-join-session');
            const alertEl = document.getElementById('join-error-alert');

            alertEl.classList.add('d-none');
            const username = usernameInput.value.trim();
            const sessionCode = codeInput.value.trim().toUpperCase();

            if (!username || !sessionCode) {
                alertEl.textContent = 'Please fill in all fields.';
                alertEl.classList.remove('d-none');
                return;
            }

            setLoading(btn, true);

            const res = await window.ApiClient.joinSession(sessionCode, username);
            setLoading(btn, false);

            if (res.success && res.data) {
                const token = res.data.participant_token;

                sessionStorage.setItem(`focussync_token_${sessionCode}`, token);
                sessionStorage.setItem(`focussync_user_${sessionCode}`, username);
                localStorage.setItem('focussync_username', username);

                window.location.href = `/session/${sessionCode}`;
            } else {
                if (res.error_code === 'FULL') {
                    showLandingErrorModal('Session Capacity Reached', `Focus session ${sessionCode} has reached its maximum capacity of 5 participants.`);
                } else if (res.error_code === 'NOT_FOUND') {
                    alertEl.textContent = `Focus session ${sessionCode} does not exist. Please check the code.`;
                    alertEl.classList.remove('d-none');
                } else {
                    alertEl.textContent = res.message || 'Failed to join session.';
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
