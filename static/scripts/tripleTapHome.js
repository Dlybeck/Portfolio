// Triple-tap to reveal Dev tile functionality
// Intercepts Home tile clicks to detect triple-tap pattern

// State management
window.tripleTapState = {
    tapCount: 0,
    tapTimer: null,
    isRevealed: false
};

// Override handleTileClick for Home tile to add triple-tap detection
document.addEventListener('DOMContentLoaded', function() {
    console.log('[TripleTap] Initializing triple-tap detection...');

    // Store original handleTileClick
    const originalHandleTileClick = window.handleTileClick;

    // Override with triple-tap detection
    window.handleTileClick = function(e, container) {
        const title = container.dataset.title;

        // Only intercept Home and Dev tile clicks
        if (title !== 'Home' && title !== 'Dev') {
            return originalHandleTileClick(e, container);
        }

        // Dev tile click should also toggle (triple-tap back to Home)
        const isDevTile = (title === 'Dev');

        // Prevent default tile click behavior for Home
        e.preventDefault();

        // Increment tap count
        window.tripleTapState.tapCount++;
        console.log('[TripleTap] Tap count:', window.tripleTapState.tapCount);

        // Clear existing timer
        if (window.tripleTapState.tapTimer) {
            clearTimeout(window.tripleTapState.tapTimer);
        }

        // Check for triple tap
        if (window.tripleTapState.tapCount === 3) {
            console.log('[TripleTap] ✅ TRIPLE TAP DETECTED on', title);

            const homeContainer = document.querySelector('[data-title="Home"]');
            const devContainer = document.querySelector('[data-title="Dev"]');

            // Toggle reveal state
            window.tripleTapState.isRevealed = !window.tripleTapState.isRevealed;

            if (window.tripleTapState.isRevealed) {
                console.log('[TripleTap] Flipping to Dev tile');
                homeContainer.classList.add('flipped-out');
                devContainer.classList.add('flipped-in');
            } else {
                console.log('[TripleTap] Flipping back to Home tile');
                homeContainer.classList.remove('flipped-out');
                devContainer.classList.remove('flipped-in');
            }

            // Reset tap count
            window.tripleTapState.tapCount = 0;
            window.tripleTapState.tapTimer = null;

            return; // Don't proceed with normal tile click
        }

        // Reset tap count after 600ms if not triple-tapped
        window.tripleTapState.tapTimer = setTimeout(() => {
            console.log('[TripleTap] Timer expired, resetting tap count');

            // If only 1 or 2 taps, treat as normal click
            if (window.tripleTapState.tapCount === 1) {
                console.log('[TripleTap] Single tap detected, executing normal tile click');
                originalHandleTileClick(e, container);
            }

            window.tripleTapState.tapCount = 0;
            window.tripleTapState.tapTimer = null;
        }, 600);
    };

    console.log('[TripleTap] ✅ Triple-tap detection initialized');
    console.log('[TripleTap] Try triple-tapping the Home tile!');
});
