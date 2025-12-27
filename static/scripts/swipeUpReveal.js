// Dev Tile Reveal - Swipe Up Gesture
// Reveals hidden Dev tile when user swipes up on expanded Home tile

// State management
window.devTileState = {
    isFlipped: false
};

/**
 * Robust swipe-up detector that works with tile click handlers
 * Uses event capture and proper gesture detection
 */
function addSwipeUpDetector(element, callback, shouldActivate) {
    let startY = 0;
    let startX = 0;
    let startTime = 0;
    let isSwiping = false;

    const MIN_DISTANCE = 50; // Minimum swipe distance - easier to trigger
    const MAX_TIME = 600; // Maximum time for swipe in ms - more forgiving
    const MAX_HORIZONTAL_DRIFT = 80; // Maximum horizontal movement - allow more drift
    const MOVE_THRESHOLD = 8; // Threshold to detect intentional swipe vs click

    const handleStart = (e) => {
        // Only proceed if the activation condition is met
        if (!shouldActivate()) {
            return;
        }

        const touch = e.touches ? e.touches[0] : e;
        startY = touch.clientY;
        startX = touch.clientX;
        startTime = Date.now();
        isSwiping = false;
    };

    const handleMove = (e) => {
        if (!startTime) return;

        const touch = e.touches ? e.touches[0] : e;
        const currentY = touch.clientY;
        const deltaY = startY - currentY;

        // If moved vertically more than threshold, it's a swipe (not a click)
        if (Math.abs(deltaY) > MOVE_THRESHOLD) {
            isSwiping = true;
            // Prevent scrolling during swipe
            if (e.cancelable) {
                e.preventDefault();
            }
        }
    };

    const handleEnd = (e) => {
        if (!startTime) return;

        const touch = e.changedTouches ? e.changedTouches[0] : e;
        const endY = touch.clientY;
        const endX = touch.clientX;
        const endTime = Date.now();

        const deltaY = startY - endY; // Positive = upward swipe
        const deltaX = Math.abs(endX - startX);
        const deltaTime = endTime - startTime;

        // Reset state
        startTime = 0;

        // Check if it's a valid upward swipe
        if (isSwiping &&
            deltaY > MIN_DISTANCE &&
            deltaX < MAX_HORIZONTAL_DRIFT &&
            deltaTime < MAX_TIME) {

            console.log('[SwipeUp] ✅ Swipe up detected!', {
                distance: deltaY,
                time: deltaTime,
                horizontal: deltaX
            });

            // Prevent the click event from firing
            e.preventDefault();
            e.stopPropagation();

            // Haptic feedback
            if (navigator.vibrate) navigator.vibrate(50);

            callback();
        }

        isSwiping = false;
    };

    const handleCancel = () => {
        startTime = 0;
        isSwiping = false;
    };

    // Touch events (use capture phase to get events before click handlers)
    element.addEventListener('touchstart', handleStart, { passive: true, capture: true });
    element.addEventListener('touchmove', handleMove, { passive: false, capture: true });
    element.addEventListener('touchend', handleEnd, { capture: true });
    element.addEventListener('touchcancel', handleCancel, { capture: true });

    // Mouse events (for desktop testing)
    element.addEventListener('mousedown', handleStart, { capture: true });
    element.addEventListener('mousemove', handleMove, { capture: true });
    element.addEventListener('mouseup', handleEnd, { capture: true });
}

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SwipeUp] Initializing swipe-up gesture...');

    // Get tiles (Dev is already created by map.js)
    const homeContainer = document.querySelector('[data-title="Home"]');
    const devContainer = document.querySelector('[data-title="Dev"]');

    if (!homeContainer || !devContainer) {
        console.error('[SwipeUp] Home or Dev tile not found!');
        return;
    }

    const homeTile = homeContainer.querySelector('.tile');
    const devTile = devContainer.querySelector('.tile');

    // Helper function to flip tiles - purely visual swap, no navigation
    function flipTile(showDev) {
        window.devTileState.isFlipped = showDev;

        if (showDev) {
            console.log('[SwipeUp] ✨ Revealing Dev tile');
            // Swap visual states
            homeContainer.classList.add('flipped-out');
            homeContainer.classList.remove('expanded');
            devContainer.classList.add('flipped-in');
            devContainer.classList.add('expanded');
        } else {
            console.log('[SwipeUp] ✨ Hiding Dev tile');
            // Restore to Home
            homeContainer.classList.remove('flipped-out');
            homeContainer.classList.add('expanded');
            devContainer.classList.remove('flipped-in');
            devContainer.classList.remove('expanded');
        }
    }

    // Add swipe-up to Home tile (only when Home is expanded)
    addSwipeUpDetector(
        homeTile,
        () => {
            console.log('[SwipeUp] 🔓 Revealing Dev tile!');
            flipTile(true);
        },
        () => {
            // Only activate when Home is expanded (centered) and not already flipped
            return homeContainer.classList.contains('expanded') && !window.devTileState.isFlipped;
        }
    );

    // Add swipe-up to Dev tile to flip back (only when Dev is visible)
    addSwipeUpDetector(
        devTile,
        () => {
            console.log('[SwipeUp] 🔒 Hiding Dev tile!');
            flipTile(false);
        },
        () => {
            // Only activate when Dev is flipped in
            return window.devTileState.isFlipped;
        }
    );

    // If user navigates away from Home while Dev is flipped, flip back automatically
    // Listen for hash changes (navigation events)
    const originalCheckUrlHash = window.checkUrlHash;
    window.checkUrlHash = function() {
        const hash = decodeURIComponent(window.location.hash.slice(1));

        // If navigating away from Home/Dev and Dev is flipped, flip back
        if (hash && hash !== 'Home' && hash !== 'Dev' && window.devTileState.isFlipped) {
            console.log('[SwipeUp] Navigation detected, flipping back to Home');
            flipTile(false);
        }

        // Call original function
        return originalCheckUrlHash();
    };

    console.log('[SwipeUp] ✅ Swipe-up gesture initialized');
    console.log('[SwipeUp] 🔐 Swipe up on Home to reveal Dev tools!');
});
