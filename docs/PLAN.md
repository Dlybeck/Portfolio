# Agor Integration Plan

This document outlines the plan to integrate Agor into the existing developer dashboard, allowing for a seamless switch between the VS Code editor and the Agor interface.

## 1. Prerequisites: Install and Run Agor

Before making any code changes, we need to install Agor and ensure it can run locally.

1.  **Install Agor:** Agor is a Node.js application and can be installed globally using npm:

    ```bash
    npm install -g @preset-io/agor
    ```

2.  **Initialize Agor:** In a new terminal, navigate to a directory where you want to store Agor's data (e.g., `~/agor-data`) and run the initialization command:

    ```bash
    mkdir ~/agor-data
    cd ~/agor-data
    agor init
    ```

3.  **Start the Agor Daemon:** Once initialized, start the Agor daemon:

    ```bash
    agor daemon start
    ```

    By default, the Agor web interface will be available at `http://localhost:5678`. We will use this port for the proxy.

## 2. Backend Changes: Create the Agor Proxy

To integrate Agor securely and avoid CORS issues, we'll create a new proxy route in the FastAPI backend.

-   **File to Modify:** `apis/route_dev.py`
-   **Action:** Add a new route handler, `agor_proxy`, that forwards requests to the Agor service running on `localhost:5678`. This will be similar to the existing `vscode_proxy` function. The new route will be `/dev/agor/{path:path}`.

## 3. Frontend Changes: Update the Dashboard

We'll modify the main dashboard to include both VS Code and Agor in switchable iframes.

-   **File to Modify:** `templates/dev/dashboard.html`
-   **Actions:**
    1.  **Add Agor Iframe:** Add a new `iframe` with `id="agor-iframe"` alongside the existing `id="vscode-iframe"`. Its `src` will point to our new `/dev/agor/` proxy endpoint.
    2.  **Add Switcher UI:** Add two buttons or tabs (e.g., "VS Code" and "Agor") to the UI.
    3.  **Initial State:** Use CSS to make the Agor iframe hidden by default.

-   **File to Create/Modify:** `static/dev/js/tabs.js` (or similar)
-   **Actions:**
    1.  **Add Event Listeners:** Attach click event listeners to the "VS Code" and "Agor" buttons.
    2.  **Implement Switching Logic:**
        -   When the "Agor" button is clicked, hide the VS Code iframe and show the Agor iframe.
        -   When the "VS Code" button is clicked, hide the Agor iframe and show the VS Code iframe.
    3.  **Update Active State:** Add a CSS class (e.g., `active`) to the currently selected button to provide visual feedback.

## 4. Finalizing the Integration

Once the backend and frontend changes are complete, the new workflow will be:

1.  Start the main FastAPI application (`python main.py`).
2.  Start the `code-server` (if not already running).
3.  Start the Agor daemon (`agor daemon start`).
4.  Navigate to the `/dev` endpoint in your browser. You will see the familiar VS Code interface, along with the new buttons to switch to Agor.

This plan will provide a seamless experience for switching between the two development environments, giving you the best of both worlds.
