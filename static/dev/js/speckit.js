/**
 * Speckit Dashboard Controller
 * Handles UI state, API calls, and WebSocket streaming.
 */

// State
let currentPhase = 'specify';
let ws = null;
let isRunning = false;

// DOM Elements
const modelSelect = document.getElementById('modelSelect');
const logsContent = document.getElementById('logsContent');
const logsPanel = document.getElementById('logsPanel');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/dev/login';
        return;
    }

    // Load saved model preference
    const savedModel = localStorage.getItem('speckit_model');
    if (savedModel) {
        modelSelect.value = savedModel;
    }

    // Initialize WebSocket
    connectWebSocket();

    // Load initial artifacts
    refreshArtifact('spec');
    refreshArtifact('plan');
});

// Model Switcher
modelSelect.addEventListener('change', (e) => {
    localStorage.setItem('speckit_model', e.target.value);
    log(`Switched model to ${e.target.value}`, 'info');
});

// Tab Switching
function switchTab(phase) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Update views
    document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
    document.getElementById(`view-${phase}`).style.display = 'block';

    currentPhase = phase;
    
    // Refresh data for this phase
    if (phase === 'plan') refreshArtifact('plan');
    if (phase === 'tasks') refreshArtifact('tasks');
}

// Log Management
function log(msg, type = 'stdout') {
    const div = document.createElement('div');
    div.className = type;
    div.textContent = msg; // Text content for safety
    logsContent.appendChild(div);
    logsContent.scrollTop = logsContent.scrollHeight;
}

function toggleLogs() {
    logsPanel.classList.toggle('collapsed');
    const icon = document.getElementById('logsChevron');
    if (logsPanel.classList.contains('collapsed')) {
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

// WebSocket Connection
function connectWebSocket() {
    const token = localStorage.getItem('access_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/speckit/ws?token=${token}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        log('Connected to Speckit stream.', 'info');
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'status' && msg.data === 'completed') {
                isRunning = false;
                log(`Process finished with exit code ${msg.exit_code}`, 'info');
                // Refresh current view artifacts
                refreshArtifact(currentPhase);
            } else {
                log(msg.data, msg.type);
            }
        } catch (e) {
            log('Error parsing WS message: ' + event.data, 'stderr');
        }
    };

    ws.onclose = () => {
        log('Connection lost. Reconnecting in 5s...', 'stderr');
        setTimeout(connectWebSocket, 5000);
    };
}

// API Interaction
async function runCommand(action) {
    if (isRunning) {
        alert('A process is already running. Please wait.');
        return;
    }

    const model = modelSelect.value;
    let args = "";

    if (action === 'specify') {
        const input = document.getElementById('spec-input');
        if (!input.value.trim()) {
            alert('Please enter a goal.');
            return;
        }
        args = input.value.trim();
    }

    // Open logs if closed
    if (logsPanel.classList.contains('collapsed')) {
        toggleLogs();
    }

    log(`Starting ${action} with ${model}...`, 'info');
    isRunning = true;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/speckit/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                action: action,
                args: args,
                ai_model: model
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Request failed');
        }
    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
        isRunning = false;
    }
}

async function refreshArtifact(type) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/speckit/artifacts/${type}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 404) {
            // Handle missing file gracefully
            if (type === 'plan') document.getElementById('plan-display').innerHTML = '<em>No plan found.</em>';
            return;
        }

        const text = await response.text();

        if (type === 'spec') {
            document.getElementById('spec-display').innerHTML = marked.parse(text);
        } else if (type === 'plan') {
            document.getElementById('plan-display').innerHTML = marked.parse(text);
        } else if (type === 'tasks') {
            renderTasks(text); // Custom parser for tasks if they are markdown lists
        }

    } catch (e) {
        console.error(`Failed to fetch ${type}:`, e);
    }
}

// Simple Task Parser (Markdown Checkboxes -> HTML)
function renderTasks(markdown) {
    const container = document.getElementById('tasks-list');
    container.innerHTML = '';
    
    // Regex to find [ ] or [x]
    const lines = markdown.split('\n');
    let found = false;

    lines.forEach(line => {
        const match = line.match(/^\s*- \[(x| )] (.*)/);
        if (match) {
            found = true;
            const isChecked = match[1] === 'x';
            const text = match[2];
            
            const div = document.createElement('div');
            div.className = 'task-item';
            div.innerHTML = `
                <input type="checkbox" class="task-check" ${isChecked ? 'checked' : ''} disabled>
                <span class="task-label" style="${isChecked ? 'text-decoration:line-through; color:#666;' : ''}">${text}</span>
            `;
            container.appendChild(div);
        }
    });

    if (!found) {
        // Maybe it's JSON?
        try {
            const tasks = JSON.parse(markdown);
            if (Array.isArray(tasks)) {
                tasks.forEach(task => {
                    const div = document.createElement('div');
                    div.className = 'task-item';
                    div.innerHTML = `
                        <input type="checkbox" class="task-check" ${task.status === 'completed' ? 'checked' : ''} disabled>
                        <span class="task-label">${task.description}</span>
                    `;
                    container.appendChild(div);
                });
            }
        } catch (e) {
            // Just render as markdown if all else fails
            container.innerHTML = `<div class="markdown-body" style="padding:16px;">${marked.parse(markdown)}</div>`;
        }
    }
}
