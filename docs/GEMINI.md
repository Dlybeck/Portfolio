## Project Overview

This project is a web-based, AI-driven development dashboard built with Python and FastAPI. It serves as a private extension to a personal portfolio website, offering remote access to a development environment from any device. The application features an AI assistant powered by Anthropic's Claude, a real-time terminal, a file manager, and a preview pane for web development.

The backend is built with FastAPI and utilizes WebSockets for real-time communication. Authentication is handled using JWT with `python-jose` and `passlib`. The frontend is built with vanilla JavaScript, `xterm.js` for the terminal, and other libraries for UI components.

## Building and Running

### Local Development (with Uvicorn)

To run the application locally, execute the following command:

```bash
python main.py
```

The application will be accessible at `http://<tailscale-ip>:8080` if Tailscale is detected, otherwise at `http://127.0.0.1:8080`.

### Local Development (with Docker)

To build and run the application with Docker, use the following commands:

**Build:**
```bash
docker build -t myapp .
```

**Run:**
```bash
docker run -p 8080:8080 myapp
```

The application will be accessible at `http://localhost:8080`.

## Development Conventions

*   **Backend:** The backend follows a modular structure, with different functionalities separated into different routers in the `apis` directory. Core logic is placed in the `core` directory, and services in the `services` directory.
*   **Frontend:** The frontend uses vanilla JavaScript and is organized into different files in the `static/dev/js` directory.
*   **Styling:** CSS files are located in `static/css` and `static/dev/css`.
*   **Templates:** HTML templates are located in the `templates` directory and use the Jinja2 templating engine.
*   **Dependencies:** Python dependencies are managed with `pip` and are listed in the `requirements.txt` file.
