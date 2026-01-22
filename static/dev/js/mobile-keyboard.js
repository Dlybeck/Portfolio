(function() {
    // Detect touch device (mobile/tablet)
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    const forceShow = window.location.search.includes('mobilekeys');

    console.log('[mobile-keyboard] Touch device:', isTouchDevice, '| Width:', window.innerWidth);

    // Only show on touch devices (or force with ?mobilekeys)
    if (!isTouchDevice && !forceShow) {
        console.log('[mobile-keyboard] Not a touch device, skipping toolbar');
        return;
    }

    console.log('[mobile-keyboard] Creating toolbar for touch device...');
    const toolbar = document.createElement('div');
    toolbar.className = 'mobile-keyboard-toolbar';
    toolbar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #21222c;
        border-bottom: 1px solid #44475a;
        padding: 8px;
        display: flex;
        gap: 8px;
        z-index: 10000;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    `;

    const keys = [
        { label: 'C-c', key: 'c', ctrl: true },  // Dedicated Ctrl+C button
        { label: 'Esc', key: 'Escape' },
        { label: 'Tab', key: 'Tab' },
        { label: 'Ctrl', key: 'Control', toggle: true },
        { label: '↑', key: 'ArrowUp' },
        { label: '↓', key: 'ArrowDown' },
        { label: '←', key: 'ArrowLeft' },
        { label: '→', key: 'ArrowRight' }
    ];

    let ctrlPressed = false;

    // Flash feedback function
    function flashButton(btn) {
        const originalBg = btn.style.background;
        btn.style.background = '#50fa7b';  // Green flash
        setTimeout(() => {
            btn.style.background = originalBg;
        }, 100);
        // Haptic feedback if available
        if (navigator.vibrate) {
            navigator.vibrate(10);
        }
    }

    keys.forEach(k => {
        const btn = document.createElement('button');
        btn.textContent = k.label;
        btn.style.cssText = `
            flex: 1;
            min-width: 44px;
            height: 44px;
            background: ${k.ctrl ? '#ff5555' : '#282a36'};
            border: 1px solid #44475a;
            color: #f8f8f2;
            font-size: 14px;
            font-weight: ${k.ctrl ? 'bold' : 'normal'};
            border-radius: 4px;
            touch-action: manipulation;
            transition: background 0.1s ease;
        `;

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Find whichever iframe exists (terminal or vscode)
            const iframe = document.getElementById('terminal-iframe') || document.getElementById('vscode-iframe');

            if (k.toggle) {
                // Toggle button (Ctrl)
                ctrlPressed = !ctrlPressed;
                btn.style.background = ctrlPressed ? '#bd93f9' : '#282a36';
            } else if (k.ctrl) {
                // Dedicated Ctrl+key button (like C-c)
                flashButton(btn);
                if (iframe && iframe.contentWindow) {
                    iframe.contentWindow.postMessage({
                        type: 'keyboard-event',
                        key: k.key,
                        ctrlKey: true,
                        altKey: false
                    }, '*');
                }
            } else {
                // Regular key button
                flashButton(btn);
                if (iframe && iframe.contentWindow) {
                    iframe.contentWindow.postMessage({
                        type: 'keyboard-event',
                        key: k.key,
                        ctrlKey: ctrlPressed,
                        altKey: false
                    }, '*');
                }

                // Reset Ctrl toggle after sending
                if (ctrlPressed) {
                    ctrlPressed = false;
                    Array.from(toolbar.children).forEach(b => {
                        if (b.textContent === 'Ctrl') {
                            b.style.background = '#282a36';
                        }
                    });
                }
            }
        });

        toolbar.appendChild(btn);
    });

    document.body.appendChild(toolbar);
})();
