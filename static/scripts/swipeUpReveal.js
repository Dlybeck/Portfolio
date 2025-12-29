// Dev Tile Reveal - Dynamic Swipe Gesture
// Reveals hidden Dev tile with finger-tracking flip animation

// Constants
const SWIPE_CONFIG = {
    MAX_DISTANCE: 200,           // Full flip distance in pixels (50% = 100px)
    SNAP_THRESHOLD: 0.5,         // 50% = snap to complete, <50% = revert
    MAX_HORIZONTAL_DRIFT: 60,    // Maximum horizontal movement allowed
    MIN_MOVE_THRESHOLD: 5,       // Minimum movement to start tracking
    ANIMATION_DURATION: 250      // Snap animation duration (ms)
};

// Haptic patterns
const HAPTICS = {
    START: 10,        // Light tap when drag starts
    THRESHOLD: 20,    // Medium tap when crossing 50% threshold
    COMPLETE: 50      // Strong tap on snap to complete
};

// State management
window.devTileState = {
    isFlipped: false,
    isDragging: false
};

/**
 * Calculate progress based on swipe distance and current state
 * @param {number} deltaY - Vertical swipe distance (positive = upward)
 * @param {boolean} isFlipped - Whether currently showing Dev tile
 * @returns {number} Progress from 0 to 1
 */
function calculateProgress(deltaY, isFlipped) {
    const distanceRatio = deltaY / SWIPE_CONFIG.MAX_DISTANCE;
    // If showing Home, swipe up increases progress (0→1)
    // If showing Dev, swipe up decreases progress (1→0)
    if (isFlipped) {
        return Math.max(0, Math.min(1, 1 - distanceRatio));
    } else {
        return Math.max(0, Math.min(1, distanceRatio));
    }
}

/**
 * Update tile classes based on flip state
 * @param {HTMLElement} homeContainer - Home tile container
 * @param {HTMLElement} devContainer - Dev tile container
 * @param {boolean} showDev - True to show Dev, false to show Home
 */
function updateTileClasses(homeContainer, devContainer, showDev) {
    if (showDev) {
        homeContainer.classList.add('flipped-out');
        homeContainer.classList.remove('expanded');
        devContainer.classList.add('flipped-in');
        devContainer.classList.add('expanded');
    } else {
        homeContainer.classList.remove('flipped-out');
        homeContainer.classList.add('expanded');
        devContainer.classList.remove('flipped-in');
        devContainer.classList.remove('expanded');
    }
}

/**
 * Trigger haptic feedback if available
 * @param {number} duration - Vibration duration in ms
 */
function haptic(duration) {
    if (navigator.vibrate) {
        navigator.vibrate(duration);
    }
}

/**
 * Apply flip transform to both tiles in real-time
 * @param {number} progress - Progress from 0 (Home) to 1 (Dev)
 * @param {HTMLElement} homeContainer - Home tile container
 * @param {HTMLElement} devContainer - Dev tile container
 */
function applyFlipTransform(progress, homeContainer, devContainer) {
    // Clamp progress between 0 and 1
    progress = Math.max(0, Math.min(1, progress));

    // Calculate rotation angles (0° → 180°)
    const angle = progress * 180;

    // Home rotates backward and fades out
    const homeRotation = -angle;
    const homeOpacity = 1 - progress;

    // Dev rotates from 180° to 0° and fades in
    const devRotation = 180 - angle;
    const devOpacity = progress;

    // Z-index swap at midpoint (90°)
    const homeZIndex = angle < 90 ? 10 : 0;
    const devZIndex = angle < 90 ? 0 : 10;

    // Apply transforms (maintain translate for positioning)
    homeContainer.style.transform = `translate(-50%, -50%) rotateY(${homeRotation}deg)`;
    homeContainer.style.opacity = homeOpacity;
    homeContainer.style.zIndex = homeZIndex;
    homeContainer.style.pointerEvents = homeOpacity > 0.5 ? 'auto' : 'none';

    devContainer.style.transform = `translate(-50%, -50%) rotateY(${devRotation}deg)`;
    devContainer.style.opacity = devOpacity;
    devContainer.style.zIndex = devZIndex;
    devContainer.style.pointerEvents = devOpacity > 0.5 ? 'auto' : 'none';
}

/**
 * Animate snap to final state (complete or revert)
 * @param {number} currentProgress - Current progress (0-1)
 * @param {number} targetProgress - Target progress (0 or 1)
 * @param {HTMLElement} homeContainer - Home tile container
 * @param {HTMLElement} devContainer - Dev tile container
 * @param {Function} onComplete - Callback when animation completes
 */
function animateSnap(currentProgress, targetProgress, homeContainer, devContainer, onComplete) {
    const startTime = performance.now();
    const startProgress = currentProgress;
    const delta = targetProgress - startProgress;

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const t = Math.min(elapsed / SWIPE_CONFIG.ANIMATION_DURATION, 1);

        // Ease-out-back for snappy spring-like feel
        // More aggressive than cubic - starts fast, overshoots slightly, settles
        const c1 = 1.70158;
        const c3 = c1 + 1;
        const eased = 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
        const progress = startProgress + (delta * eased);

        applyFlipTransform(progress, homeContainer, devContainer);

        if (t < 1) {
            requestAnimationFrame(animate);
        } else {
            onComplete();
        }
    }

    requestAnimationFrame(animate);
}

/**
 * Dynamic swipe detector with finger-tracking flip
 * @param {HTMLElement} element - Element to attach gesture to
 * @param {Function} onFlipComplete - Callback when flip completes to Dev
 * @param {Function} onFlipRevert - Callback when flip reverts to Home
 * @param {Function} shouldActivate - Function that returns if gesture should activate
 * @param {HTMLElement} homeContainer - Home tile container
 * @param {HTMLElement} devContainer - Dev tile container
 */
function addDynamicSwipeDetector(element, onFlipComplete, onFlipRevert, shouldActivate, homeContainer, devContainer) {
    let startY = 0;
    let startX = 0;
    let startTime = 0;
    let hasStartedDrag = false;
    let currentProgress = 0;
    let hasPassedThreshold = false;
    let animationFrameId = null;

    const handleStart = (e) => {
        // Only proceed if activation condition is met
        if (!shouldActivate()) {
            return;
        }

        // Cancel any ongoing animation
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }

        const touch = e.touches ? e.touches[0] : e;
        startY = touch.clientY;
        startX = touch.clientX;
        startTime = Date.now();
        hasStartedDrag = false;
        hasPassedThreshold = false;
        currentProgress = window.devTileState.isFlipped ? 1 : 0;

        // Disable CSS transitions during drag
        homeContainer.style.transition = 'none';
        devContainer.style.transition = 'none';
    };

    const handleMove = (e) => {
        if (!startTime) return;

        const touch = e.touches ? e.touches[0] : e;
        const currentY = touch.clientY;
        const currentX = touch.clientX;

        const deltaY = startY - currentY; // Positive = upward swipe
        const deltaX = Math.abs(currentX - startX);

        // Check if movement is intentional (not a tap)
        if (!hasStartedDrag && Math.abs(deltaY) > SWIPE_CONFIG.MIN_MOVE_THRESHOLD) {
            hasStartedDrag = true;
            window.devTileState.isDragging = true;
            haptic(HAPTICS.START);

            console.log('[SwipeUp] 🎯 Drag started');
        }

        if (hasStartedDrag) {
            // Check if swipe is too horizontal (reject diagonal swipes)
            if (deltaX > SWIPE_CONFIG.MAX_HORIZONTAL_DRIFT) {
                return;
            }

            // Prevent scrolling during vertical swipe
            if (e.cancelable) {
                e.preventDefault();
            }

            // Calculate progress based on swipe distance
            currentProgress = calculateProgress(deltaY, window.devTileState.isFlipped);

            // Haptic feedback when crossing 50% threshold
            if (!hasPassedThreshold && currentProgress >= SWIPE_CONFIG.SNAP_THRESHOLD) {
                hasPassedThreshold = true;
                haptic(HAPTICS.THRESHOLD);
            } else if (hasPassedThreshold && currentProgress < SWIPE_CONFIG.SNAP_THRESHOLD) {
                hasPassedThreshold = false;
                haptic(HAPTICS.THRESHOLD);
            }

            // Apply transform in real-time using RAF for smoothness
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            animationFrameId = requestAnimationFrame(() => {
                applyFlipTransform(currentProgress, homeContainer, devContainer);
            });
        }
    };

    const handleEnd = (e) => {
        if (!startTime) return;

        const touch = e.changedTouches ? e.changedTouches[0] : e;
        const endY = touch.clientY;
        const endX = touch.clientX;

        const deltaY = startY - endY;
        const deltaX = Math.abs(endX - startX);

        // Recalculate final progress using exact end position (touchmove might be stale)
        currentProgress = calculateProgress(deltaY, window.devTileState.isFlipped);

        // Clean up
        startTime = 0;
        window.devTileState.isDragging = false;

        // Re-enable CSS transitions for snap animation
        homeContainer.style.transition = '';
        devContainer.style.transition = '';

        if (!hasStartedDrag) {
            // Was just a tap, not a drag - do nothing
            return;
        }

        console.log('[SwipeUp] 📊 Drag ended', {
            progress: (currentProgress * 100).toFixed(1) + '%',
            distance: deltaY,
            horizontalDrift: deltaX
        });

        // Reject gesture if too horizontal (likely scroll attempt)
        if (deltaX > SWIPE_CONFIG.MAX_HORIZONTAL_DRIFT) {
            console.log('[SwipeUp] ❌ Gesture rejected (too horizontal), reverting');

            // Snap back to current state
            const targetProgress = window.devTileState.isFlipped ? 1 : 0;
            animateSnap(currentProgress, targetProgress, homeContainer, devContainer, () => {
                console.log('[SwipeUp] ↩️ Reverted to ' + (targetProgress === 1 ? 'Dev' : 'Home'));
            });
            return;
        }

        // Determine if we should snap to complete or revert
        const shouldComplete = currentProgress >= SWIPE_CONFIG.SNAP_THRESHOLD;

        if (shouldComplete) {
            // Snap to Dev (complete flip)
            console.log('[SwipeUp] ✅ Snapping to Dev');
            haptic(HAPTICS.COMPLETE);

            animateSnap(currentProgress, 1, homeContainer, devContainer, () => {
                window.devTileState.isFlipped = true;
                updateTileClasses(homeContainer, devContainer, true);
                onFlipComplete();
                console.log('[SwipeUp] ✨ Flip to Dev complete');
            });
        } else {
            // Snap back to Home (revert flip)
            console.log('[SwipeUp] ↩️ Snapping back to Home');

            animateSnap(currentProgress, 0, homeContainer, devContainer, () => {
                window.devTileState.isFlipped = false;
                updateTileClasses(homeContainer, devContainer, false);
                onFlipRevert();
                console.log('[SwipeUp] ✨ Reverted to Home');
            });
        }

        hasStartedDrag = false;
    };

    const handleCancel = () => {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }

        startTime = 0;
        hasStartedDrag = false;
        window.devTileState.isDragging = false;

        // Re-enable transitions
        homeContainer.style.transition = '';
        devContainer.style.transition = '';
    };

    // Touch events (capture phase to intercept before click handlers)
    element.addEventListener('touchstart', handleStart, { passive: true, capture: true });
    element.addEventListener('touchmove', handleMove, { passive: false, capture: true });
    element.addEventListener('touchend', handleEnd, { capture: true });
    element.addEventListener('touchcancel', handleCancel, { capture: true });

    // Mouse events for desktop testing
    element.addEventListener('mousedown', handleStart, { capture: true });
    element.addEventListener('mousemove', handleMove, { capture: true });
    element.addEventListener('mouseup', handleEnd, { capture: true });
}

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SwipeUp] 🚀 Initializing dynamic swipe gesture...');

    const homeContainer = document.querySelector('[data-title="Home"]');
    const devContainer = document.querySelector('[data-title="Dev"]');

    if (!homeContainer || !devContainer) {
        console.error('[SwipeUp] ❌ Home or Dev tile not found!');
        return;
    }

    const homeTile = homeContainer.querySelector('.tile');
    const devTile = devContainer.querySelector('.tile');

    // Flag to prevent observer interference during programmatic flips
    let isFlipping = false;

    /**
     * Flip tiles programmatically (non-gesture triggered)
     * @param {boolean} showDev - True to show Dev, false to show Home
     */
    function flipTile(showDev) {
        if (window.devTileState.isDragging) {
            // Don't interrupt active drag
            return;
        }

        isFlipping = true;
        const targetProgress = showDev ? 1 : 0;
        const currentProgress = window.devTileState.isFlipped ? 1 : 0;

        console.log(`[SwipeUp] ${showDev ? '✨ Revealing' : '🔒 Hiding'} Dev tile (programmatic)`);

        // Ensure transitions are enabled
        homeContainer.style.transition = '';
        devContainer.style.transition = '';

        animateSnap(currentProgress, targetProgress, homeContainer, devContainer, () => {
            window.devTileState.isFlipped = showDev;
            updateTileClasses(homeContainer, devContainer, showDev);
            isFlipping = false;
        });
    }

    // Add dynamic swipe to Home tile
    addDynamicSwipeDetector(
        homeTile,
        () => {}, // onFlipComplete - no additional action needed
        () => {}, // onFlipRevert - no additional action needed
        () => homeContainer.classList.contains('expanded') && !window.devTileState.isFlipped,
        homeContainer,
        devContainer
    );

    // Add dynamic swipe to Dev tile (flip back to Home)
    addDynamicSwipeDetector(
        devTile,
        () => {}, // Will actually revert to Home (progress goes from 1→0)
        () => {},
        () => window.devTileState.isFlipped,
        homeContainer,
        devContainer
    );

    // Auto-flip back when navigating to other tiles
    const observer = new MutationObserver(() => {
        if (isFlipping || window.devTileState.isDragging) return;

        const allTiles = document.querySelectorAll('.tile-container');
        const otherTileExpanded = Array.from(allTiles).some(tile => {
            const title = tile.getAttribute('data-title');
            return title !== 'Home' && title !== 'Dev' && tile.classList.contains('expanded');
        });

        if (otherTileExpanded && window.devTileState.isFlipped) {
            console.log('[SwipeUp] 🔄 Navigation detected, auto-flipping to Home');
            flipTile(false);
        }
    });

    // Observe all tiles for navigation changes
    document.querySelectorAll('.tile-container').forEach(tile => {
        observer.observe(tile, {
            attributes: true,
            attributeFilter: ['class']
        });
    });

    // Backup navigation detection via hash changes
    const originalCheckUrlHash = window.checkUrlHash;
    if (originalCheckUrlHash) {
        window.checkUrlHash = function() {
            const hash = decodeURIComponent(window.location.hash.slice(1));

            if (hash && hash !== 'Home' && hash !== 'Dev' && window.devTileState.isFlipped && !window.devTileState.isDragging) {
                console.log('[SwipeUp] 🔄 Hash navigation detected, auto-flipping to Home');
                flipTile(false);
            }

            return originalCheckUrlHash();
        };
    }

    console.log('[SwipeUp] ✅ Dynamic swipe initialized');
    console.log('[SwipeUp] 💡 Drag up on Home to reveal Dev - follows your finger!');
});
