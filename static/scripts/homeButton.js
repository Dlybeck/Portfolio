/**
 * Check to see if the home button should be visible in the navbar
 */
window.checkHomeButton = function (){
    // Get the current style
    const style = document.body.style;

    // Get the background position
    const backgroundPosition = style.backgroundPosition;

    // Get the home button
    let button = document.querySelector(".home-button");

    // Check if the background position is '0% 0%' (home)
    if (backgroundPosition === '0rem 0rem') {
        //Hide the home button
        button.classList.remove("visible");
    } else {
        //Show the home button
        button.classList.add('visible');
    }
}
