let button = document.querySelector(".home-button");

button.addEventListener("touchstart", function() {
    checkHomeButton();
});

let navtitle = document.querySelector(".navbar-title")

navtitle.addEventListener("touchstart", function() {
    checkHomeButton();
});



function checkHomeButton(){
    // Get the computed style of the element
    const style = document.body.style;

    // Get the background position value
    const backgroundPosition = style.backgroundPosition;

    // Check if the background position is '0% 0%'
    if (backgroundPosition === '0% 0%') {
        button.classList.remove("visible");
    } else {
        button.classList.add('visible');
    }
}

window.checkHomeButton = checkHomeButton;
