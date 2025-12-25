// Triple-tap to reveal Dev tile functionality
// Detects 3 quick taps on Home tile to toggle secret Dev tile with flip animation

window.addEventListener('load', function() {
    console.log('[TripleTap] Initializing triple-tap detection...');

    const homeContainer = document.querySelector('[data-title="Home"]');
    const devContainer = document.querySelector('[data-title="Dev"]');

    if (!homeContainer || !devContainer) {
        console.error('[TripleTap] Home or Dev tile not found!');
        return;
    }

    const homeTile = homeContainer.querySelector('.tile');

    if (!homeTile) {
        console.error('[TripleTap] Home .tile element not found!');
        return;
    }

    console.log('[TripleTap] Attached to:', homeTile);

    let tapCount = 0;
    let tapTimer = null;
    let isRevealed = false;

    // Triple-tap detection
    homeTile.addEventListener('click', (e) => {
        tapCount++;
        console.log('[TripleTap] Tap count:', tapCount);

        // Clear existing timer
        if (tapTimer) {
            clearTimeout(tapTimer);
        }

        // If this is the third tap
        if (tapCount === 3) {
            console.log('[TripleTap] ✅ TRIPLE TAP DETECTED!');

            // Prevent normal tile click
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            // Toggle reveal state
            isRevealed = !isRevealed;

            if (isRevealed) {
                console.log('[TripleTap] Revealing Dev tile with flip');
                homeContainer.classList.add('flipped-out');
                devContainer.classList.add('flipped-in');
            } else {
                console.log('[TripleTap] Hiding Dev tile with flip');
                homeContainer.classList.remove('flipped-out');
                devContainer.classList.remove('flipped-in');
            }

            // Reset
            tapCount = 0;
            tapTimer = null;

            return false;
        }

        // Reset tap count after 600ms if not triple-tapped
        tapTimer = setTimeout(() => {
            console.log('[TripleTap] Timer expired, resetting tap count');
            tapCount = 0;
            tapTimer = null;
        }, 600);
    }, { capture: true });

    console.log('[TripleTap] ✅ Triple-tap detection initialized');
    console.log('[TripleTap] Try triple-tapping the Home tile!');
});
