// Triple-tap to reveal Dev tile functionality
// Only active when Home tile is already centered/expanded to avoid navigation conflicts

// State management
window.tripleTapState = {
    tapCount: 0,
    tapTimer: null,
    isFlipped: false
};

// Override handleTileClick for Home and Dev tiles
document.addEventListener('DOMContentLoaded', function() {
    console.log('[TripleTap] Initializing triple-tap detection...');

    // Create the Dev tile (not created automatically since it's not in tilesData)
    if (!document.querySelector('[data-title="Dev"]')) {
        console.log('[TripleTap] Creating Dev tile...');
        const devTile = window.createTile('Dev');

        // Attach click handler to Dev tile (same pattern as map.js)
        const devTileElement = devTile.querySelector('.tile');
        devTileElement.addEventListener('click', function(e) {
            window.handleTileClick(e, devTile);
        });

        console.log('[TripleTap] Dev tile created successfully');
    }

    // Store original handleTileClick
    const originalHandleTileClick = window.handleTileClick;

    // Override with triple-tap detection
    window.handleTileClick = function(e, container) {
        const title = container.dataset.title;

        // Only intercept Home and Dev tile clicks
        if (title !== 'Home' && title !== 'Dev') {
            return originalHandleTileClick(e, container);
        }

        // Check if we're currently flipped to Dev
        const homeContainer = document.querySelector('[data-title="Home"]');
        const devContainer = document.querySelector('[data-title="Dev"]');
        const isCurrentlyFlipped = homeContainer.classList.contains('flipped-out');

        // If flipped to Dev, clicking Dev should flip back
        if (title === 'Dev' && isCurrentlyFlipped) {
            console.log('[TripleTap] Dev clicked while flipped - checking for triple-tap to flip back');
            return handleTripleTap(e, container, homeContainer, devContainer);
        }

        // For Home tile: only handle triple-tap if Home is already expanded (centered)
        if (title === 'Home') {
            const isHomeExpanded = homeContainer.classList.contains('expanded');

            if (!isHomeExpanded && !isCurrentlyFlipped) {
                // Home is not centered - allow normal navigation
                console.log('[TripleTap] Home not expanded, allowing normal navigation');
                return originalHandleTileClick(e, container);
            }

            // Home is already expanded OR we're flipped - handle triple-tap
            console.log('[TripleTap] Home expanded or flipped, enabling triple-tap detection');
            return handleTripleTap(e, container, homeContainer, devContainer);
        }

        // Fallback to original behavior
        return originalHandleTileClick(e, container);
    };

    // Helper function to handle triple-tap logic
    function handleTripleTap(e, container, homeContainer, devContainer) {
        // Prevent default navigation
        e.preventDefault();
        e.stopPropagation();

        // Increment tap count
        window.tripleTapState.tapCount++;
        console.log('[TripleTap] Tap count:', window.tripleTapState.tapCount);

        // Clear existing timer
        if (window.tripleTapState.tapTimer) {
            clearTimeout(window.tripleTapState.tapTimer);
        }

        // Check for triple tap
        if (window.tripleTapState.tapCount === 3) {
            console.log('[TripleTap] ✅ TRIPLE TAP DETECTED - Flipping!');

            // Toggle flip state
            window.tripleTapState.isFlipped = !window.tripleTapState.isFlipped;

            if (window.tripleTapState.isFlipped) {
                console.log('[TripleTap] Flipping to Dev tile');
                homeContainer.classList.add('flipped-out');
                devContainer.classList.add('flipped-in');
                // Make Dev the "expanded" tile
                homeContainer.classList.remove('expanded');
                devContainer.classList.add('expanded');
            } else {
                console.log('[TripleTap] Flipping back to Home tile');
                homeContainer.classList.remove('flipped-out');
                devContainer.classList.remove('flipped-in');
                // Make Home the "expanded" tile again
                devContainer.classList.remove('expanded');
                homeContainer.classList.add('expanded');
            }

            // Reset tap count
            window.tripleTapState.tapCount = 0;
            window.tripleTapState.tapTimer = null;
            return;
        }

        // Reset tap count after 600ms if not triple-tapped
        window.tripleTapState.tapTimer = setTimeout(() => {
            console.log('[TripleTap] Timer expired, resetting tap count');
            window.tripleTapState.tapCount = 0;
            window.tripleTapState.tapTimer = null;
        }, 600);
    }

    console.log('[TripleTap] ✅ Triple-tap detection initialized');
    console.log('[TripleTap] Triple-tap Home when expanded to reveal Dev!');
});
