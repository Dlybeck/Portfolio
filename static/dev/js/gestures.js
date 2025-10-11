/* Touch Gesture Handlers - Alpine.js Components */

// Main swipe handler for view switching
function swipeHandler() {
    return {
        touchStartX: 0,
        touchStartY: 0,
        touchCurrentX: 0,
        touchCurrentY: 0,
        isSwiping: false,

        onTouchStart(e) {
            if (window.innerWidth > 768) {
                Alpine.store('debugPanel')?.log('🖥️ Desktop detected - swipe disabled');
                return;
            }

            // Don't swipe if starting on interactive elements
            const target = e.target;
            const isInteractive = target.closest('.swipe-toolbar') ||
                                 target.closest('button') ||
                                 target.closest('input');

            if (isInteractive) {
                Alpine.store('debugPanel')?.log('🚫 Touch on interactive element - ignoring');
                return;
            }

            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.isSwiping = false;
            Alpine.store('debugPanel')?.log(`👇 Touch start: X=${Math.round(this.touchStartX)}, Y=${Math.round(this.touchStartY)}`);
        },

        onTouchMove(e) {
            if (window.innerWidth > 768) return;

            this.touchCurrentX = e.touches[0].clientX;
            this.touchCurrentY = e.touches[0].clientY;

            const deltaX = Math.abs(this.touchCurrentX - this.touchStartX);
            const deltaY = Math.abs(this.touchCurrentY - this.touchStartY);

            // Determine if horizontal swipe
            if (deltaX > deltaY && deltaX > 10) {
                this.isSwiping = true;
                e.preventDefault(); // Prevent scroll
            }
        },

        onTouchEnd(e) {
            if (window.innerWidth > 768) {
                return;
            }

            const deltaX = this.touchCurrentX - this.touchStartX;
            const deltaY = Math.abs(this.touchCurrentY - this.touchStartY);
            const debug = Alpine.store('debugPanel');

            debug?.log(`👆 Touch end: ΔX=${Math.round(deltaX)}, ΔY=${Math.round(deltaY)}`);

            // Ignore if too vertical or too short
            if (deltaY > Math.abs(deltaX)) {
                debug?.log('❌ Too vertical - ignoring');
                this.isSwiping = false;
                return;
            }

            // Require longer swipe distance (100px)
            if (Math.abs(deltaX) < 100) {
                debug?.log(`❌ Too short: ${Math.round(Math.abs(deltaX))}px < 100px`);
                this.isSwiping = false;
                return;
            }

            const store = Alpine.store('dashboard');
            debug?.log(`📍 Current view: ${store.currentView}`);

            if (deltaX < 0 && store.currentView === 'terminal') {
                // Swipe left - show preview
                debug?.log('✅ Swipe LEFT → Switching to preview');
                store.switchView('preview');
            } else if (deltaX > 0 && store.currentView === 'preview') {
                // Swipe right - show terminal
                debug?.log('✅ Swipe RIGHT → Switching to terminal');
                store.switchView('terminal');
            } else {
                debug?.log(`⚠️ No action: deltaX=${Math.round(deltaX)}, view=${store.currentView}`);
            }

            this.isSwiping = false;
        }
    };
}

// Toolbar swipe handler
function toolbarHandler() {
    return {
        touchStartX: 0,

        sendKey(key) {
            // Send key to terminal
            const keyMap = {
                'Tab': '\t',
                'S+Tab': '\x1b\t', // Shift+Tab
                '^C': '\x03',      // Ctrl+C
                'Esc': '\x1b',
                '↑': '\x1b[A',
                '↓': '\x1b[B',
                '←': '\x1b[D',
                '→': '\x1b[C',
                'Enter': '\r',
                'Clear': '\x0c'
            };

            const sequence = keyMap[key] || key;
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({
                    type: 'input',
                    data: sequence
                }));
            }

            Alpine.store('dashboard').vibrate(10);
        },

        copyTerminal() {
            if (window.term) {
                const selection = window.term.getSelection();
                if (selection) {
                    navigator.clipboard.writeText(selection).then(() => {
                        showNotification('Copied!', 'success');
                        Alpine.store('dashboard').vibrate(20);
                    });
                }
            }
        },

        onToolbarTouchStart(e) {
            this.touchStartX = e.touches[0].clientX;
        },

        onToolbarTouchMove(e) {
            // Optional: show visual feedback
        },

        onToolbarTouchEnd(e) {
            const deltaX = e.changedTouches[0].clientX - this.touchStartX;
            const store = Alpine.store('dashboard');

            if (Math.abs(deltaX) < 50) return;

            if (deltaX < 0) {
                store.nextToolbarPage();
            } else {
                store.prevToolbarPage();
            }
        }
    };
}

// Helper function for notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: var(--accent-color);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}
