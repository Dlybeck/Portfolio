function openPage(route) {
    const container = document.querySelector(".mini-window-container");
    const page = document.querySelector(".mini-window");
    const closeButton = document.querySelector(".close-button");
    
    // Store the initial route
    const initialRoute = route;

    // Set the iframe's src to the initial route
    page.setAttribute("src", route);
    container.style.visibility = "visible";
    container.style.opacity = "1";

    const closePage = () => {
        // Only close page if the page is visible
        if (container.style.visibility === "visible" && container.style.opacity === "1") {
            // make the close button act as a back button IF it is not on the original page
            if (page.contentWindow.location.pathname === initialRoute) {
                // hide
                container.style.opacity = "0";
                container.style.visibility = "hidden";
                document.removeEventListener('click', handleClickOutside);
            } else {
                // go back to the previous page
                page.contentWindow.history.back();
            }
        }
    };
    

    const handleClickOutside = (event) => {
        if (!container.contains(event.target)) {
            container.style.opacity = "0";
            container.style.visibility = "hidden";
            document.removeEventListener('click', handleClickOutside);
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
