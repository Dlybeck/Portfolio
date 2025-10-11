/* Mobile Keyboard Detection using Visual Viewport API */

(function() {
    // Only run on mobile devices
    if (window.innerWidth > 768) return;

    // Check if Visual Viewport API is supported
    if (!window.visualViewport) {
        console.warn('[KeyboardHandler] Visual Viewport API not supported');
        return;
    }

    const viewport = window.visualViewport;
    let initialHeight = viewport.height;
    let isKeyboardVisible = false;

    // Store initial height on page load
    window.addEventListener('load', () => {
        initialHeight = viewport.height;
        console.log(`[KeyboardHandler] Initial viewport height: ${initialHeight}px`);
    });

    function updateViewport() {
        const currentHeight = viewport.height;

        // Set CSS custom property with actual viewport height
        document.documentElement.style.setProperty('--viewport-height', `${currentHeight}px`);

        const heightDifference = initialHeight - currentHeight;

        // Consider keyboard visible if viewport shrunk by more than 150px
        // This threshold helps avoid false positives from browser UI changes
        const threshold = 150;
        const shouldBeVisible = heightDifference > threshold;

        if (shouldBeVisible !== isKeyboardVisible) {
            isKeyboardVisible = shouldBeVisible;

            if (isKeyboardVisible) {
                console.log(`[KeyboardHandler] Keyboard detected (viewport: ${currentHeight}px, diff: ${heightDifference}px)`);
                document.body.classList.add('keyboard-visible');
            } else {
                console.log(`[KeyboardHandler] Keyboard hidden (viewport: ${currentHeight}px)`);
                document.body.classList.remove('keyboard-visible');
            }
        }
    }

    // Listen for viewport changes
    viewport.addEventListener('resize', updateViewport);
    viewport.addEventListener('scroll', updateViewport);

    // Set initial viewport height
    updateViewport();

    // Also check on focus/blur events of inputs (backup detection)
    document.addEventListener('focusin', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            // Small delay to allow keyboard to appear
            setTimeout(updateViewport, 300);
        }
    });

    document.addEventListener('focusout', () => {
        // Small delay to allow keyboard to disappear
        setTimeout(updateViewport, 300);
    });

    console.log('[KeyboardHandler] Initialized');
})();
