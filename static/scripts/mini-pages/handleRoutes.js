document.addEventListener('click', function(event) {
    // Check if the clicked element or any of its ancestors match the selector '.internal-link'
    if (event.target.closest('.internal-link')) {
        // Find the closest ancestor with the class 'internal-link'
        const linkElement = event.target.closest('.internal-link');

        // Skip links that should open in new tab/window
        if (linkElement.getAttribute('target') === '_blank' || linkElement.getAttribute('target') === '_parent') {
            return; // Let browser handle it normally
        }

        event.preventDefault(); // Prevent the default link behavior
        const href = linkElement.getAttribute("href");

        // Create a URL object to parse the href
        const url = new URL(href, window.location.origin);
        const path = url.pathname;

        window.parent.navigateToPage(path); // Call the navigateToPage function in the parent window with the path

    }
});
