window.TimerRenderer = {
    timerState: null,
    serverOffset: 0,
    animationFrameId: null,
    soundEnabled: true,
    soundPlayed: false,

    init: function() {
        this.clockEl = document.getElementById('timer-clock');
        this.statusEl = document.getElementById('timer-status');
        this.sessionEl = document.getElementById('session-counter');
        this.progressRing = document.getElementById('timer-progress-ring');
        this.toggleBtn = document.getElementById('btn-timer-toggle');
        this.toggleText = document.getElementById('toggle-text');
        this.playIcon = document.getElementById('toggle-icon-play');
        this.pauseIcon = document.getElementById('toggle-icon-pause');
        
        this.circumference = 2 * Math.PI * 120; // 753.98
        if (this.progressRing) {
            this.progressRing.style.strokeDasharray = `${this.circumference} ${this.circumference}`;
        }
    },

    updateState: function(state, soundEnabled = true) {
        this.soundEnabled = soundEnabled;
        if (!state) return;

        // Calculate server time offset
        if (state.server_time) {
            this.serverOffset = (state.server_time * 1000) - Date.now();
        }

        const isNewModeOrStatus = !this.timerState || 
            this.timerState.mode !== state.mode || 
            this.timerState.status !== state.status;

        this.timerState = state;
        if (isNewModeOrStatus) {
            this.soundPlayed = false;
        }

        this.render();
        this.startLoop();
    },

    startLoop: function() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }

        const loop = () => {
            this.render();
            if (this.timerState && this.timerState.status === 'RUNNING') {
                this.animationFrameId = requestAnimationFrame(loop);
            }
        };

        if (this.timerState && this.timerState.status === 'RUNNING') {
            this.animationFrameId = requestAnimationFrame(loop);
        }
    },

    calculateRemaining: function() {
        if (!this.timerState) return 0;
        
        if (this.timerState.status === 'RUNNING' && this.timerState.target_end_time) {
            const currentServerTimeSec = (Date.now() + this.serverOffset) / 1000;
            const remaining = Math.ceil(this.timerState.target_end_time - currentServerTimeSec);
            return Math.max(0, remaining);
        }

        return Math.max(0, Math.ceil(this.timerState.remaining_seconds || 0));
    },

    render: function() {
        if (!this.timerState) return;

        const remaining = this.calculateRemaining();
        const duration = this.timerState.duration || 1500;

        // Check completion trigger
        if (remaining <= 0 && this.timerState.status === 'RUNNING' && !this.soundPlayed) {
            this.soundPlayed = true;
            const sessionCode = document.querySelector('.session-container')?.dataset.sessionCode;
            if (sessionCode && window.SocketClient) {
                window.SocketClient.emit('timer_complete', { session_code: sessionCode });
            }
        }

        // Format MM:SS
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        const formattedTime = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        
        if (this.clockEl) this.clockEl.textContent = formattedTime;
        document.title = `${formattedTime} - ${this.timerState.mode.replace('_', ' ')} | FocusSync`;

        // Update Status Badge
        if (this.statusEl) {
            this.statusEl.textContent = this.timerState.status;
            this.statusEl.className = `timer-status-badge badge rounded-pill px-3 py-1 mt-2 bg-input border-custom ${
                this.timerState.status === 'RUNNING' ? 'text-success' : 'text-secondary-custom'
            }`;
        }

        // Update Session Counter
        if (this.sessionEl) {
            const count = this.timerState.completed_sessions || 0;
            const currentSessionInCycle = (count % 4) + 1;
            this.sessionEl.textContent = `Session ${currentSessionInCycle} of 4 (${count} completed)`;
        }

        // Update Progress Ring
        if (this.progressRing) {
            const progressRatio = Math.min(1, Math.max(0, remaining / duration));
            const offset = this.circumference * (1 - progressRatio);
            this.progressRing.style.strokeDashoffset = offset;

            // Class modes
            const modeClass = this.timerState.mode === 'FOCUS' ? 'focus-mode' :
                             (this.timerState.mode === 'SHORT_BREAK' ? 'short-break-mode' : 'long-break-mode');
            this.progressRing.className.baseVal = `timer-circle-progress ${modeClass}`;
        }

        // Update Toggle Play/Pause Button State
        if (this.toggleBtn && this.toggleText && this.playIcon && this.pauseIcon) {
            if (this.timerState.status === 'RUNNING') {
                this.toggleText.textContent = 'Pause';
                this.playIcon.classList.add('d-none');
                this.pauseIcon.classList.remove('d-none');
            } else {
                this.toggleText.textContent = this.timerState.status === 'PAUSED' ? 'Resume' : 'Start';
                this.playIcon.classList.remove('d-none');
                this.pauseIcon.classList.add('d-none');
            }
        }

        // Highlight mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            if (btn.dataset.mode === this.timerState.mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
};
