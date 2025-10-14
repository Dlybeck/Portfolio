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

        async fetchSessions() {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/dev/debug/sessions', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.log(`🗂️ Total sessions: ${data.total_sessions}`);
                    for (const [id, info] of Object.entries(data.sessions)) {
                        this.log(`  📦 ${id}: ${info.clients} clients, buffer=${info.buffer_size}`);
                    }
                } else {
                    this.log(`❌ Failed to fetch sessions: ${response.status}`);
                }
            } catch (err) {
                this.log(`❌ Error fetching sessions: ${err.message}`);
            }
        },

        clear() {
            this.logs = [];
            this.log('🧹 Logs cleared');
        }
    });

    // Main dashboard store
    Alpine.store('dashboard', {
        // View state
        currentView: 'terminal',  // 'terminal' | 'files' | 'preview'

        // Toolbar state
        toolbarPage: 0,

        // Connection state
        wsConnected: false,
        wsReconnecting: false,
        reconnectAttempts: 0,

        // Terminal state
        terminalReady: false,
        workingDir: localStorage.getItem('working_directory') || '~',
        fontSize: parseInt(localStorage.getItem('fontSize')) || (window.innerWidth <= 768 ? 12 : 14),

        // Tab state
        currentTab: 'files',
        terminalOutput: '',
        currentFilePath: localStorage.getItem('working_directory') || '~',

        // Theme state
        theme: localStorage.getItem('theme') || 'dark',
        soundEnabled: localStorage.getItem('soundEnabled') !== 'false',

        // Terminal mode state (fancy/simple)
        termMode: (() => {
            // Check if user has a saved preference
            const savedMode = localStorage.getItem('term_mode');
            if (savedMode) {
                return savedMode;
            }
            // No saved preference - default based on device type
            // Mobile (width <= 768px) defaults to 'simple', desktop to 'fancy'
            const isMobile = window.innerWidth <= 768;
            const defaultMode = isMobile ? 'simple' : 'fancy';
            // Save the default so it persists
            localStorage.setItem('term_mode', defaultMode);
            return defaultMode;
        })(),

        // Selection mode state
        selectionMode: false,

        // Methods
        switchView(view) {
            if (window.innerWidth > 768) return; // Desktop - no switching

            if (view === 'terminal' || view === 'files' || view === 'preview') {
                this.currentView = view;
                document.body.dataset.view = view;
                this.vibrate(10);

                // If switching to files view, load the file browser
                if (view === 'files') {
                    this.loadFilesView();
                }

                // If switching to terminal view, refresh and focus it
                if (view === 'terminal') {
                    setTimeout(() => {
                        if (window.term) {
                            window.term.refresh();
                            window.term.focus();

                            // On mobile, also focus the hidden textarea to trigger keyboard
                            if (window.innerWidth <= 768) {
                                try {
                                    const textarea = document.querySelector('.xterm-helper-textarea');
                                    if (textarea) {
                                        textarea.focus();
                                    }
                                } catch (e) {
                                    console.log('Could not focus textarea:', e);
                                }
                            }
                        }
                    }, 50);
                }
            }
        },

        loadFilesView() {
            // Load file browser into the files section
            const workingDir = localStorage.getItem('working_directory') || '~';

            // Use the existing loadFileBrowser function from tabs.js
            if (typeof loadFileBrowserForFiles === 'function') {
                loadFileBrowserForFiles(workingDir);
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
