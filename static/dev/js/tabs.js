/* Tab Content Management */

let currentTab = 'files';
let currentFilePath = localStorage.getItem('working_directory') || '~';
let separateTerminal = null;
let separateWs = null;
let separateFitAddon = null;

function switchTab(tabName) {
    currentTab = tabName;
    Alpine.store('dashboard').switchTab(tabName);
    updateTabContent();
}

function updateTabContent() {
    const tabContent = document.getElementById('tabContent');
    const store = Alpine.store('dashboard');

    switch(currentTab) {
        case 'files':
            loadFileBrowser(currentFilePath);
            break;

        case 'terminal':
            initSeparateTerminal();
            break;

        case 'preview':
            const htmlMatch = store.terminalOutput.match(/<html[\s\S]*<\/html>/i);
            if (htmlMatch) {
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                tabContent.innerHTML = '';
                tabContent.appendChild(iframe);
                iframe.contentDocument.write(htmlMatch[0]);
            } else {
                tabContent.innerHTML = '<div class="placeholder">Preview will appear here when Claude generates HTML or images...</div>';
            }
            break;

        case 'logs':
            const cleanLogs = store.terminalOutput.replace(/\x1b\[[0-9;]*m/g, '');
            tabContent.innerHTML = '<pre style="padding: 16px; overflow: auto; background: #1a1a1a; color: #f8f8f8; font-size: 12px; height: 100%;">' +
                (cleanLogs || 'No output yet...') + '</pre>';
            break;
    }
}

function initSeparateTerminal() {
    const tabContent = document.getElementById('tabContent');

    if (separateTerminal && separateWs && separateWs.readyState === WebSocket.OPEN) {
        tabContent.innerHTML = '<div id="separateTerminalContainer" style="width: 100%; height: 100%;"></div>';
        const container = document.getElementById('separateTerminalContainer');
        separateTerminal.open(container);
        separateFitAddon.fit();
        separateTerminal.focus();
        return;
    }

    tabContent.innerHTML = '<div id="separateTerminalContainer" style="width: 100%; height: 100%;"></div>';
    const container = document.getElementById('separateTerminalContainer');

    if (separateTerminal) {
        separateTerminal.dispose();
    }
    if (separateWs && separateWs.readyState === WebSocket.OPEN) {
        separateWs.close();
    }

    separateFitAddon = new FitAddon.FitAddon();
    separateTerminal = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#1a1a1a',
            foreground: '#f8f8f8',
            cursor: '#f8f8f8'
        }
    });

    separateTerminal.loadAddon(separateFitAddon);
    separateTerminal.open(container);
    separateFitAddon.fit();
    separateTerminal.focus();

    const workingDir = localStorage.getItem('working_directory') || '~';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const sessionId = 'terminal_tab_' + Date.now();
    const token = localStorage.getItem('access_token');
    const wsUrl = `${protocol}//${window.location.host}/dev/ws/terminal?cwd=${encodeURIComponent(workingDir)}&session=${sessionId}&token=${encodeURIComponent(token)}`;
    separateWs = new WebSocket(wsUrl);

    separateWs.onopen = () => {
        console.log('Separate terminal connected');
    };

    separateWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'output') {
            separateTerminal.write(data.data);
        }
    };

    separateTerminal.onData((data) => {
        if (separateWs.readyState === WebSocket.OPEN) {
            separateWs.send(JSON.stringify({type: 'input', data}));
        }
    });

    const resizeObserver = new ResizeObserver(() => {
        if (separateFitAddon && currentTab === 'terminal') {
            separateFitAddon.fit();
            if (separateWs && separateWs.readyState === WebSocket.OPEN) {
                separateWs.send(JSON.stringify({
                    type: 'resize',
                    rows: separateTerminal.rows,
                    cols: separateTerminal.cols
                }));
            }
        }
    });
    resizeObserver.observe(container);
}

async function loadFileBrowser(path) {
    const tabContent = document.getElementById('tabContent');
    const token = localStorage.getItem('access_token');

    tabContent.innerHTML = `
        <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
            <div style="margin-bottom: 12px;">
                <button onclick="navigateUp()" style="background: #444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-right: 8px;">⬆️ Up</button>
                <span style="color: #888; font-family: monospace; font-size: 13px;" id="currentPath">${path}</span>
            </div>
            <div id="fileList" style="flex: 1; overflow-y: auto; background: #2d2d2d; border-radius: 4px; padding: 8px;">
                <div style="color: #888; text-align: center; padding: 20px;">Loading...</div>
            </div>
        </div>
    `;

    try {
        const response = await fetch('/dev/api/list-directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ path })
        });

        const data = await response.json();
        const allItems = [...(data.directories || []), ...(data.files || [])];
        displayFiles(allItems, path);
    } catch (error) {
        document.getElementById('fileList').innerHTML = '<div style="color: #f88; padding: 20px;">Error loading files</div>';
    }
}

function displayFiles(files, path) {
    const fileList = document.getElementById('fileList');

    if (!fileList) return;

    if (files.length === 0) {
        fileList.innerHTML = '<div style="color: #888; padding: 20px;">No files or folders</div>';
        return;
    }

    fileList.innerHTML = files.map(file => {
        const icon = file.type === 'directory' ? '📁' : '📄';
        return `
            <div onclick="openFile('${file.path}')" style="padding: 8px 12px; margin: 4px 0; background: #383838; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s;"
                 onmouseover="this.style.background='#444'" onmouseout="this.style.background='#383838'">
                <span style="font-size: 16px;">${icon}</span>
                <span style="color: #f8f8f8; font-size: 14px;">${file.name}</span>
            </div>
        `;
    }).join('');
}

async function openFile(path) {
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch('/dev/api/list-directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ path })
        });

        if (response.ok) {
            currentFilePath = path;
            document.getElementById('currentPath').textContent = path;
            const data = await response.json();
            const allItems = [...(data.directories || []), ...(data.files || [])];
            displayFiles(allItems, path);
        } else {
            console.log('Not a directory, would view file:', path);
        }
    } catch (error) {
        console.error('Error opening file:', error);
    }
}

function navigateUp() {
    const token = localStorage.getItem('access_token');
    fetch('/dev/api/parent-directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ path: currentFilePath })
    })
    .then(res => res.json())
    .then(data => {
        if (data.parent) {
            currentFilePath = data.parent;
            loadFileBrowser(data.parent);
        }
    });
}
