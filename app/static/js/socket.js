window.SocketClient = {
    socket: null,
    listeners: {},

    init: function() {
        if (this.socket) return this.socket;

        // Initialize Socket.IO connection
        this.socket = io({
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
            transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
            console.log('Socket.IO connected. SID:', this.socket.id);
            this.updateConnectionStatus('connected');
        });

        this.socket.on('disconnect', (reason) => {
            console.warn('Socket.IO disconnected:', reason);
            this.updateConnectionStatus('disconnected');
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO connect error:', error);
            this.updateConnectionStatus('reconnecting');
        });

        return this.socket;
    },

    on: function(event, callback) {
        if (!this.socket) this.init();
        this.socket.on(event, callback);
    },

    emit: function(event, data) {
        if (!this.socket) this.init();
        this.socket.emit(event, data);
    },

    updateConnectionStatus: function(status) {
        const dot = document.getElementById('connection-status-dot');
        const text = document.getElementById('connection-status-text');
        if (!dot || !text) return;

        dot.className = `status-dot ${status}`;
        if (status === 'connected') text.textContent = 'Connected';
        else if (status === 'reconnecting') text.textContent = 'Reconnecting...';
        else text.textContent = 'Disconnected';
    }
};
