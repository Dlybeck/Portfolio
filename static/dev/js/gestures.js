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
            if (window.innerWidth > 768) return;

            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.isSwiping = false;
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
            if (window.innerWidth > 768) return;
            if (!this.isSwiping) return;

            const deltaX = this.touchCurrentX - this.touchStartX;
            const deltaY = Math.abs(this.touchCurrentY - this.touchStartY);

            // Ignore if too vertical or too short
            if (deltaY > Math.abs(deltaX) || Math.abs(deltaX) < 80) {
                this.isSwiping = false;
                return;
            }

            const store = Alpine.store('dashboard');

            if (deltaX < 0 && store.currentView === 'terminal') {
                // Swipe left - show preview
                store.switchView('preview');
            } else if (deltaX > 0 && store.currentView === 'preview') {
                // Swipe right - show terminal
                store.switchView('terminal');
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
