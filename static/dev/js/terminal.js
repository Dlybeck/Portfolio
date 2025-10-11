/* Terminal Initialization (xterm.js) */

let term = null;
let fitAddon = null;

// Global term mode tracking
window.currentTermMode = 'fancy';

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

    // Enable clickable URLs
    const webLinksAddon = new WebLinksAddon.WebLinksAddon();
    term.loadAddon(webLinksAddon);

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
async function killSession() {
    if (!confirm('Kill current session and restart? This will terminate any running processes.')) {
        return;
    }

    const token = localStorage.getItem('access_token');

    // Always kill the default user session (simplified logic)
    const sessionId = 'user_main_session';

    // First, explicitly kill the session on the backend
    try {
        console.log(`[Kill] Killing session ${sessionId} on backend...`);
        await fetch('/dev/api/kill-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        console.log('[Kill] Backend session killed successfully');
    } catch (err) {
        console.error('[Kill] Failed to kill backend session:', err);
    }

    // Close WebSocket to force disconnect
    shouldReconnect = false;
    if (window.ws) {
        window.ws.close();
    }

    // Clear terminal display
    if (window.term) {
        window.term.clear();
    }

    // Reload page to create fresh session
    setTimeout(() => {
        window.location.href = window.location.pathname;
    }, 500);
}

// Toggle terminal mode (fancy/simple)
function toggleTermMode() {
    // Toggle mode
    const newMode = window.currentTermMode === 'fancy' ? 'simple' : 'fancy';

    console.log(`[TermMode] Toggling from ${window.currentTermMode} to ${newMode}`);

    // Send toggle message to backend
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'toggle_term_mode',
            mode: newMode
        }));
    } else {
        console.error('[TermMode] WebSocket not connected');
    }
}
