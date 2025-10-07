/* WebSocket Connection Management */

let ws = null;
let shouldReconnect = true;
const maxReconnectDelay = 30000; // 30 seconds

function connectWebSocket() {
    const store = Alpine.store('dashboard');
    const token = localStorage.getItem('access_token');
    const workingDir = store.workingDir;

    // Check auth
    if (!token) {
        window.location.href = '/dev/login';
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/dev/ws/terminal?cwd=${encodeURIComponent(workingDir)}&token=${encodeURIComponent(token)}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Terminal connected');
        store.updateConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'output') {
            if (window.term) {
                window.term.write(message.data);
            }

            // Capture output for tabs (keep last 50KB)
            store.terminalOutput += message.data;
            if (store.terminalOutput.length > 50000) {
                store.terminalOutput = store.terminalOutput.slice(-50000);
            }
        }
    };

    ws.onclose = () => {
        console.log('Terminal disconnected');
        store.updateConnectionStatus('disconnected');

        if (window.term) {
            window.term.write('\r\n\x1b[33mConnection lost. Reconnecting...\x1b[0m\r\n');
        }

        // Auto-reconnect with exponential backoff
        if (shouldReconnect) {
            attemptReconnect();
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Force reconnect on error
        if (ws) {
            ws.close();
        }
    };

    // Expose globally
    window.ws = ws;
}

function attemptReconnect() {
    const store = Alpine.store('dashboard');
    const delay = Math.min(1000 * Math.pow(2, store.reconnectAttempts), maxReconnectDelay);

    console.log(`[Reconnect] Attempt ${store.reconnectAttempts + 1} in ${delay}ms...`);
    store.updateConnectionStatus('reconnecting');

    setTimeout(() => {
        if (shouldReconnect) {
            console.log('[Reconnect] Attempting to reconnect...');
            connectWebSocket();
        }
    }, delay);
}

// Visibility API - keep connection alive when tab is hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('[Visibility] Tab hidden - connection stays alive');
    } else {
        console.log('[Visibility] Tab visible');
        // If connection lost while hidden, reconnect now
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.log('[Visibility] Reconnecting on tab visible...');
            connectWebSocket();
        }
    }
});

// Prevent disconnection on mobile when swiping away
window.addEventListener('pagehide', (event) => {
    if (event.persisted) {
        console.log('[PageHide] Page hidden but persisted - keeping connection');
    }
});

// Only truly disconnect when page is being unloaded
window.addEventListener('beforeunload', () => {
    console.log('[BeforeUnload] Page closing - allowing disconnect');
    shouldReconnect = false;
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
});

// Auto-refresh token every 25 minutes
setInterval(async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
        try {
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
    }
}, 25 * 60 * 1000);
