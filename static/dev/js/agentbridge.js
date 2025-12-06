/**
 * AgentBridge Dashboard Controller
 * AI-Agnostic Coding Orchestrator
 */

// State
let currentPhase = 'specify';
let currentProvider = localStorage.getItem('agentbridge_provider') || 'claude';
let currentFeature = '';
let currentCwd = '';
let hasAgentBridge = false;
let isRunning = false;
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setProviderUI(currentProvider);
    connectWebSocket();
    loadCwd();  // Load current working directory first

    // Handle enter key in input
    document.getElementById('main-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAction();
    });

    // Handle enter key in cwd input
    document.getElementById('cwd-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') changeCwd();
    });

    // Feature selector change
    document.getElementById('feature-select').addEventListener('change', (e) => {
        currentFeature = e.target.value;
        if (currentFeature) {
            loadFeatureArtifacts(currentFeature);
        }
    });
});

// Working Directory Functions
async function loadCwd() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/cwd', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const data = await res.json();
            currentCwd = data.cwd;
            hasAgentBridge = data.has_agentbridge;
            document.getElementById('cwd-input').value = currentCwd;
            updateCwdUI();

            // Load config and features after cwd is set
            if (hasAgentBridge) {
                loadConfig();
                loadFeatures();
            }
        }
    } catch (e) {
        console.error('Failed to load cwd', e);
    }
}

async function changeCwd() {
    if (isRunning) {
        log('Cannot change directory during execution', 'stderr');
        return;
    }

    const newCwd = document.getElementById('cwd-input').value.trim();
    if (!newCwd) {
        alert('Please enter a directory path');
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/cwd', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ cwd: newCwd })
        });

        const data = await res.json();
        if (res.ok) {
            currentCwd = data.cwd;
            hasAgentBridge = data.has_agentbridge;
            document.getElementById('cwd-input').value = currentCwd;
            updateCwdUI();
            log(data.message, 'status');

            // Reload config and features
            if (hasAgentBridge) {
                loadConfig();
                loadFeatures();
            } else {
                // Clear features since AgentBridge not initialized
                const select = document.getElementById('feature-select');
                while (select.options.length > 1) {
                    select.remove(1);
                }
            }
        } else {
            log(`Failed: ${data.detail}`, 'stderr');
        }
    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
    }
}

async function initAgentBridge() {
    try {
        const token = localStorage.getItem('access_token');
        log(`Initializing SpecKit with ${currentProvider}...`, 'status');

        const res = await fetch('/api/agentbridge/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ provider: currentProvider })
        });

        const data = await res.json();
        if (res.ok) {
            hasAgentBridge = true;
            updateCwdUI();
            log(data.message, 'status');
            loadConfig();
            loadFeatures();
        } else {
            log(`Failed: ${data.detail}`, 'stderr');
        }
    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
    }
}

function updateCwdUI() {
    const initBtn = document.getElementById('init-btn');
    const statusBadge = document.getElementById('status-badge');

    if (hasAgentBridge) {
        initBtn.style.display = 'none';
        setStatus('ready');
    } else {
        initBtn.style.display = 'inline-block';
        statusBadge.className = 'status-badge warning';
        statusBadge.textContent = 'Not Initialized';
    }
}

function setProviderUI(provider) {
    currentProvider = provider;
    localStorage.setItem('agentbridge_provider', provider);

    document.querySelectorAll('.provider-btn').forEach(btn => {
        const isActive = btn.classList.contains(provider);
        btn.classList.toggle('active', isActive);
    });
}

async function switchProvider(provider) {
    if (isRunning) {
        log('Cannot switch providers during execution', 'stderr');
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ provider })
        });

        const data = await res.json();
        if (res.ok) {
            setProviderUI(provider);
            log(`Switched to ${provider}`, 'status');
        } else {
            log(`Switch failed: ${data.detail}`, 'stderr');
        }
    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
    }
}

function setPhase(phase) {
    currentPhase = phase;

    const steps = ['specify', 'plan', 'tasks', 'implement', 'status'];
    let activeFound = false;

    steps.forEach((s) => {
        const el = document.getElementById(`step-${s}`);
        if (!el) return;
        el.classList.remove('active', 'completed');

        if (s === phase) {
            el.classList.add('active');
            activeFound = true;
        } else if (!activeFound) {
            el.classList.add('completed');
        }
    });

    // Update view visibility
    document.querySelectorAll('.phase-view').forEach(el => el.classList.remove('active'));
    const view = document.getElementById(`view-${phase}`);
    if (view) view.classList.add('active');

    updateActionBar(phase);
}

function updateActionBar(phase) {
    const input = document.getElementById('main-input');
    const btnText = document.getElementById('action-text');

    switch (phase) {
        case 'specify':
            input.style.display = 'block';
            input.placeholder = "Describe your feature...";
            btnText.innerText = "Specify";
            break;
        case 'plan':
            input.style.display = 'none';
            btnText.innerText = "Generate Plan";
            break;
        case 'tasks':
            input.style.display = 'none';
            btnText.innerText = "Generate Tasks";
            break;
        case 'implement':
            input.style.display = 'none';
            btnText.innerText = "Implement Next";
            break;
        case 'status':
            input.style.display = 'none';
            btnText.innerText = "Refresh Status";
            break;
    }
}

async function handleAction() {
    if (isRunning) return;

    const input = document.getElementById('main-input');
    let args = "";

    if (currentPhase === 'specify') {
        if (!input.value.trim()) {
            alert("Please describe your feature.");
            return;
        }
        args = input.value.trim();
    }

    // Open logs panel
    document.getElementById('logs-panel').classList.add('open');

    await runCommand(currentPhase, args);
}

function toggleLogs() {
    document.getElementById('logs-panel').classList.toggle('open');
}

// WebSocket connection
function connectWebSocket() {
    const token = localStorage.getItem('access_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/agentbridge/ws?token=${token}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        log('Connected to AgentBridge', 'status');
    };

    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg.type === 'status' && msg.data === 'completed') {
            isRunning = false;
            setStatus('ready');
            log(`Process finished (Exit: ${msg.exit_code})`, 'status');

            // Refresh artifacts after completion
            setTimeout(() => {
                if (currentFeature) {
                    loadFeatureArtifacts(currentFeature);
                }
                loadFeatures();

                if (msg.exit_code === 0) {
                    setTimeout(() => {
                        document.getElementById('logs-panel').classList.remove('open');
                    }, 2000);
                }
            }, 500);
        } else {
            log(msg.data, msg.type);
        }
    };

    ws.onclose = () => {
        log('Disconnected. Reconnecting...', 'stderr');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
        log('WebSocket error', 'stderr');
    };
}

function log(text, type) {
    const container = document.getElementById('logs-content');
    const div = document.createElement('div');
    div.className = type || 'stdout';
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function setStatus(status) {
    const badge = document.getElementById('status-badge');
    badge.className = 'status-badge ' + status;
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}

async function loadConfig() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/config', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const config = await res.json();
            setProviderUI(config.provider);
        }
    } catch (e) {
        console.error('Failed to load config', e);
    }
}

async function loadFeatures() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/features', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const data = await res.json();
            const select = document.getElementById('feature-select');

            // Clear existing options except first
            while (select.options.length > 1) {
                select.remove(1);
            }

            // Add features
            data.features.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f.name;
                opt.textContent = f.name;
                select.appendChild(opt);
            });

            // Select current feature if set
            if (currentFeature) {
                select.value = currentFeature;
            }
        }
    } catch (e) {
        console.error('Failed to load features', e);
    }
}

async function loadFeatureArtifacts(feature) {
    const artifacts = ['spec', 'plan', 'tasks'];

    for (const artifact of artifacts) {
        try {
            const token = localStorage.getItem('access_token');
            const res = await fetch(`/api/agentbridge/features/${feature}/artifacts/${artifact}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const text = await res.text();
                displayArtifact(artifact, text);
            } else if (res.status === 404) {
                // Artifact doesn't exist yet - this is expected, show placeholder
                displayArtifact(artifact, null);
            }
        } catch (e) {
            console.error(`Failed to load ${artifact}`, e);
        }
    }
}

function displayArtifact(type, text) {
    const placeholderHtml = `<div style="color: #888; font-style: italic; padding: 20px; text-align: center;">
        Not generated yet. Click the "${type === 'plan' ? 'Generate Plan' : 'Generate Tasks'}" button above to create this artifact.
    </div>`;

    if (type === 'plan') {
        const el = document.getElementById('plan-display');
        el.innerHTML = text ? marked.parse(text) : placeholderHtml;
    } else if (type === 'tasks') {
        const el = document.getElementById('tasks-display');
        el.innerHTML = text ? renderTasks(text) : placeholderHtml;
    }
}

function renderTasks(text) {
    const lines = text.split('\n');
    let html = '';
    let taskCount = 0;
    let completedCount = 0;

    lines.forEach(line => {
        const match = line.match(/^\s*- \[(x| )\] (.*)/);
        if (match) {
            taskCount++;
            const checked = match[1] === 'x';
            if (checked) completedCount++;

            html += `
                <div class="task-item" style="opacity: ${checked ? 0.5 : 1}; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px;">
                    <input type="checkbox" ${checked ? 'checked' : ''} disabled style="width: 18px; height: 18px; accent-color: #238636;">
                    <span style="${checked ? 'text-decoration: line-through; color: #888;' : ''}">${match[2]}</span>
                </div>
            `;
        }
    });

    if (taskCount > 0) {
        const pct = Math.round((completedCount / taskCount) * 100);
        html = `
            <div style="margin-bottom: 16px; padding: 12px; background: rgba(0,102,153,0.2); border-radius: 8px;">
                <strong>Progress:</strong> ${completedCount}/${taskCount} tasks (${pct}%)
                <div style="height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 8px;">
                    <div style="height: 100%; width: ${pct}%; background: #238636; border-radius: 2px;"></div>
                </div>
            </div>
        ` + html;
    }

    return html || marked.parse(text);
}

async function runCommand(action, args) {
    if (action === 'check') return;

    isRunning = true;
    setStatus('running');
    log(`>>> Running ${action}...`, 'status');

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                action: action,
                args: args,
                feature: currentFeature,
                provider: currentProvider
            })
        });

        const data = await res.json();

        if (data.feature) {
            currentFeature = data.feature;
            document.getElementById('feature-select').value = currentFeature;
        }

    } catch (e) {
        log(`Error: ${e.message}`, 'stderr');
        isRunning = false;
        setStatus('error');
    }
}
