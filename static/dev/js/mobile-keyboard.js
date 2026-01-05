(function() {
    if (window.innerWidth > 768) return;

    const toolbar = document.createElement('div');
    toolbar.className = 'mobile-keyboard-toolbar';
    toolbar.style.cssText = `
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #21222c;
        border-top: 1px solid #44475a;
        padding: 8px;
        display: flex;
        gap: 8px;
        z-index: 10000;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    `;

    const keys = [
        { label: 'Esc', key: 'Escape' },
        { label: 'Tab', key: 'Tab' },
        { label: 'Ctrl', key: 'Control', toggle: true },
        { label: 'Alt', key: 'Alt', toggle: true },
        { label: '↑', key: 'ArrowUp' },
        { label: '↓', key: 'ArrowDown' },
        { label: '←', key: 'ArrowLeft' },
        { label: '→', key: 'ArrowRight' }
    ];

    let ctrlPressed = false;
    let altPressed = false;

    keys.forEach(k => {
        const btn = document.createElement('button');
        btn.textContent = k.label;
        btn.style.cssText = `
            flex: 1;
            min-width: 44px;
            height: 44px;
            background: #282a36;
            border: 1px solid #44475a;
            color: #f8f8f2;
            font-size: 14px;
            border-radius: 4px;
            touch-action: manipulation;
        `;

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (k.toggle) {
                btn.style.background = btn.style.background === 'rgb(189, 147, 249)' ? '#282a36' : '#bd93f9';
                btn.style.color = btn.style.background === 'rgb(189, 147, 249)' ? '#282a36' : '#f8f8f2';
                
                if (k.key === 'Control') ctrlPressed = !ctrlPressed;
                if (k.key === 'Alt') altPressed = !altPressed;
            } else {
                const iframe = document.getElementById('terminal-iframe');
                if (iframe && iframe.contentWindow) {
                    iframe.contentWindow.postMessage({
                        type: 'keyboard-event',
                        key: k.key,
                        ctrlKey: ctrlPressed,
                        altKey: altPressed
                    }, '*');
                }

                ctrlPressed = false;
                altPressed = false;
                Array.from(toolbar.children).forEach(b => {
                    if (b.textContent === 'Ctrl' || b.textContent === 'Alt') {
                        b.style.background = '#282a36';
                        b.style.color = '#f8f8f2';
                    }
                });
            }
        });

        toolbar.appendChild(btn);
    });

    document.body.appendChild(toolbar);
})();
