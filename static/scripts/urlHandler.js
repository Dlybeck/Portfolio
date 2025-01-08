window.checkUrlHash = function() {
    const hash = decodeURIComponent(window.location.hash.slice(1));
    if (hash && window.positions[hash]) {
        window.centerOnTile(hash);
        if (window.routes[hash]) {
            const miniWindow = document.querySelector('.mini-window');
            if (miniWindow) {
                miniWindow.src = window.routes[hash];
                document.querySelector('.mini-window-container').style.display = 'block';
            }
        }
    } else {
        window.centerOnTile('Home');
    }
};