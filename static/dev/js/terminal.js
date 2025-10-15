/* Terminal Initialization (xterm.js) */

let term = null;

// Global term mode tracking - initialize from store
window.currentTermMode = Alpine.store('dashboard').termMode;

function initTerminal() {
    const store = Alpine.store('dashboard');

    // Calculate fixed dimensions - never resize
    const fontSize = store.fontSize;
    const charWidth = fontSize * 0.6; // Approximate character width
    // Account for padding and scrollbar - subtract 32px for safety
    const availableWidth = window.innerWidth - 32;
    let cols = Math.max(80, Math.floor(availableWidth / charWidth));

    // On mobile (width <= 768px), cap at 80 columns to prevent text wrapping
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
        cols = Math.min(cols, 80);
    }

    const rows = 5000; // Large buffer for full chat history

    // Initialize xterm.js with fixed dimensions
    term = new Terminal({
        cursorBlink: true,
        fontSize: fontSize,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        rows: rows,
        cols: cols,
        scrollback: 0, // No internal scrollback - all rows are visible
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

    // Enable clickable URLs
    const webLinksAddon = new WebLinksAddon.WebLinksAddon();
    term.loadAddon(webLinksAddon);

    term.open(document.getElementById('terminal'));

    // Send input to terminal
    term.onData((data) => {
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {
            window.ws.send(JSON.stringify({type: 'input', data}));
        }
    });

    // Send initial size to backend
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'resize',
            rows: term.rows,
            cols: term.cols
        }));
    }

    // Expose globally for other modules
    window.term = term;

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

    // Update global state immediately
    window.currentTermMode = newMode;

    console.log(`[TermMode] Toggling from ${window.currentTermMode} to ${newMode}`);

    // Save preference to localStorage
    localStorage.setItem('term_mode', newMode);

    // Update Alpine store
    const store = Alpine.store('dashboard');
    if (store) {
        store.termMode = newMode;
    }

    // Show confirmation toast
    if (newMode === 'simple') {
        showToast('✓ Simple Mode: Clean text, no ASCII art', 'success');
    } else {
        showToast('✓ Fancy Mode: Full colors and ASCII art', 'success');
    }

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
