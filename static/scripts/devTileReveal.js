// Dev Tile Reveal - Long Press Detection
// Reveals hidden Dev tile when Home tile is long-pressed (750ms)
// Based on Gemini recommendation + Android Developer Options standard

// State management
window.devTileState = {
    isFlipped: false
};

/**
 * Adds robust long-press trigger (Gemini's recommended implementation)
 * Handles touch + mouse, scroll cancellation, and context menu prevention
 */
function addLongPressTrigger(element, callback, duration = 750) {
    let timer = null;
    let startX = 0;
    let startY = 0;
    const MOVEMENT_THRESHOLD = 10; // px

    const start = (e) => {
        // Prevent interfering with multi-touch gestures
        if (e.touches && e.touches.length > 1) return;

        // Track start position to detect scrolling
        if (e.touches) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        } else {
            startX = e.clientX;
            startY = e.clientY;
        }

        // Add visual feedback class
        element.classList.add('is-pressing');

        timer = setTimeout(() => {
            element.classList.remove('is-pressing');
            // Prevent context menu that fires after long press
            window.addEventListener('contextmenu', preventMenu, { once: true });

            // Haptic feedback
            if (navigator.vibrate) navigator.vibrate(50);

            callback();
        }, duration);
    };

    const cancel = () => {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        element.classList.remove('is-pressing');
    };

    const move = (e) => {
        if (!timer) return;

        // If user drags finger significantly, cancel (scrolling)
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        if (Math.abs(clientX - startX) > MOVEMENT_THRESHOLD ||
            Math.abs(clientY - startY) > MOVEMENT_THRESHOLD) {
            cancel();
        }
    };

    const preventMenu = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    // Touch Events
    element.addEventListener('touchstart', start, { passive: true });
    element.addEventListener('touchend', cancel);
    element.addEventListener('touchmove', move, { passive: true });
    element.addEventListener('touchcancel', cancel);

    // Mouse Events (desktop testing)
    element.addEventListener('mousedown', start);
    element.addEventListener('mouseup', cancel);
    element.addEventListener('mouseleave', cancel);
}

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DevTile] Initializing long-press detection (750ms)...');

    // Create the Dev tile (not in tilesData hierarchy)
    if (!document.querySelector('[data-title="Dev"]')) {
        console.log('[DevTile] Creating Dev tile...');
        window.createTile('Dev');
    }

    // Get tiles
    const homeContainer = document.querySelector('[data-title="Home"]');
    const devContainer = document.querySelector('[data-title="Dev"]');

    if (!homeContainer || !devContainer) {
        console.error('[DevTile] Home or Dev tile not found!');
        return;
    }

    const homeTile = homeContainer.querySelector('.tile');
    const devTile = devContainer.querySelector('.tile');

    // Helper function to flip tiles
    function flipTile(showDev) {
        window.devTileState.isFlipped = showDev;

        if (showDev) {
            console.log('[DevTile] ✨ Flipping to Dev tile');
            homeContainer.classList.add('flipped-out');
            devContainer.classList.add('flipped-in');
            // Transfer expanded state
            homeContainer.classList.remove('expanded');
            devContainer.classList.add('expanded');
        } else {
            console.log('[DevTile] ✨ Flipping back to Home tile');
            homeContainer.classList.remove('flipped-out');
            devContainer.classList.remove('flipped-in');
            // Transfer expanded state back
            devContainer.classList.remove('expanded');
            homeContainer.classList.add('expanded');
        }
    }

    // Add long-press to Home tile
    addLongPressTrigger(homeTile, () => {
        // Only trigger when Home is expanded (avoid navigation conflicts)
        const isHomeExpanded = homeContainer.classList.contains('expanded');
        if (!isHomeExpanded) {
            console.log('[DevTile] Home not expanded, ignoring long-press');
            return;
        }

        console.log('[DevTile] ✅ LONG PRESS DETECTED - Revealing Dev!');
        flipTile(true);
    }, 750);

    // Add long-press to Dev tile to flip back
    addLongPressTrigger(devTile, () => {
        console.log('[DevTile] ✅ LONG PRESS DETECTED - Returning to Home!');
        flipTile(false);
    }, 750);

    console.log('[DevTile] ✅ Long-press detection initialized');
    console.log('[DevTile] 🔐 Long-press Home when expanded to reveal Dev tools!');
});
