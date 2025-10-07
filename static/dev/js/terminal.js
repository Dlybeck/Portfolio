/* Terminal Initialization (xterm.js) */

let term = null;
let fitAddon = null;

function initTerminal() {
    const store = Alpine.store('dashboard');

    // Initialize xterm.js
    term = new Terminal({
        cursorBlink: true,
        fontSize: store.fontSize,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#1a1a1a',
            foreground: '#f8f8f8',
            cursor: '#f8f8f8',
            black: '#000000',
            red: '#cd0000',
            green: '#00cd00',
            yellow: '#cdcd00',
            blue: '#0000ee',
            magenta: '#cd00cd',
            cyan: '#00cdcd',
            white: '#e5e5e5',
            brightBlack: '#7f7f7f',
            brightRed: '#ff0000',
            brightGreen: '#00ff00',
            brightYellow: '#ffff00',
            brightBlue: '#5c5cff',
            brightMagenta: '#ff00ff',
            brightCyan: '#00ffff',
            brightWhite: '#ffffff'
        }
    });

    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);

    term.open(document.getElementById('terminal'));
    fitAddon.fit();

    // Send input to terminal
    term.onData((data) => {
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {
            window.ws.send(JSON.stringify({type: 'input', data}));
        }
    });

    // Handle resize
    window.addEventListener('resize', () => {
        if (fitAddon) {
            fitAddon.fit();
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({
                    type: 'resize',
                    rows: term.rows,
                    cols: term.cols
                }));
            }
        }
    });

    // Expose globally for other modules
    window.term = term;
    window.fitAddon = fitAddon;

    store.terminalReady = true;
}

// Logout function
function logout() {
    const token = localStorage.getItem('access_token');

    fetch('/auth/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).catch(err => console.error('Logout error:', err));

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('working_directory');
    window.location.href = '/dev/login';
}

// Change directory function
function changeDirectory() {
    localStorage.removeItem('working_directory');
    window.location.href = '/dev';
}

// Kill session function - force restart when Claude is stuck
function killSession() {
    if (confirm('Kill current session and restart? This will terminate any running processes.')) {
        // Close WebSocket
        shouldReconnect = false;
        if (window.ws) {
            window.ws.close();
        }

        // Clear terminal
        if (window.term) {
            window.term.clear();
        }

        // Force NEW session by adding timestamp to URL
        setTimeout(() => {
            window.location.href = window.location.pathname + '?new_session=' + Date.now();
        }, 100);
    }
}
