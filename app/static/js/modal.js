window.ModalController = {
    init: function() {
        this.bindCounters();
        this.bindCopyButtons();
        this.bindSettingsForm();
        this.setupInviteModal();
    },

    bindCounters: function() {
        document.querySelectorAll('.btn-counter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = btn.dataset.target;
                const input = document.getElementById(targetId);
                if (!input) return;

                let val = parseInt(input.value) || 0;
                const min = parseInt(input.min) || 1;
                const max = parseInt(input.max) || 60;

                if (btn.classList.contains('btn-plus')) {
                    if (val < max) input.value = val + 1;
                } else if (btn.classList.contains('btn-minus')) {
                    if (val > min) input.value = val - 1;
                }
            });
        });
    },

    bindCopyButtons: function() {
        const copyTextToClipboard = async (text, successMsg) => {
            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(text);
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }
                window.NotificationManager.showToast(successMsg, 'success');
            } catch (err) {
                console.error('Clipboard copy failed:', err);
                window.NotificationManager.showToast('Failed to copy to clipboard', 'error');
            }
        };

        // Quick copy in header
        const quickCopyBtn = document.getElementById('btn-copy-session-code-quick');
        if (quickCopyBtn) {
            quickCopyBtn.addEventListener('click', () => {
                const sessionCode = document.getElementById('header-session-code')?.textContent;
                if (sessionCode) copyTextToClipboard(sessionCode, `Session code ${sessionCode} copied!`);
            });
        }

        // Copy session code in invite modal
        const modalCopyCodeBtn = document.getElementById('btn-copy-session-code-modal');
        if (modalCopyCodeBtn) {
            modalCopyCodeBtn.addEventListener('click', () => {
                const sessionCode = document.getElementById('modal-session-code')?.textContent;
                if (sessionCode) copyTextToClipboard(sessionCode, `Session code ${sessionCode} copied!`);
            });
        }

        // Copy invite link in invite modal
        const modalCopyLinkBtn = document.getElementById('btn-copy-invite-link');
        if (modalCopyLinkBtn) {
            modalCopyLinkBtn.addEventListener('click', () => {
                const sessionCode = document.getElementById('modal-session-code')?.textContent;
                if (sessionCode) {
                    const inviteUrl = `${window.location.origin}/session/${sessionCode}`;
                    copyTextToClipboard(inviteUrl, 'Invite link copied to clipboard!');
                }
            });
        }
    },

    setupInviteModal: function() {
        const inviteModalEl = document.getElementById('inviteModal');
        if (inviteModalEl) {
            inviteModalEl.addEventListener('show.bs.modal', () => {
                const sessionCode = document.querySelector('.session-container')?.dataset.sessionCode;
                const modalCodeEl = document.getElementById('modal-session-code');
                if (sessionCode && modalCodeEl) {
                    modalCodeEl.textContent = sessionCode;
                }
            });
        }
    },

    bindSettingsForm: function() {
        const settingsForm = document.getElementById('settings-form');
        if (!settingsForm) return;

        // Populate initial local sound preference
        const soundInput = document.getElementById('setting-sound');
        if (soundInput) {
            soundInput.checked = window.NotificationManager.soundEnabled;
        }

        settingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const sessionCode = document.querySelector('.session-container')?.dataset.sessionCode;
            if (!sessionCode) return;

            const focusVal = parseInt(document.getElementById('setting-focus').value);
            const shortVal = parseInt(document.getElementById('setting-short-break').value);
            const longVal = parseInt(document.getElementById('setting-long-break').value);
            const intervalVal = parseInt(document.getElementById('setting-long-break-interval')?.value || 4);
            const autoStartVal = document.getElementById('setting-auto-start').checked;
            const soundVal = document.getElementById('setting-sound').checked;

            // Set PER USER local sound preference
            window.NotificationManager.setSoundEnabled(soundVal);

            window.SocketClient.emit('settings_updated', {
                session_code: sessionCode,
                focus_duration: focusVal,
                short_break_duration: shortVal,
                long_break_duration: longVal,
                long_break_interval: intervalVal,
                auto_start: autoStartVal,
                sound_enabled: soundVal
            });

            // Close modal using bootstrap
            const modalEl = document.getElementById('settingsModal');
            if (modalEl) {
                const bsModal = bootstrap.Modal.getInstance(modalEl);
                if (bsModal) bsModal.hide();
            }
        });
    }
};
