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
        console.log('Separate terminal connected (plain bash)');
        // Don't auto-start Claude - this is just a bash terminal
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
            // It's a directory
            currentFilePath = path;
            document.getElementById('currentPath').textContent = path;
            const data = await response.json();
            const allItems = [...(data.directories || []), ...(data.files || [])];
            displayFiles(allItems, path);
        } else {
            // It's a file - view it
            viewFile(path);
        }
    } catch (error) {
        console.error('Error opening file:', error);
    }
}

async function viewFile(path) {
    // Switch to preview tab
    currentTab = 'preview';
    Alpine.store('dashboard').switchTab('preview');

    // Update active tab UI
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.tab:nth-child(3)').classList.add('active');

    const tabContent = document.getElementById('tabContent');
    const fileExt = path.split('.').pop().toLowerCase();
    const token = localStorage.getItem('access_token');

    // Show progress bar
    tabContent.innerHTML = `
        <div style="padding: 32px; text-align: center;">
            <div style="color: #888; margin-bottom: 16px;">Loading file...</div>
            <div style="background: #2d2d2d; border-radius: 8px; overflow: hidden; height: 24px; width: 100%; max-width: 400px; margin: 0 auto;">
                <div id="progressBar" style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: 0%; transition: width 0.3s;"></div>
            </div>
            <div id="progressText" style="color: #888; margin-top: 8px; font-size: 13px;">0%</div>
        </div>
    `;

    try {
        const response = await fetch(`/dev/api/read-file?path=${encodeURIComponent(path)}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error('Failed to load file');
        }

        const contentLength = response.headers.get('content-length');
        const total = parseInt(contentLength, 10);
        let loaded = 0;
        const reader = response.body.getReader();
        const chunks = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            chunks.push(value);
            loaded += value.length;

            if (total) {
                const percent = Math.round((loaded / total) * 100);
                const progressBar = document.getElementById('progressBar');
                const progressText = document.getElementById('progressText');
                if (progressBar && progressText) {
                    progressBar.style.width = percent + '%';
                    progressText.textContent = `${percent}%`;
                }
            }
        }

        const blob = new Blob(chunks);
        const blobUrl = URL.createObjectURL(blob);

        // Handle different file types
        if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'].includes(fileExt)) {
            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; overflow: auto; display: flex; flex-direction: column; align-items: center; background: #1a1a1a;">
                    <div style="margin-bottom: 12px; width: 100%; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                        <span style="color: #888; font-size: 13px; font-family: monospace; flex: 1; min-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${path}</span>
                        <button onclick="window.open('${blobUrl}')" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Open in New Tab</button>
                    </div>
                    <img src="${blobUrl}" style="max-width: 100%; max-height: 80vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);" />
                </div>
            `;
        } else if (['pdf'].includes(fileExt)) {
            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
                    <div style="margin-bottom: 12px;">
                        <button onclick="window.open('${blobUrl}')" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Open in New Tab</button>
                    </div>
                    <iframe src="${blobUrl}" style="flex: 1; border: none; border-radius: 4px;"></iframe>
                </div>
            `;
        } else if (['mp4', 'webm', 'ogg', 'mov'].includes(fileExt)) {
            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; display: flex; flex-direction: column; align-items: center; background: #1a1a1a;">
                    <video controls style="max-width: 100%; max-height: 80vh; border-radius: 8px;">
                        <source src="${blobUrl}" type="video/${fileExt}">
                    </video>
                </div>
            `;
        } else if (['html', 'htm'].includes(fileExt)) {
            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
                    <iframe src="${blobUrl}" style="flex: 1; border: none; background: white; border-radius: 4px;"></iframe>
                </div>
            `;
        } else {
            const text = await blob.text();
            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
                    <div style="margin-bottom: 12px;">
                        <span style="color: #888; font-size: 13px;">${path}</span>
                    </div>
                    <pre style="flex: 1; overflow: auto; background: #1a1a1a; color: #f8f8f8; padding: 16px; border-radius: 4px; margin: 0; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5;">${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                </div>
            `;
        }
    } catch (error) {
        tabContent.innerHTML = `<div style="padding: 16px; color: #f88;">Failed to load file: ${error.message}</div>`;
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
