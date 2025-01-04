// backgroundCheck.js
function checkHomeButton() {
    // Get the computed style of the element
    const style = document.body.style;

    // Get the background position value
    const backgroundPosition = style.backgroundPosition;

    let button = document.querySelector(".home-button");
    console.log(backgroundPosition)
    // Check if the background position is '0% 0%'
    if (backgroundPosition === '0% 0%') {
        console.log("Hiding");
        button.style.display = "none";
    } else {
        console.log("Making visible");
        button.style.display = "block";
    }
}
window.checkHomeButton = checkHomeButton;
