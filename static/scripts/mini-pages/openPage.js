function openPage(route) {
    console.log("Here!")
    const container = document.querySelector(".mini-window-container");
    const page = document.querySelector(".mini-window");
    const closeButton = document.querySelector(".close-button");
    
    page.setAttribute("src", route);
    container.style.visibility = "visible";
    container.style.opacity = "1";

    const closePage = () => {
        container.style.opacity = "0";
        setTimeout(() => {
            container.style.visibility = "hidden";
        }, 1000);
        document.removeEventListener('click', handleClickOutside);
    };

    const handleClickOutside = (event) => {
        if (!container.contains(event.target)) {
            closePage();
        }
    };

    closeButton.addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent triggering handleClickOutside

        document.querySelector('.mini-window-container').style.display = 'none';
        
        // Remove the hash when closing the iframe
        history.pushState("", document.title, window.location.pathname + window.location.search);

        closePage();
    });

    setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
    }, 100);
}

window.openPage = openPage;