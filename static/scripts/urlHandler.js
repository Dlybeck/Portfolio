window.checkUrlHash = function() {
    //Grab the hashed part of the url
    const hash = decodeURIComponent(window.location.hash.slice(1));

    //If a window position matched the hash
    if (hash && window.positions[hash]) {
        //Move to the tile
        window.centerOnTile(hash);
    } else {
        //Go to home
        window.centerOnTile('Home');
    }
};