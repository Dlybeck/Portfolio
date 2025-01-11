document.addEventListener('click', function(event) {
    // Check if the clicked element or any of its ancestors match the selector '.internal-link'
    if (event.target.closest('.internal-link')) {
        event.preventDefault(); // Prevent the default link behavior

        // Find the closest ancestor with the class 'internal-link'
        const linkElement = event.target.closest('.internal-link');
        const href = linkElement.getAttribute("href");

        // Create a URL object to parse the href
        const url = new URL(href, window.location.origin);
        const path = url.pathname;

        console.log('Path extracted:', path); // Debugging line

        window.parent.navigateToPage(path); // Call the navigateToPage function in the parent window with the path

    }
});
