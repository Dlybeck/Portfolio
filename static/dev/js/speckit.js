/**
 * Speckit Dashboard Controller (v2 - Stepper UI)
 */

// State
let currentPhase = 'specify';
let currentModel = localStorage.getItem('speckit_model') || 'claude';
let isRunning = false;
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setModel(currentModel);
    connectWebSocket();
    
    // Try to load existing state
    refreshArtifact('spec');
    refreshArtifact('plan');
    
    // Handle enter key in input
    document.getElementById('main-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAction();
    });
    
    // Initial check to get CWD
    runCommand('check', '');
});

function setModel(model) {
    // Prevent switching during execution
    if (isRunning) {
        log('Cannot switch models during execution', 'stderr');
        return;
    }

    currentModel = model;
    localStorage.setItem('speckit_model', model);

    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.classList.toggle('active', btn.innerText.toLowerCase() === model);
    });
}

function setPhase(phase) {
    currentPhase = phase;
    
    // Update Stepper UI
    const steps = ['specify', 'plan', 'tasks', 'implement'];
    let activeFound = false;
    
    steps.forEach((s, index) => {
        const el = document.getElementById(`step-${s}`);
        el.classList.remove('active', 'completed');
        
        if (s === phase) {
            el.classList.add('active');
            activeFound = true;
        } else if (!activeFound) {
            el.classList.add('completed');
        }
    });

    // Update View Visibility
    document.querySelectorAll('.phase-view').forEach(el => el.style.display = 'none');
    document.getElementById(`view-${phase}`).style.display = 'block';

    // Update Action Bar Context
    updateActionBar(phase);

    // Refresh Data
    if (phase !== 'specify') refreshArtifact(phase);
}

function updateActionBar(phase) {
    const input = document.getElementById('main-input');
    const btnText = document.getElementById('action-text');
    const inputWrapper = document.getElementById('input-wrapper');

    if (phase === 'specify') {
        input.style.display = 'block';
        input.placeholder = "Enter a goal (e.g. 'Add dark mode')...";
        btnText.innerText = "Generate Spec";
    } else if (phase === 'plan') {
        input.style.display = 'none';
        btnText.innerText = "Generate Plan";
    } else if (phase === 'tasks') {
        input.style.display = 'none';
        btnText.innerText = "Generate Tasks";
    } else if (phase === 'implement') {
        input.style.display = 'none';
        btnText.innerText = "Start Build";
    }
}

async function handleAction() {
    if (isRunning) return;

    const input = document.getElementById('main-input');
    let args = "";

    if (currentPhase === 'specify') {
        if (!input.value.trim()) {
            alert("Please enter a goal.");
            return;
        }
        args = input.value.trim();
    }

    // Auto-open logs
    document.getElementById('logs-panel').classList.add('open');
    
    await runCommand(currentPhase, args);
}

// Toggle Logs
function toggleLogs() {
    document.getElementById('logs-panel').classList.toggle('open');
}

// API & WebSocket Logic
function connectWebSocket() {
    const token = localStorage.getItem('access_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/speckit/ws?token=${token}`;

    ws = new WebSocket(wsUrl);
    
    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'status' && msg.data === 'completed') {
            isRunning = false;
            log(`Process finished (Exit: ${msg.exit_code})`, 'info');
            refreshArtifact(currentPhase);
            
            // Auto-advance logic could go here
            if (msg.exit_code === 0) {
               // maybe suggest next step?
            }
        } else {
            log(msg.data, msg.type);
        }
    };
}

function log(text, type) {
    const container = document.getElementById('logs-content');
    const div = document.createElement('div');
    div.style.color = type === 'stderr' ? '#ff6b6b' : (type === 'info' ? '#4dabf7' : '#adb5bd');
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function runCommand(action, args) {
    // If not 'check', set running state
    if (action !== 'check') {
        isRunning = true;
        log(`>>> Starting ${action}...`, 'info');
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/speckit/run', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                action: action,
                args: args,
                ai_model: currentModel
            })
        });
        
        const data = await res.json();
        
        if (data.cwd) {
            document.getElementById('cwd-display').textContent = data.cwd;
        }
        
    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
        isRunning = false;
    }
}

async function refreshArtifact(type) {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`/api/speckit/artifacts/${type}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 404) {
            // Keep default empty state
            return;
        }

        const text = await res.text();
        
        if (type === 'spec') {
            document.getElementById('spec-display').innerHTML = marked.parse(text);
            // If we found a spec, maybe we should show it
            if(currentPhase === 'specify' && text.length > 0) {
                // Optional: visual feedback
            }
        } else if (type === 'plan') {
            document.getElementById('plan-display').innerHTML = marked.parse(text);
        } else if (type === 'tasks') {
            renderTasks(text);
        }

    } catch (e) {
        console.error("Artifact fetch failed", e);
    }
}

function renderTasks(text) {
    const container = document.getElementById('tasks-list');
    // Regex for - [ ] or - [x]
    const lines = text.split('\n');
    let html = '';
    let found = false;

    lines.forEach(line => {
        const match = line.match(/^\s*- \[(x| )] (.*)/);
        if (match) {
            found = true;
            const checked = match[1] === 'x';
            html += `
                <div class="task-item" style="opacity: ${checked ? 0.5 : 1}">
                    <input type="checkbox" class="task-check" ${checked ? 'checked' : ''} disabled>
                    <span style="${checked ? 'text-decoration: line-through' : ''}">${match[2]}</span>
                </div>
            `;
        }
    });

    if (found) {
        container.innerHTML = html;
    } else if (text.trim().length > 0) {
        container.innerHTML = `<div class="markdown-body">${marked.parse(text)}</div>`;
    }
}