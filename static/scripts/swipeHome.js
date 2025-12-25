// Swipe-to-reveal Dev tile functionality
// Detects vertical swipe on Home tile to reveal/hide secret Dev tile

// Wait for tiles to be created
window.addEventListener('load', function() {
    console.log('[SwipeHome] Initializing swipe detection...');

    const homeContainer = document.querySelector('[data-title="Home"]');

    if (!homeContainer) {
        console.error('[SwipeHome] Home tile container not found!');
        return;
    }

    // Get the actual tile element (not the container)
    const homeTile = homeContainer.querySelector('.tile');

    if (!homeTile) {
        console.error('[SwipeHome] Home .tile element not found!');
        return;
    }

    console.log('[SwipeHome] Attached to:', homeTile);

    let startY = 0;
    let startTime = 0;
    let currentY = 0;
    let isPointerDown = false;

    // Use Pointer Events API (better than touch events)
    homeTile.addEventListener('pointerdown', (e) => {
        console.log('[SwipeHome] Pointer down at Y:', e.clientY);
        startY = e.clientY;
        currentY = e.clientY;
        startTime = Date.now();
        isPointerDown = true;

        // Set pointer capture for smooth tracking
        homeTile.setPointerCapture(e.pointerId);
    }, { capture: true });

    homeTile.addEventListener('pointermove', (e) => {
        if (!isPointerDown) return;

        currentY = e.clientY;
        const deltaY = startY - currentY;

        console.log('[SwipeHome] Moving - deltaY:', deltaY);

        // If moving vertically, prevent other gestures
        if (Math.abs(deltaY) > 10) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, { passive: false, capture: true });

    homeTile.addEventListener('pointerup', (e) => {
        if (!isPointerDown) return;

        const endY = e.clientY;
        const swipeDistance = startY - endY; // Positive = up
        const swipeTime = Date.now() - startTime;

        console.log('[SwipeHome] Pointer up - distance:', swipeDistance, 'time:', swipeTime);

        // Valid swipe detected
        if (Math.abs(swipeDistance) > 50 && swipeTime < 500) {
            console.log('[SwipeHome] ✅ VALID SWIPE DETECTED');

            if (swipeDistance > 0) {
                // Swipe up - reveal
                console.log('[SwipeHome] Revealing Dev tile');
                homeContainer.classList.add('swiped-up');
            } else {
                // Swipe down - hide
                console.log('[SwipeHome] Hiding Dev tile');
                homeContainer.classList.remove('swiped-up');
            }

            // Block click event
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            // Don't let the tile click handler run
            setTimeout(() => {
                isPointerDown = false;
            }, 100);

            return false;
        }

        isPointerDown = false;
        console.log('[SwipeHome] Not a valid swipe - allowing click');
    }, { passive: false, capture: true });

    // Cancel on pointer leave
    homeTile.addEventListener('pointercancel', () => {
        isPointerDown = false;
        console.log('[SwipeHome] Pointer cancelled');
    });

    console.log('[SwipeHome] ✅ Pointer-based swipe detection initialized');
    console.log('[SwipeHome] Try swiping up/down on the Home tile!');
});
