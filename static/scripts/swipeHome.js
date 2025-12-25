// Swipe-to-reveal Dev tile functionality
// Detects vertical swipe on Home tile to reveal/hide secret Dev tile

// Wait for tiles to be created, not just DOM ready
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
    let isDragging = false;

    // Touch start - record starting position
    homeTile.addEventListener('touchstart', (e) => {
        console.log('[SwipeHome] Touch start detected');
        startY = e.touches[0].clientY;
        startTime = Date.now();
        isDragging = false;
    }, { passive: true });

    // Touch move - detect if user is dragging
    homeTile.addEventListener('touchmove', (e) => {
        const currentY = e.touches[0].clientY;
        const deltaY = startY - currentY;

        // If moved more than 10px, it's a drag (not a tap)
        if (Math.abs(deltaY) > 10) {
            isDragging = true;
        }
    });

    // Touch end - check if valid swipe
    homeTile.addEventListener('touchend', (e) => {
        const endY = e.changedTouches[0].clientY;
        const swipeDistance = startY - endY; // Positive = swipe up
        const swipeTime = Date.now() - startTime;

        console.log('[SwipeHome] Touch end - distance:', swipeDistance, 'time:', swipeTime);

        // Swipe up to reveal Dev (must swipe at least 50px)
        if (swipeDistance > 50 && swipeTime < 500) {
            console.log('[SwipeHome] ✅ Swiped up - revealing Dev tile');
            homeTile.classList.add('swiped-up');
            e.preventDefault(); // Prevent click event
        }
        // Swipe down to hide Dev
        else if (swipeDistance < -50 && swipeTime < 500) {
            console.log('[SwipeHome] ✅ Swiped down - hiding Dev tile');
            homeTile.classList.remove('swiped-up');
            e.preventDefault();
        } else {
            console.log('[SwipeHome] ❌ Not a valid swipe (threshold not met)');
        }

        // Reset for next swipe
        startY = 0;
        startTime = 0;
        isDragging = false;
    });

    // Also support mouse for desktop testing
    let mouseDown = false;

    homeTile.addEventListener('mousedown', (e) => {
        startY = e.clientY;
        startTime = Date.now();
        mouseDown = true;
        isDragging = false;
    });

    homeTile.addEventListener('mousemove', (e) => {
        if (!mouseDown) return;

        const currentY = e.clientY;
        const deltaY = startY - currentY;

        if (Math.abs(deltaY) > 10) {
            isDragging = true;
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
        }
        // Swipe down to hide
        else if (swipeDistance < -50 && swipeTime < 500) {
            console.log('[SwipeHome] Mouse swipe down - hiding Dev tile');
            homeTile.classList.remove('swiped-up');
            e.preventDefault();
        }

        mouseDown = false;
        startY = 0;
        startTime = 0;
        isDragging = false;
    });

    // Prevent click event if user was dragging
    homeTile.addEventListener('click', (e) => {
        if (isDragging) {
            console.log('[SwipeHome] Preventing click - was dragging');
            e.stopPropagation();
            e.preventDefault();
        }
    }, true); // Use capture phase to catch before other handlers

    console.log('[SwipeHome] ✅ Swipe detection initialized successfully');
    console.log('[SwipeHome] Try swiping up on the Home tile!');
});
