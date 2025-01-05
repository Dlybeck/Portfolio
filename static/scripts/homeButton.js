
function checkHomeButton(){
    // Get the computed style of the element
    const style = document.body.style;

    // Get the background position value
    const backgroundPosition = style.backgroundPosition;

    let button = document.querySelector(".home-button");

    // Check if the background position is '0% 0%'
    if (backgroundPosition === '0rem 0rem') {
        button.classList.remove("visible");
    } else {
        button.classList.add('visible');
    }
}

window.checkHomeButton = checkHomeButton;
