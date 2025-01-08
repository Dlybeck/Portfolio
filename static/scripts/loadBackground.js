
/**
 * Load in high quality background once page is loaded quickly with low quality
 */
document.addEventListener("DOMContentLoaded", function() {
    // Create a new Image object for the high-resolution background
    var highResBackground = new Image();
    highResBackground.src = `/static/images/sand2048.png`;

    // Once the high-resolution background is loaded, replace the background image
    highResBackground.onload = function() {
            document.body.style.backgroundImage = `url("/static/images/sand2048.png")`;
    };
});

