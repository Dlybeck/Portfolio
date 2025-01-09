function openPage(route) {
    const container = document.querySelector(".mini-window-container");
    const page = document.querySelector(".mini-window");
    const closeButton = document.querySelector(".close-button");
    
    page.setAttribute("src", route);
    container.style.visibility = "visible";
    container.style.opacity = "1";

    const closePage = () => {
        container.style.opacity = "0";
        container.style.visibility = "hidden";
        document.removeEventListener('click', handleClickOutside);
    };

    const handleClickOutside = (event) => {
        if (!container.contains(event.target)) {
            closePage();
        }
    };

    closeButton.addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent triggering handleClickOutside
        closePage();
    });

    setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
    }, 100);
}

window.openPage = openPage;