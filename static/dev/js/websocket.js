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

    // Force new session if requested via URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const newSessionParam = urlParams.get('new_session');
    const sessionParam = newSessionParam ? `&session=session_${newSessionParam}` : '';

    // Send preferred terminal mode (from localStorage/Alpine store)
    const preferredMode = store.termMode || 'simple';
    const modeParam = `&mode=${preferredMode}`;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/dev/ws/terminal?cwd=${encodeURIComponent(workingDir)}&token=${encodeURIComponent(token)}${sessionParam}${modeParam}`;

    // Track last message time for client-side ping
    let lastMessageTime = Date.now();
    let clientPingInterval = null;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Terminal connected');
        store.updateConnectionStatus('connected');

        // Start client-side ping (send ping every 20s, expect response within 10s)
        clientPingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Check if we've received any message recently
                const timeSinceLastMessage = Date.now() - lastMessageTime;

                // If no message for 25 seconds, connection might be dead - force reconnect
                if (timeSinceLastMessage > 25000) {
                    console.log(`[ClientPing] No message for ${timeSinceLastMessage/1000}s - forcing reconnect`);
                    ws.close();
                    return;
                }

                // Send client-initiated ping
                ws.send(JSON.stringify({type: 'ping'}));
                console.log('[ClientPing] Sent client ping');
            }
        }, 20000);  // Every 20 seconds (between server's 15s pings)
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        lastMessageTime = Date.now();  // Update on any message

        if (message.type === 'ping') {
            // Respond to server ping to keep connection alive
            ws.send(JSON.stringify({type: 'pong'}));
        } else if (message.type === 'output') {
            if (window.term) {
                window.term.write(message.data);
            }

            // Capture output for tabs (keep last 50KB)
            store.terminalOutput += message.data;
            if (store.terminalOutput.length > 50000) {
                store.terminalOutput = store.terminalOutput.slice(-50000);
            }
        } else if (message.type === 'current_term_mode') {
            // Initial term mode sent on connect
            window.currentTermMode = message.mode;
            console.log(`[TermMode] Current mode: ${message.mode}`);

            // Update localStorage and Alpine store
            localStorage.setItem('term_mode', message.mode);
            const store = Alpine.store('dashboard');
            if (store) {
                store.termMode = message.mode;
            }

            // Dispatch event to update button
            window.dispatchEvent(new CustomEvent('term_mode_update', {
                detail: { mode: message.mode }
            }));
        } else if (message.type === 'term_mode_changed') {
            // Term mode changed by another client
            window.currentTermMode = message.mode;
            console.log(`[TermMode] Mode changed to: ${message.mode}`);

            // Update localStorage and Alpine store
            localStorage.setItem('term_mode', message.mode);
            const store = Alpine.store('dashboard');
            if (store) {
                store.termMode = message.mode;
            }

            // Dispatch event to update button across all devices
            window.dispatchEvent(new CustomEvent('term_mode_update', {
                detail: { mode: message.mode }
            }));
        }
    };

    ws.onclose = (event) => {
        console.log('Terminal disconnected', event.code, event.reason);

        // Clean up client ping interval
        if (clientPingInterval) {
            clearInterval(clientPingInterval);
            clientPingInterval = null;
        }

        // Check if it's an authentication failure (code 1008)
        if (event.code === 1008) {
            console.log('[Auth] Session expired or invalid token - redirecting to login');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/dev/login';
            return;
        }

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

// Auto-refresh token every 11 hours 55 minutes (5 min before 12 hour expiry)
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
                console.log('[Token] Refreshed successfully');
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
    }
}, (11 * 60 * 60 * 1000) + (55 * 60 * 1000));  // 11h 55m
