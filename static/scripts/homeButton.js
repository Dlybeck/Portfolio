/**
 * Decide whether the "home" icon in the navbar should be visible.
 * Rule: show it whenever the current centered tile is not "Home".
 * The current tile is driven by the URL hash (see urlHandler.js).
 */
window.checkHomeButton = function () {
    const button = document.querySelector(".home-button");
    if (!button) return;

    const current = window.currentTileTitle
        || decodeURIComponent((window.location.hash || '').replace(/^#/, ''))
        || 'Home';
    const onHome = current === 'Home';

    if (onHome) {
        button.classList.remove("visible");
    } else {
        button.classList.add("visible");
    }
};
