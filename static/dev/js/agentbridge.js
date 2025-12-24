/**
 * AgentBridge V2 - Chat-First SpecKit Dashboard
 * AI-Agnostic Coding Orchestrator with hot-swapping between Claude/Gemini
 */

// =============================================================================
// STATE
// =============================================================================
let state = {
    currentStep: 'specify',
    currentTab: 'chat',
    currentProvider: localStorage.getItem('agentbridge_provider') || 'claude',  // Default to Claude
    currentProject: '',
    currentFeature: '',
    isRunning: false,
    hasSpecKit: false,
    chatHistory: [],  // Per-step chat history
    stepArtifacts: {}, // Cached artifacts per step
    completedSteps: new Set(),
    browsePath: '',
    selectedBrowsePath: '',
    ws: null
};

// Ensure localStorage is set to claude if not present
if (!localStorage.getItem('agentbridge_provider')) {
    localStorage.setItem('agentbridge_provider', 'claude');
}

// Step configuration
const STEPS = ['constitution', 'specify', 'plan', 'tasks', 'implement'];
const STEP_ARTIFACTS = {
    constitution: { file: 'constitution.md', name: 'Constitution' },
    specify: { file: 'spec.md', name: 'Specification' },
    plan: { file: 'plan.md', name: 'Plan' },
    tasks: { file: 'tasks.md', name: 'Tasks' },
    implement: { file: null, name: 'Implementation' }
};

const SLASH_COMMANDS = [
    { cmd: '/clarify', desc: 'Ask clarifying questions', steps: ['specify', 'plan'] },
    { cmd: '/analyze', desc: 'Check artifact consistency', steps: ['tasks', 'implement'] },
    { cmd: '/checklist', desc: 'Generate review checklist', steps: ['plan', 'tasks', 'implement'] }
];

// =============================================================================
// INITIALIZATION
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initializeUI();
    loadProject();
    connectWebSocket();
    setupEventListeners();
});

function initializeUI() {
    setProviderUI(state.currentProvider);
    setStep(state.currentStep);
    setTab(state.currentTab);
    updateStatus('ready');
}

function setupEventListeners() {
    const input = document.getElementById('chat-input');

    // Multi-line input: Enter sends, Shift+Enter for newline
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';

        // Show/hide slash command hints
        const value = input.value;
        if (value.startsWith('/')) {
            showSlashHint(value);
        } else {
            hideSlashHint();
        }
    });

    // Close modal on overlay click
    document.getElementById('file-browser-modal').addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            closeFileBrowser();
        }
    });

    // Escape key closes modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeFileBrowser();
        }
    });
}

// =============================================================================
// PROJECT & CWD MANAGEMENT
// =============================================================================
async function loadProject() {
    try {
        const token = localStorage.getItem('access_token');
        console.log('[AgentBridge] Fetching project path from /api/agentbridge/cwd');

        const res = await fetch('/api/agentbridge/cwd', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('[AgentBridge] Response status:', res.status);

        if (res.ok) {
            const data = await res.json();
            console.log('[AgentBridge] Received data:', data);

            state.currentProject = data.cwd;
            state.hasSpecKit = data.has_agentbridge;
            updateProjectUI();

            if (state.hasSpecKit) {
                loadFeatures();
            }
        } else {
            const errorText = await res.text();
            console.error('[AgentBridge] API call failed:', res.status, errorText);
            addChatMessage('error', `Failed to load project (${res.status}): ${errorText}`);
            
            // Fallback: Use portfolio directory as default
            state.currentProject = '/home/dlybeck/Documents/portfolio';
            updateProjectUI();
            addChatMessage('warning', 'Using default project: ' + state.currentProject);
        }
    } catch (e) {
        console.error('[AgentBridge] Exception in loadProject:', e);
        
        // Fallback: Use portfolio directory as default
        state.currentProject = '/home/dlybeck/Documents/portfolio';
        updateProjectUI();
        addChatMessage('warning', `Could not load project from server. Using default: ${state.currentProject}`);
    }
}


function updateProjectUI() {
    const name = state.currentProject.split('/').pop() || state.currentProject;
    document.getElementById('project-name').textContent = name;
    document.getElementById('project-path').textContent = state.currentProject;

    // Show/hide init banner based on SpecKit initialization
    const initBanner = document.getElementById('init-banner');
    if (initBanner) {
        initBanner.style.display = state.hasSpecKit ? 'none' : 'block';
    }

    // Update status based on SpecKit initialization
    if (!state.hasSpecKit && state.currentProject) {
        addChatMessage('system', `Project loaded: ${name}. SpecKit not initialized - click "Init SpecKit" to get started.`);
    }
}

// =============================================================================
// FILE BROWSER
// =============================================================================
async function openFileBrowser() {
    document.getElementById('file-browser-modal').classList.add('visible');
    await loadRecentProjects();
    await browseDirectory(state.currentProject || null);
}

function closeFileBrowser() {
    document.getElementById('file-browser-modal').classList.remove('visible');
    state.selectedBrowsePath = '';
}

async function loadRecentProjects() {
    try {
        const token = localStorage.getItem('access_token');

        if (!token) {
            console.warn('[FileBrowser] No token for recent projects');
            document.getElementById('recent-projects').style.display = 'none';
            return;
        }

        const res = await fetch('/api/agentbridge/recent-projects', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('[FileBrowser] Recent projects response:', res.status);

        if (res.ok) {
            const data = await res.json();
            const container = document.getElementById('recent-list');
            container.innerHTML = '';

            if (data.projects.length === 0) {
                document.getElementById('recent-projects').style.display = 'none';
                console.log('[FileBrowser] No recent projects found');
                return;
            }

            document.getElementById('recent-projects').style.display = 'block';
            console.log('[FileBrowser] Loaded', data.projects.length, 'recent projects');

            data.projects.forEach(project => {
                const item = document.createElement('div');
                item.className = 'file-item' + (project.is_speckit ? ' is-speckit' : project.is_git ? ' is-git' : '');
                item.innerHTML = `
                    <i class="bi ${project.is_speckit ? 'bi-check-circle-fill' : project.is_git ? 'bi-git' : 'bi-folder'}"></i>
                    <span>${project.name}</span>
                    <span style="color: #666; font-size: 11px; margin-left: 8px;">${project.path}</span>
                    ${project.is_current_workspace ? '<span class="badge" style="background: var(--primary-color);">Workspace</span>' : ''}
                `;
                item.onclick = () => selectBrowsePath(project.path, true);
                container.appendChild(item);
            });
        } else {
            console.error('[FileBrowser] Failed to load recent projects:', res.status);
            document.getElementById('recent-projects').style.display = 'none';
        }
    } catch (e) {
        console.error('[FileBrowser] Exception loading recent projects:', e);
        document.getElementById('recent-projects').style.display = 'none';
    }
}

async function browseDirectory(path) {
    const fileListEl = document.getElementById('file-list');

    try {
        const token = localStorage.getItem('access_token');
        const url = path ? `/api/agentbridge/browse?path=${encodeURIComponent(path)}` : '/api/agentbridge/browse';
        console.log('[FileBrowser] Browsing:', url, 'Token:', token ? 'present' : 'MISSING');

        if (!token) {
            console.error('[FileBrowser] No access token found');
            fileListEl.innerHTML = `<div class="empty-state"><p style="color: var(--error-color);">Authentication required. Please login first.</p></div>`;
            return;
        }

        // Show loading state
        fileListEl.innerHTML = '<div class="empty-state"><p>Loading directories...</p></div>';

        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('[FileBrowser] Response status:', res.status);

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            console.error('[FileBrowser] Browse failed:', res.status, errData);
            fileListEl.innerHTML = `<div class="empty-state"><p style="color: var(--error-color);">Error ${res.status}: ${errData.detail || res.statusText}</p><p style="font-size: 12px; margin-top: 8px;">Path: ${path || 'home'}</p></div>`;
            return;
        }

        const data = await res.json();
        console.log('[FileBrowser] Received data:', data);

        state.browsePath = data.path;

        // Render breadcrumbs
        const breadcrumbsEl = document.getElementById('breadcrumbs');
        breadcrumbsEl.innerHTML = data.breadcrumbs.map((b, i) =>
            `<span class="breadcrumb" onclick="browseDirectory('${b.path.replace(/'/g, "\\'")}')">${b.name}</span>` +
            (i < data.breadcrumbs.length - 1 ? '<span class="breadcrumb-sep">/</span>' : '')
        ).join('');

        // Render file list
        // Filter: show directories only, hide hidden by default
        const dirs = data.entries.filter(e => e.is_dir && !e.hidden);

        console.log('[FileBrowser] Found', dirs.length, 'directories');

        if (dirs.length === 0) {
            fileListEl.innerHTML = '<div class="empty-state"><p>No subdirectories</p><p style="font-size: 12px; margin-top: 8px;">Current path: ' + data.path + '</p></div>';
            return;
        }

        fileListEl.innerHTML = dirs.map(entry => `
            <div class="file-item ${entry.is_speckit ? 'is-speckit' : entry.is_git ? 'is-git' : ''} ${entry.path === state.selectedBrowsePath ? 'selected' : ''}"
                 onclick="handleFileClick(event, '${entry.path.replace(/'/g, "\\'")}')"
                 ondblclick="browseDirectory('${entry.path.replace(/'/g, "\\'")}')">
                <i class="bi ${entry.is_speckit ? 'bi-check-circle-fill' : entry.is_git ? 'bi-git' : 'bi-folder'}"></i>
                <span>${entry.name}</span>
                <div class="badges">
                    ${entry.is_speckit ? '<span class="badge" style="background: var(--success-color);">SpecKit</span>' : ''}
                    ${entry.is_git && !entry.is_speckit ? '<span class="badge">Git</span>' : ''}
                </div>
            </div>
        `).join('');

        console.log('[FileBrowser] Rendered', dirs.length, 'directory items');
    } catch (e) {
        console.error('[FileBrowser] Exception in browseDirectory:', e);
        fileListEl.innerHTML = `<div class="empty-state"><p style="color: var(--error-color);">Failed to load directories</p><p style="font-size: 12px; margin-top: 8px;">${e.message}</p></div>`;
    }
}

function handleFileClick(event, path) {
    event.stopPropagation();
    selectBrowsePath(path, false);
}

function selectBrowsePath(path, immediate = false) {
    state.selectedBrowsePath = path;

    // Update UI to show selection
    document.querySelectorAll('.file-list .file-item').forEach(el => {
        el.classList.remove('selected');
    });

    const items = document.querySelectorAll('.file-list .file-item');
    items.forEach(item => {
        if (item.querySelector('span')?.nextSibling?.textContent?.includes(path.split('/').pop())) {
            item.classList.add('selected');
        }
    });

    if (immediate) {
        selectProject();
    }
}

async function selectProject() {
    const path = state.selectedBrowsePath || state.browsePath;
    if (!path) return;

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/cwd', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ cwd: path })
        });

        const data = await res.json();
        if (res.ok) {
            state.currentProject = data.cwd;
            state.hasSpecKit = data.has_agentbridge;
            updateProjectUI();
            closeFileBrowser();

            // Clear chat and reload
            clearChat();
            addChatMessage('system', data.message);

            if (state.hasSpecKit) {
                loadFeatures();
                loadCurrentArtifact();
            }
        } else {
            addChatMessage('error', data.detail || 'Failed to change project');
        }
    } catch (e) {
        addChatMessage('error', `Error: ${e.message}`);
    }
}

// =============================================================================
// FEATURE MANAGEMENT
// =============================================================================
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
            if (state.currentFeature) {
                select.value = state.currentFeature;
            }
        }
    } catch (e) {
        console.error('Failed to load features:', e);
    }
}

function selectFeature(feature) {
    state.currentFeature = feature;
    if (feature) {
        loadCurrentArtifact();
        addChatMessage('system', `Loaded feature: ${feature}`);
    }
}

// =============================================================================
// STEP NAVIGATION
// =============================================================================
function setStep(step) {
    state.currentStep = step;

    // Update stepper UI
    const stepOrder = STEPS;
    const currentIndex = stepOrder.indexOf(step);

    stepOrder.forEach((s, i) => {
        const el = document.getElementById(`step-${s}`);
        if (!el) return;

        el.classList.remove('active', 'completed', 'ready');

        if (s === step) {
            el.classList.add('active');
        } else if (state.completedSteps.has(s)) {
            el.classList.add('completed');
        } else if (i === currentIndex + 1 && state.completedSteps.has(step)) {
            el.classList.add('ready');
        }
    });

    // Update artifact tab name
    const artifactName = STEP_ARTIFACTS[step]?.name || 'Artifact';
    document.getElementById('artifact-tab-name').textContent = artifactName;

    // Update action button
    const actionText = document.getElementById('step-action-text');

    switch (step) {
        case 'constitution':
            actionText.textContent = 'Create Constitution';
            break;
        case 'specify':
            actionText.textContent = 'Specify';
            break;
        case 'plan':
            actionText.textContent = 'Generate Plan';
            break;
        case 'tasks':
            actionText.textContent = 'Generate Tasks';
            break;
        case 'implement':
            actionText.textContent = 'Implement';
            break;
    }

    // Update slash command hints based on step
    updateSlashHints(step);

    // Load artifact for this step
    loadCurrentArtifact();
}

function setTab(tab) {
    state.currentTab = tab;

    // Update tab UI
    document.querySelectorAll('.content-tab').forEach(el => {
        el.classList.toggle('active', el.dataset.tab === tab);
    });

    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.toggle('active', el.id === `tab-${tab}`);
    });
}

// =============================================================================
// ARTIFACT LOADING
// =============================================================================
async function loadCurrentArtifact() {
    if (!state.currentFeature) {
        showEmptyArtifact();
        return;
    }

    const artifactConfig = STEP_ARTIFACTS[state.currentStep];
    if (!artifactConfig?.file) {
        showEmptyArtifact();
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`/api/agentbridge/features/${state.currentFeature}/artifacts/${artifactConfig.file.replace('.md', '')}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const text = await res.text();
            state.stepArtifacts[state.currentStep] = text;
            displayArtifact(text);

            // Mark step as completed if artifact exists
            state.completedSteps.add(state.currentStep);
            setStep(state.currentStep); // Refresh UI
        } else if (res.status === 404) {
            showEmptyArtifact();
        }
    } catch (e) {
        console.error(`Failed to load artifact:`, e);
        showEmptyArtifact();
    }
}

function displayArtifact(text) {
    const container = document.getElementById('artifact-container');

    if (state.currentStep === 'tasks') {
        container.innerHTML = `<div class="markdown-body">${renderTasks(text)}</div>`;
    } else {
        container.innerHTML = `<div class="markdown-body">${marked.parse(text)}</div>`;
    }
}

function showEmptyArtifact() {
    const container = document.getElementById('artifact-container');
    const stepName = STEP_ARTIFACTS[state.currentStep]?.name || 'Artifact';

    container.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-file-earmark-text"></i>
            <p>No ${stepName.toLowerCase()} generated yet</p>
            <p style="font-size: 12px; color: #555;">Complete the ${state.currentStep} step to generate content</p>
        </div>
    `;
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
                <div style="opacity: ${checked ? 0.6 : 1}; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px;">
                    <input type="checkbox" ${checked ? 'checked' : ''} disabled style="width: 18px; height: 18px; accent-color: var(--success-color);">
                    <span style="${checked ? 'text-decoration: line-through; color: #888;' : ''}">${match[2]}</span>
                </div>
            `;
        }
    });

    if (taskCount > 0) {
        const pct = Math.round((completedCount / taskCount) * 100);
        html = `
            <div style="margin-bottom: 20px; padding: 16px; background: rgba(0,102,153,0.15); border: 1px solid rgba(0,102,153,0.3); border-radius: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <strong>Progress</strong>
                    <span>${completedCount}/${taskCount} tasks (${pct}%)</span>
                </div>
                <div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px;">
                    <div style="height: 100%; width: ${pct}%; background: var(--success-color); border-radius: 3px; transition: width 0.3s;"></div>
                </div>
            </div>
        ` + html;
    }

    return html || marked.parse(text);
}

// =============================================================================
// CHAT INTERFACE
// =============================================================================
function addChatMessage(type, content, sender = null) {
    const container = document.getElementById('chat-container');
    const msg = document.createElement('div');
    msg.className = `chat-message ${type}`;

    let senderLabel = '';
    if (type === 'ai') {
        senderLabel = `<div class="sender">${state.currentProvider === 'claude' ? 'Claude' : 'Gemini'}</div>`;
    } else if (type === 'user') {
        senderLabel = '<div class="sender">You</div>';
    }

    // Parse markdown for AI messages
    const renderedContent = (type === 'ai') ? marked.parse(content) : escapeHtml(content);

    msg.innerHTML = senderLabel + renderedContent;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;

    // Store in history
    state.chatHistory.push({ type, content, sender, step: state.currentStep });
}

function clearChat() {
    const container = document.getElementById('chat-container');
    container.innerHTML = '';
    state.chatHistory = [];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// SLASH COMMANDS
// =============================================================================
function updateSlashHints(step) {
    const hintContainer = document.getElementById('slash-hint');
    const relevant = SLASH_COMMANDS.filter(c => c.steps.includes(step));

    hintContainer.innerHTML = relevant.map(c => `
        <div class="slash-hint-item" onclick="insertSlashCommand('${c.cmd}')">
            <span class="cmd">${c.cmd}</span>
            <span class="desc">${c.desc}</span>
        </div>
    `).join('');
}

function showSlashHint(value) {
    const hintContainer = document.getElementById('slash-hint');
    const query = value.toLowerCase();

    const items = hintContainer.querySelectorAll('.slash-hint-item');
    let hasVisible = false;

    items.forEach(item => {
        const cmd = item.querySelector('.cmd').textContent.toLowerCase();
        const match = cmd.startsWith(query);
        item.style.display = match ? 'flex' : 'none';
        if (match) hasVisible = true;
    });

    hintContainer.classList.toggle('visible', hasVisible);
}

function hideSlashHint() {
    document.getElementById('slash-hint').classList.remove('visible');
}

function insertSlashCommand(cmd) {
    const input = document.getElementById('chat-input');
    input.value = cmd + ' ';
    input.focus();
    hideSlashHint();
}

// =============================================================================
// MESSAGE SENDING & ACTIONS
// =============================================================================
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();

    if (!text || state.isRunning) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';
    hideSlashHint();

    // Check for slash commands
    if (text.startsWith('/')) {
        const parts = text.split(' ');
        const cmd = parts[0].substring(1); // Remove leading /
        const args = parts.slice(1).join(' ');

        if (['clarify', 'analyze', 'checklist'].includes(cmd)) {
            addChatMessage('user', text);
            await runCommand(cmd, args);
            return;
        }
    }

    // Regular message - either starts a new step action or chats with running process
    addChatMessage('user', text);

    if (state.isRunning) {
        // Send to running process (chat action)
        await runCommand('chat', text);
    } else {
        // Start the current step with this input
        await runCommand(state.currentStep, text);
    }
}

async function runStepAction() {
    if (state.isRunning) return;

    const input = document.getElementById('chat-input');
    let args = input.value.trim();

    // For specify step, require input
    if (state.currentStep === 'specify' && !args) {
        addChatMessage('error', 'Please describe your feature first.');
        input.focus();
        return;
    }

    if (args) {
        addChatMessage('user', args);
        input.value = '';
        input.style.height = 'auto';
    }

    await runCommand(state.currentStep, args);
}

async function runCommand(action, args = '') {
    state.isRunning = true;
    updateStatus('running');
    document.getElementById('send-btn').disabled = true;

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
                feature: state.currentFeature,
                provider: state.currentProvider
            })
        });

        const data = await res.json();

        if (res.ok) {
            if (data.feature) {
                state.currentFeature = data.feature;
                document.getElementById('feature-select').value = state.currentFeature;
            }

            if (action === 'chat') {
                // Message was sent to stdin, output will come via WebSocket
            } else {
                // Command started, output will stream via WebSocket
            }
        } else {
            addChatMessage('error', data.detail || 'Command failed');
            state.isRunning = false;
            updateStatus('error');
        }
    } catch (e) {
        addChatMessage('error', `Error: ${e.message}`);
        state.isRunning = false;
        updateStatus('error');
    }

    document.getElementById('send-btn').disabled = false;
}

// =============================================================================
// PROVIDER SWITCHING
// =============================================================================
function setProviderUI(provider) {
    state.currentProvider = provider;
    localStorage.setItem('agentbridge_provider', provider);

    document.querySelectorAll('.provider-btn').forEach(btn => {
        btn.classList.toggle('active', btn.classList.contains(provider));
    });
}

async function switchProvider(provider) {
    if (state.isRunning) {
        addChatMessage('error', 'Cannot switch providers while a command is running.');
        return;
    }

    if (provider === state.currentProvider) return;

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

            // Show warning banner
            document.getElementById('new-provider-name').textContent = provider === 'claude' ? 'Claude' : 'Gemini';
            const warning = document.getElementById('provider-warning');
            warning.classList.add('visible');

            // Hide after 5 seconds
            setTimeout(() => {
                warning.classList.remove('visible');
            }, 5000);

            addChatMessage('system', `Switched to ${provider === 'claude' ? 'Claude' : 'Gemini'}. Note: Previous AI context was not carried over.`);
        } else {
            addChatMessage('error', data.detail || 'Failed to switch provider');
        }
    } catch (e) {
        addChatMessage('error', `Error: ${e.message}`);
    }
}

// =============================================================================
// WEBSOCKET
// =============================================================================
function connectWebSocket() {
    const token = localStorage.getItem('access_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/agentbridge/ws?token=${token}`;

    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        console.log('WebSocket connected');
    };

    state.ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg.type === 'status' && msg.data === 'completed') {
            state.isRunning = false;

            if (msg.exit_code === 0) {
                updateStatus('ready');

                // Mark current step as completed
                state.completedSteps.add(state.currentStep);
                setStep(state.currentStep); // Refresh UI

                // Reload artifact and switch to artifact tab to show result
                setTimeout(() => {
                    loadCurrentArtifact();
                    loadFeatures();
                    // Auto-switch to artifact tab if there's an artifact for this step
                    if (STEP_ARTIFACTS[state.currentStep]?.file) {
                        setTab('artifact');
                    }
                }, 500);

                // Suggest next step
                const stepIndex = STEPS.indexOf(state.currentStep);
                const stepName = capitalizeFirst(state.currentStep);
                if (stepIndex < STEPS.length - 1) {
                    const nextStep = STEPS[stepIndex + 1];
                    const nextStepName = capitalizeFirst(nextStep);
                    addChatMessage('system', `${stepName} complete! Ready to proceed to ${nextStepName}.`);
                } else {
                    addChatMessage('system', 'Implementation complete!');
                }
            } else {
                updateStatus('error');
                addChatMessage('error', `Process exited with code ${msg.exit_code}`);
            }
        } else if (msg.type === 'stdout' || msg.type === 'stderr') {
            // Stream AI output to chat
            addChatMessage('ai', msg.data);
        } else if (msg.type === 'status') {
            addChatMessage('system', msg.data);
        }
    };

    state.ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (e) => {
        console.error('WebSocket error:', e);
    };
}

// =============================================================================
// STATUS
// =============================================================================
function updateStatus(status) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    const actionBtn = document.getElementById('step-action-btn');

    dot.className = 'status-dot ' + status;

    switch (status) {
        case 'ready':
            text.textContent = 'Ready';
            actionBtn.disabled = false;
            break;
        case 'running':
            text.textContent = 'Running...';
            actionBtn.disabled = true;
            break;
        case 'error':
            text.textContent = 'Error';
            actionBtn.disabled = false;
            break;
        default:
            text.textContent = status;
    }
}

// =============================================================================
// HELPERS
// =============================================================================
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// =============================================================================
// INIT SPECKIT
// =============================================================================
async function initSpecKit() {
    if (state.isRunning) {
        addChatMessage('error', 'Cannot initialize while a command is running.');
        return;
    }

    state.isRunning = true;
    updateStatus('running');
    addChatMessage('system', `Initializing SpecKit with ${state.currentProvider}...`);

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/agentbridge/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ provider: state.currentProvider })
        });

        const data = await res.json();

        if (res.ok) {
            state.hasSpecKit = true;
            updateProjectUI();
            addChatMessage('system', data.message || 'SpecKit initialized successfully!');
            loadFeatures();
        } else {
            addChatMessage('error', data.detail || 'Failed to initialize SpecKit');
        }
    } catch (e) {
        addChatMessage('error', `Error: ${e.message}`);
    }

    state.isRunning = false;
    updateStatus('ready');
}
