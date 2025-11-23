# SamDavidWeb

## 1. Run locally with uvicorn

### Run ```main.py```

## 2. Run locally with docker

### To build (if not already build):

```
docker build -t myapp .
```

### To run:
```
docker run -p 8080:8080 myapp
```

### Then go to http://localhost:8080

## 3. Adding a new tile

To add a new tile to the interactive map:

1. Open `static/scripts/tileData.js` and add your tile title to the `window.tilesData` object, specifying an array of connected tile titles:

```js
"New Tile Title": ["ConnectedTile1", "ConnectedTile2"]
```

2. Still in `static/scripts/tileData.js`, add a corresponding entry to the `window.tileInfo` object with position, HTML content, and route:

```js
"New Tile Title": [
    [xCoordinate, yCoordinate],
    `
    Your HTML content here.
    `,
    `/your/route`
]
```

3. Save and reload the page. The new tile will be automatically generated.

4. Create a matching HTML page for the tile under `templates/pages`, extending the base template. For example:

```html
<!-- templates/pages/your_route.html -->
{% extends "shared/page.html" %}

{% block content %}
Your HTML content here.
{% endblock %}
```

5. Add the route to the js for the tile.