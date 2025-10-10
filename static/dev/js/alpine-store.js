/* Alpine.js Data Store - Single Source of Truth */

document.addEventListener('alpine:init', () => {
    // Debug panel store
    Alpine.store('debugPanel', {
        visible: false,
        logs: [],
        maxLogs: 30,

        toggle() {
            this.visible = !this.visible;
            if (this.visible) {
                this.log('🐛 Debug panel opened');
                this.logState();
            }
        },

        log(message) {
            const timestamp = new Date().toLocaleTimeString();
            this.logs.unshift(`[${timestamp}] ${message}`);
            if (this.logs.length > this.maxLogs) {
                this.logs.pop();
            }
        },

        logState() {
            const dashboard = Alpine.store('dashboard');
            this.log(`📱 View: ${dashboard.currentView}`);
            this.log(`🖱️ Width: ${window.innerWidth}px`);
            this.log(`📶 WS: ${dashboard.wsConnected ? 'Connected' : 'Disconnected'}`);
        },

        clear() {
            this.logs = [];
            this.log('🧹 Logs cleared');
        }
    });

    // Main dashboard store
    Alpine.store('dashboard', {
        // View state
        currentView: 'terminal',  // 'terminal' | 'preview'

        // Toolbar state
        toolbarPage: 0,

        // Connection state
        wsConnected: false,
        wsReconnecting: false,
        reconnectAttempts: 0,

        // Terminal state
        terminalReady: false,
        workingDir: localStorage.getItem('working_directory') || '~',
        fontSize: parseInt(localStorage.getItem('fontSize')) || 14,

        // Tab state
        currentTab: 'files',
        terminalOutput: '',
        currentFilePath: localStorage.getItem('working_directory') || '~',

        // Theme state
        theme: localStorage.getItem('theme') || 'dark',
        soundEnabled: localStorage.getItem('soundEnabled') !== 'false',

        // Methods
        switchView(view) {
            if (window.innerWidth > 768) return; // Desktop - no switching

            if (view === 'terminal' || view === 'preview') {
                this.currentView = view;
                document.body.dataset.view = view;
                this.vibrate(10);
            }
        },

        switchTab(tabName) {
            this.currentTab = tabName;
        },

        nextToolbarPage() {
            this.toolbarPage = Math.min(this.toolbarPage + 1, 1); // Max 2 pages (0 and 1)
        },

        prevToolbarPage() {
            this.toolbarPage = Math.max(0, this.toolbarPage - 1);
        },

        setToolbarPage(page) {
            this.toolbarPage = page;
            this.vibrate(10);
        },

        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', this.theme);
            document.body.classList.toggle('light-theme', this.theme === 'light');
            this.vibrate(10);
        },

        toggleSound() {
            this.soundEnabled = !this.soundEnabled;
            localStorage.setItem('soundEnabled', this.soundEnabled);
            this.vibrate(10);
        },

        increaseFontSize() {
            if (this.fontSize < 20) {
                this.fontSize++;
                localStorage.setItem('fontSize', this.fontSize);
                if (window.term && window.fitAddon) {
                    window.term.options.fontSize = this.fontSize;
                    window.fitAddon.fit();
                }
                this.vibrate(10);
            }
        },

        decreaseFontSize() {
            if (this.fontSize > 10) {
                this.fontSize--;
                localStorage.setItem('fontSize', this.fontSize);
                if (window.term && window.fitAddon) {
                    window.term.options.fontSize = this.fontSize;
                    window.fitAddon.fit();
                }
                this.vibrate(10);
            }
        },

        updateConnectionStatus(status) {
            switch(status) {
                case 'connected':
                    this.wsConnected = true;
                    this.wsReconnecting = false;
                    this.reconnectAttempts = 0;
                    this.vibrate(20);
                    break;
                case 'disconnected':
                    this.wsConnected = false;
                    this.wsReconnecting = false;
                    this.vibrate(50);
                    this.playNotificationSound();
                    break;
                case 'reconnecting':
                    this.wsConnected = false;
                    this.wsReconnecting = true;
                    this.reconnectAttempts++;
                    break;
            }
        },

        vibrate(duration) {
            if ('vibrate' in navigator) {
                navigator.vibrate(duration);
            }
        },

        playNotificationSound() {
            if (!this.soundEnabled) return;

            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);

                oscillator.frequency.value = 800;
                oscillator.type = 'sine';

                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.2);
            } catch (e) {
                console.error('Sound failed:', e);
            }
        },

        // Initialize
        init() {
            // Apply saved theme
            if (this.theme === 'light') {
                document.body.classList.add('light-theme');
            }

            // Set initial view
            document.body.dataset.view = this.currentView;
        }
    });
});
