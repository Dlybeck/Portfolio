// Dev Tile Reveal - Swipe Up Gesture
// Reveals hidden Dev tile when user swipes up on Home tile

// State management
window.devTileState = {
    isFlipped: false
};

/**
 * Simple swipe-up detector
 * Detects vertical swipe gesture on an element
 */
function addSwipeUpDetector(element, callback) {
    let startY = 0;
    let startX = 0;
    let startTime = 0;

    const MIN_DISTANCE = 50; // Minimum swipe distance in pixels
    const MAX_TIME = 300; // Maximum time for swipe in ms
    const MAX_HORIZONTAL_DRIFT = 50; // Maximum horizontal movement allowed

    const handleStart = (e) => {
        const touch = e.touches ? e.touches[0] : e;
        startY = touch.clientY;
        startX = touch.clientX;
        startTime = Date.now();
    };

    const handleEnd = (e) => {
        const touch = e.changedTouches ? e.changedTouches[0] : e;
        const endY = touch.clientY;
        const endX = touch.clientX;
        const endTime = Date.now();

        const deltaY = startY - endY; // Positive = upward swipe
        const deltaX = Math.abs(endX - startX);
        const deltaTime = endTime - startTime;

        // Check if it's a valid upward swipe
        if (deltaY > MIN_DISTANCE &&
            deltaX < MAX_HORIZONTAL_DRIFT &&
            deltaTime < MAX_TIME) {

            console.log('[SwipeUp] ✅ Swipe up detected!', {
                distance: deltaY,
                time: deltaTime
            });

            // Haptic feedback
            if (navigator.vibrate) navigator.vibrate(50);

            callback();
        }
    };

    // Touch events
    element.addEventListener('touchstart', handleStart, { passive: true });
    element.addEventListener('touchend', handleEnd);

    // Mouse events (for desktop testing)
    element.addEventListener('mousedown', handleStart);
    element.addEventListener('mouseup', handleEnd);
}

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SwipeUp] Initializing swipe-up gesture...');

    // Create the Dev tile (not in tilesData hierarchy)
    if (!document.querySelector('[data-title="Dev"]')) {
        console.log('[SwipeUp] Creating Dev tile...');
        window.createTile('Dev');

        // Add click handler to Dev tile for navigation
        const devContainer = document.querySelector('[data-title="Dev"]');
        const devTileElement = devContainer.querySelector('.tile');
        devTileElement.addEventListener('click', function(e) {
            window.handleTileClick(e, devContainer);
        });
    }

    // Get tiles
    const homeContainer = document.querySelector('[data-title="Home"]');
    const devContainer = document.querySelector('[data-title="Dev"]');

    if (!homeContainer || !devContainer) {
        console.error('[SwipeUp] Home or Dev tile not found!');
        return;
    }

    const homeTile = homeContainer.querySelector('.tile');
    const devTile = devContainer.querySelector('.tile');

    // Helper function to flip tiles
    function flipTile(showDev) {
        window.devTileState.isFlipped = showDev;

        if (showDev) {
            console.log('[SwipeUp] ✨ Revealing Dev tile');
            homeContainer.classList.add('flipped-out');
            devContainer.classList.add('flipped-in');
            // Make Dev the centered tile
            devContainer.classList.add('connected'); // Use 'connected' style like Home
        } else {
            console.log('[SwipeUp] ✨ Hiding Dev tile');
            homeContainer.classList.remove('flipped-out');
            devContainer.classList.remove('flipped-in');
            devContainer.classList.remove('connected');
        }
    }

    // Add swipe-up to Home tile (only when Home is centered)
    addSwipeUpDetector(homeTile, () => {
        // Only trigger when on Home view (URL hash is empty or #Home)
        const currentHash = decodeURIComponent(window.location.hash.slice(1));
        if (currentHash !== '' && currentHash !== 'Home') {
            console.log('[SwipeUp] Not on Home view, ignoring swipe');
            return;
        }

        console.log('[SwipeUp] 🔓 Revealing Dev tile!');
        flipTile(true);
    });

    // Add swipe-up to Dev tile to flip back
    addSwipeUpDetector(devTile, () => {
        if (window.devTileState.isFlipped) {
            console.log('[SwipeUp] 🔒 Hiding Dev tile!');
            flipTile(false);
        }
    });

    console.log('[SwipeUp] ✅ Swipe-up gesture initialized');
    console.log('[SwipeUp] 🔐 Swipe up on Home to reveal Dev tools!');
});
