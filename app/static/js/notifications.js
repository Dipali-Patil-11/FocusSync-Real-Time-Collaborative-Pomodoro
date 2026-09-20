window.NotificationManager = {
    processedEvents: new Set(),
    audioCtx: null,
    soundEnabled: true,

    init: function() {
        // Load user sound preference from localStorage
        const storedSound = localStorage.getItem('focussync_sound_enabled');
        this.soundEnabled = storedSound !== null ? (storedSound === 'true') : true;

        // Add autoplay unlock listener on user interaction
        const unlockAudio = () => {
            this.getAudioContext();
            if (this.audioCtx && this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
            document.removeEventListener('click', unlockAudio);
            document.removeEventListener('keydown', unlockAudio);
            document.removeEventListener('touchstart', unlockAudio);
        };
        document.addEventListener('click', unlockAudio, { once: true });
        document.addEventListener('keydown', unlockAudio, { once: true });
        document.addEventListener('touchstart', unlockAudio, { once: true });
    },

    setSoundEnabled: function(enabled) {
        this.soundEnabled = Boolean(enabled);
        localStorage.setItem('focussync_sound_enabled', this.soundEnabled ? 'true' : 'false');
    },

    getAudioContext: function() {
        if (!this.audioCtx) {
            const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
            if (AudioCtxClass) {
                this.audioCtx = new AudioCtxClass();
            }
        }
        return this.audioCtx;
    },

    hasProcessedEvent: function(eventId) {
        if (!eventId) return false;
        if (this.processedEvents.has(eventId)) return true;
        this.processedEvents.add(eventId);
        // Limit set size
        if (this.processedEvents.size > 200) {
            const oldest = this.processedEvents.values().next().value;
            this.processedEvents.delete(oldest);
        }
        return false;
    },

    playSound: function(type = 'FOCUS_START') {
        if (!this.soundEnabled) return;

        try {
            const ctx = this.getAudioContext();
            if (!ctx) return;

            if (ctx.state === 'suspended') {
                ctx.resume();
            }

            const now = ctx.currentTime;
            const masterGain = ctx.createGain();
            masterGain.gain.setValueAtTime(0.12, now);
            masterGain.connect(ctx.destination);

            if (type === 'FOCUS_START') {
                // Double rising chime (523Hz C5 -> 659Hz E5)
                const osc1 = ctx.createOscillator();
                osc1.type = 'sine';
                osc1.frequency.setValueAtTime(523.25, now);
                osc1.frequency.exponentialRampToValueAtTime(659.25, now + 0.15);
                osc1.connect(masterGain);
                osc1.start(now);
                osc1.stop(now + 0.3);

                masterGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

            } else if (type === 'SHORT_BREAK_START' || type === 'LONG_BREAK_START') {
                // Pleasant ascending notes (440Hz A4 -> 554Hz C#5)
                const osc = ctx.createOscillator();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.exponentialRampToValueAtTime(554.37, now + 0.2);
                osc.connect(masterGain);
                osc.start(now);
                osc.stop(now + 0.35);

                masterGain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

            } else if (type === 'COMPLETED') {
                // Completion chord (523Hz -> 659Hz -> 783Hz G5)
                const freqs = [523.25, 659.25, 783.99];
                freqs.forEach((freq, idx) => {
                    const osc = ctx.createOscillator();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, now + (idx * 0.08));
                    osc.connect(masterGain);
                    osc.start(now + (idx * 0.08));
                    osc.stop(now + 0.5);
                });

                masterGain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

            } else if (type === 'JOINED') {
                // Soft double ping (660Hz -> 880Hz)
                const osc = ctx.createOscillator();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(660, now);
                osc.frequency.setValueAtTime(880, now + 0.1);
                osc.connect(masterGain);
                osc.start(now);
                osc.stop(now + 0.25);

                masterGain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

            } else if (type === 'LEFT') {
                // Gentle descending ping (440Hz -> 330Hz)
                const osc = ctx.createOscillator();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.exponentialRampToValueAtTime(330, now + 0.2);
                osc.connect(masterGain);
                osc.start(now);
                osc.stop(now + 0.3);

                masterGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
            }
        } catch (e) {
            console.warn('Notification audio playback failed or blocked:', e);
        }
    },

    showNotificationToast: function({ event_id, title, message, mode, soundType, category }) {
        if (event_id && this.hasProcessedEvent(event_id)) {
            return; // Prevent duplicate toast
        }

        // Play Sound (respects local soundEnabled preference)
        this.playSound(soundType);

        // Visual Toast Construction
        const container = document.getElementById('toast-container');
        if (!container) return;

        let accentColor = 'var(--color-focus)';
        let iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>';

        if (mode === 'FOCUS') {
            accentColor = 'var(--color-focus)';
        } else if (mode === 'SHORT_BREAK') {
            accentColor = 'var(--color-short-break)';
            iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"></path><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path></svg>';
        } else if (mode === 'LONG_BREAK') {
            accentColor = 'var(--color-long-break)';
            iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>';
        } else if (category === 'COMPLETED') {
            accentColor = 'var(--color-warning)';
            iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        } else if (category === 'JOINED') {
            accentColor = 'var(--color-success)';
            iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>';
        } else if (category === 'LEFT') {
            accentColor = 'var(--color-danger)';
            iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="11" x2="23" y2="11"></line></svg>';
        }

        const toastEl = document.createElement('div');
        toastEl.className = 'toast toast-custom show mb-2';
        toastEl.style.borderLeft = `4px solid ${accentColor}`;

        toastEl.innerHTML = `
            <div class="d-flex align-items-center p-3 gap-3">
                <div class="toast-icon-box" style="color: ${accentColor}">
                    ${iconSvg}
                </div>
                <div class="flex-fill">
                    <div class="fw-bold small text-primary-custom mb-0.5">${title}</div>
                    <div class="extra-small text-secondary-custom">${message}</div>
                </div>
                <button type="button" class="btn-close p-1 ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toastEl);
        const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
        bsToast.show();

        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },

    // Shortcut handlers for specific events
    showToast: function(message, type = 'info') {
        this.showNotificationToast({
            title: type === 'error' ? 'Notice' : 'FocusSync',
            message: message,
            category: type === 'error' ? 'LEFT' : 'INFO',
            soundType: type === 'error' ? 'LEFT' : 'JOINED'
        });
    }
};

// Initialize NotificationManager
document.addEventListener('DOMContentLoaded', () => {
    window.NotificationManager.init();
});
