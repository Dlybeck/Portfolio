// Swipe-to-reveal Dev tile functionality
// Detects vertical swipe on Home tile to reveal/hide secret Dev tile

// Wait for tiles to be created
window.addEventListener('load', function() {
    console.log('[SwipeHome] Initializing swipe detection...');

    const homeTile = document.querySelector('[data-title="Home"]');
    const devTile = document.querySelector('[data-title="Dev"]');

    console.log('[SwipeHome] Home tile:', homeTile);
    console.log('[SwipeHome] Dev tile:', devTile);

    if (!homeTile) {
        console.error('[SwipeHome] Home tile not found!');
        return;
    }

    if (!devTile) {
        console.error('[SwipeHome] Dev tile not found!');
        return;
    }

    let startY = 0;
    let startTime = 0;
    let isSwiping = false;

    // Touch start - record starting position (CAPTURE PHASE - runs first!)
    homeTile.addEventListener('touchstart', (e) => {
        console.log('[SwipeHome] Touch start detected');
        startY = e.touches[0].clientY;
        startTime = Date.now();
        isSwiping = false;
    }, { passive: false, capture: true });

    // Touch move - detect if user is swiping (CAPTURE PHASE)
    homeTile.addEventListener('touchmove', (e) => {
        if (startY === 0) return;

        const currentY = e.touches[0].clientY;
        const deltaY = startY - currentY;

        // If moved more than 10px, it's a swipe (not a tap)
        if (Math.abs(deltaY) > 10) {
            isSwiping = true;
            // Prevent page scroll while swiping
            e.preventDefault();
        }
    }, { passive: false, capture: true });

    // Touch end - check if valid swipe (CAPTURE PHASE - runs before click!)
    homeTile.addEventListener('touchend', (e) => {
        if (startY === 0) return;

        const endY = e.changedTouches[0].clientY;
        const swipeDistance = startY - endY; // Positive = swipe up
        const swipeTime = Date.now() - startTime;

        console.log('[SwipeHome] Touch end - distance:', swipeDistance, 'time:', swipeTime, 'isSwiping:', isSwiping);

        // Swipe up to reveal Dev (must swipe at least 50px)
        if (swipeDistance > 50 && swipeTime < 500) {
            console.log('[SwipeHome] ✅ Swiped up - revealing Dev tile');
            homeTile.classList.add('swiped-up');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation(); // Prevent ALL other handlers
        }
        // Swipe down to hide Dev
        else if (swipeDistance < -50 && swipeTime < 500) {
            console.log('[SwipeHome] ✅ Swiped down - hiding Dev tile');
            homeTile.classList.remove('swiped-up');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
        }
        // Not a valid swipe - allow click to proceed
        else {
            console.log('[SwipeHome] ❌ Not a valid swipe (threshold not met)');
            isSwiping = false;
        }

        // Reset for next interaction
        startY = 0;
        startTime = 0;
    }, { passive: false, capture: true });

    // Prevent click event if user was swiping (CAPTURE PHASE)
    homeTile.addEventListener('click', (e) => {
        if (isSwiping) {
            console.log('[SwipeHome] Blocking click - was swiping');
            e.stopPropagation();
            e.stopImmediatePropagation();
            e.preventDefault();
            isSwiping = false; // Reset
            return false;
        }
    }, { capture: true });

    // Also support mouse for desktop testing
    let mouseDown = false;

    homeTile.addEventListener('mousedown', (e) => {
        startY = e.clientY;
        startTime = Date.now();
        mouseDown = true;
        isSwiping = false;
    });

    homeTile.addEventListener('mousemove', (e) => {
        if (!mouseDown) return;

        const currentY = e.clientY;
        const deltaY = startY - currentY;

        if (Math.abs(deltaY) > 10) {
            isSwiping = true;
        }
    });

    homeTile.addEventListener('mouseup', (e) => {
        if (!mouseDown) return;

        const endY = e.clientY;
        const swipeDistance = startY - endY;
        const swipeTime = Date.now() - startTime;

        // Swipe up to reveal
        if (swipeDistance > 50 && swipeTime < 500) {
            console.log('[SwipeHome] Mouse swipe up - revealing Dev tile');
            homeTile.classList.add('swiped-up');
            e.preventDefault();
            e.stopPropagation();
        }
        // Swipe down to hide
        else if (swipeDistance < -50 && swipeTime < 500) {
            console.log('[SwipeHome] Mouse swipe down - hiding Dev tile');
            homeTile.classList.remove('swiped-up');
            e.preventDefault();
            e.stopPropagation();
        }

        mouseDown = false;
        startY = 0;
        startTime = 0;
        isSwiping = false;
    });

    // Prevent mouse click if was swiping
    homeTile.addEventListener('click', (e) => {
        if (isSwiping) {
            e.stopPropagation();
            e.preventDefault();
            isSwiping = false;
            return false;
        }
    }, { capture: true });

    console.log('[SwipeHome] ✅ Swipe detection initialized successfully');
    console.log('[SwipeHome] Try swiping up on the Home tile!');
});
