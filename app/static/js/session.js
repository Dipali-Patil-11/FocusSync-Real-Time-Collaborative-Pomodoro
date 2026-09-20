window.SessionManager = {
    sessionCode: null,
    participantToken: null,
    username: null,

    init: function() {
        const container = document.querySelector('.session-container');
        if (!container) return; // Not on session page

        this.sessionCode = container.dataset.sessionCode;
        this.participantToken = sessionStorage.getItem(`focussync_token_${this.sessionCode}`);
        this.username = sessionStorage.getItem(`focussync_user_${this.sessionCode}`) || localStorage.getItem('focussync_username');

        window.TimerRenderer.init();
        window.ModalController.init();
        
        this.bindEvents();
        this.connectAndJoin();
    },

    connectAndJoin: function() {
        // If user navigated directly via URL without username in session, prompt
        if (!this.username) {
            const promptedName = prompt('Enter your name to join this Focus Session:');
            if (promptedName && promptedName.trim().length >= 2) {
                this.username = promptedName.trim();
                localStorage.setItem('focussync_username', this.username);
            } else {
                window.location.href = `/?error=name_required&code=${this.sessionCode}`;
                return;
            }
        }

        // Initialize Socket.IO connection
        window.SocketClient.init();

        // Emit join_session when socket connects
        window.SocketClient.on('connect', () => {
            window.SocketClient.emit('join_session', {
                session_code: this.sessionCode,
                username: this.username,
                participant_token: this.participantToken
            });
        });
    },

    bindEvents: function() {

        // Timer Toggle (Start / Pause)
        const toggleBtn = document.getElementById('btn-timer-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const currentStatus = window.TimerRenderer.timerState?.status;
                if (currentStatus === 'RUNNING') {
                    window.SocketClient.emit('timer_pause', { session_code: this.sessionCode });
                } else if (currentStatus === 'PAUSED') {
                    window.SocketClient.emit('timer_resume', { session_code: this.sessionCode });
                } else {
                    window.SocketClient.emit('timer_start', { session_code: this.sessionCode });
                }
            });
        }

        // Timer Reset
        const resetBtn = document.getElementById('btn-timer-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                window.SocketClient.emit('timer_reset', { session_code: this.sessionCode });
            });
        }

        // Timer Skip
        const skipBtn = document.getElementById('btn-timer-skip');
        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                window.SocketClient.emit('timer_skip', { session_code: this.sessionCode });
            });
        }

        // Leave Session Button
        const leaveBtn = document.getElementById('btn-leave');
        if (leaveBtn) {
            leaveBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to leave this focus session?')) {
                    window.SocketClient.emit('leave_session', {
                        session_code: this.sessionCode,
                        participant_token: this.participantToken
                    });
                    sessionStorage.removeItem(`focussync_token_${this.sessionCode}`);
                    window.location.href = '/';
                }
            });
        }

        // Socket Events
        window.SocketClient.on('session_state', (data) => {
            if (data.participant_token) {
                this.participantToken = data.participant_token;
                sessionStorage.setItem(`focussync_token_${this.sessionCode}`, data.participant_token);
                sessionStorage.setItem(`focussync_user_${this.sessionCode}`, this.username);
            }
            if (data.participants) {
                this.renderParticipants(data.participants);
            }
            if (data.settings) {
                this.updateSettingsUI(data.settings);
            }
            if (data.timer) {
                window.TimerRenderer.updateState(data.timer, data.settings?.sound_enabled ?? true);
            }
        });

        window.SocketClient.on('participant_joined', (data) => {
            if (data.participants) this.renderParticipants(data.participants);
            const msg = data.message || `${data.username} joined the focus session`;
            this.setNotification(msg);
            
            window.NotificationManager.showNotificationToast({
                event_id: data.event_id,
                title: data.title || msg,
                message: msg,
                category: 'JOINED',
                soundType: 'JOINED'
            });
        });

        window.SocketClient.on('participant_left', (data) => {
            if (data.participants) this.renderParticipants(data.participants);
            const msg = data.message || `${data.username} left the focus session`;
            this.setNotification(msg);

            window.NotificationManager.showNotificationToast({
                event_id: data.event_id,
                title: data.title || msg,
                message: msg,
                category: 'LEFT',
                soundType: 'LEFT'
            });
        });

        window.SocketClient.on('presence_update', (data) => {
            if (data.participants) this.renderParticipants(data.participants);
        });

        window.SocketClient.on('timer_started_notification', (data) => {
            this.setNotification(`${data.title}: ${data.message}`);
            window.NotificationManager.showNotificationToast({
                event_id: data.event_id,
                title: data.title,
                message: data.message,
                mode: data.mode,
                soundType: `${data.mode}_START`
            });
        });

        window.SocketClient.on('timer_completed_notification', (data) => {
            this.setNotification(`${data.title}: ${data.message}`);
            window.NotificationManager.showNotificationToast({
                event_id: data.event_id,
                title: data.title,
                message: data.message,
                mode: data.mode,
                category: 'COMPLETED',
                soundType: 'COMPLETED'
            });
        });

        window.SocketClient.on('timer_start', (data) => {
            window.TimerRenderer.updateState(data.timer);
        });

        window.SocketClient.on('timer_pause', (data) => {
            window.TimerRenderer.updateState(data.timer);
            this.setNotification('Timer paused');
        });

        window.SocketClient.on('timer_resume', (data) => {
            window.TimerRenderer.updateState(data.timer);
        });

        window.SocketClient.on('timer_reset', (data) => {
            window.TimerRenderer.updateState(data.timer);
            this.setNotification('Timer reset');
        });

        window.SocketClient.on('timer_skip', (data) => {
            window.TimerRenderer.updateState(data.timer);
            this.setNotification(`Skipped to ${data.timer.mode.replace('_', ' ')}`);
        });

        window.SocketClient.on('timer_mode_changed', (data) => {
            window.TimerRenderer.updateState(data.timer);
            this.setNotification(`Switched to ${data.timer.mode.replace('_', ' ')}`);
        });

        window.SocketClient.on('settings_updated', (data) => {
            if (data.settings) this.updateSettingsUI(data.settings);
            if (data.timer) window.TimerRenderer.updateState(data.timer, data.settings?.sound_enabled);
            this.setNotification('Timer settings updated');
        });

        window.SocketClient.on('session_capacity_reached', (data) => {
            const modalEl = document.getElementById('sessionCapacityModal');
            if (modalEl) {
                const bsModal = new bootstrap.Modal(modalEl);
                bsModal.show();
            } else {
                alert(data.message || 'Session capacity reached');
                window.location.href = '/';
            }
        });

        window.SocketClient.on('session_error', (data) => {
            window.NotificationManager.showToast(data.message || 'An error occurred', 'error');
        });
    },

    setNotification: function(msg) {
        const textEl = document.getElementById('notification-text');
        if (textEl) textEl.textContent = msg;
    },

    renderParticipants: function(participants) {
        const countEl = document.getElementById('participants-count');
        const container = document.getElementById('participants-container');
        if (!container) return;

        if (countEl) {
            countEl.textContent = `${participants.length}/2`;
        }

        container.innerHTML = '';
        participants.forEach(p => {
            const initial = p.username.charAt(0).toUpperCase();
            const isMe = p.participant_token === this.participantToken;
            const onlineClass = p.is_online ? 'connected' : 'disconnected';
            const onlineText = p.is_online ? 'Online' : 'Offline';

            const card = document.createElement('div');
            card.className = 'participant-card';
            card.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <div class="avatar-circle">
                        ${initial}
                    </div>
                    <div>
                        <div class="fw-semibold small text-primary-custom d-flex align-items-center gap-2">
                            ${p.username}
                            ${isMe ? '<span class="badge bg-input border-custom text-orange extra-small">You</span>' : ''}
                        </div>
                        <div class="text-secondary-custom extra-small d-flex align-items-center gap-1.5 mt-0.5">
                            <span class="status-dot ${onlineClass}"></span>
                            ${onlineText} (Slot ${p.slot})
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    },

    updateSettingsUI: function(settings) {
        if (!settings) return;
        const focusInput = document.getElementById('setting-focus');
        const shortInput = document.getElementById('setting-short-break');
        const longInput = document.getElementById('setting-long-break');
        const intervalInput = document.getElementById('setting-long-break-interval');
        const autoStartInput = document.getElementById('setting-auto-start');
        const soundInput = document.getElementById('setting-sound');

        if (focusInput) focusInput.value = settings.focus_duration;
        if (shortInput) shortInput.value = settings.short_break_duration;
        if (longInput) longInput.value = settings.long_break_duration;
        if (intervalInput) intervalInput.value = settings.long_break_interval || 4;
        if (autoStartInput) autoStartInput.checked = settings.auto_start;
        if (soundInput) soundInput.checked = settings.sound_enabled;

        if (window.TimerRenderer) {
            window.TimerRenderer.updateSettings(settings);
        }
    }
};
