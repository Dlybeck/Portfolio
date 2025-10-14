/* Tab Content Management */

let currentTab = 'files';
let currentFilePath = localStorage.getItem('working_directory') || '~';
let separateTerminal = null;
let separateWs = null;
let separateFitAddon = null;

// Global fetch error handler for auth and offline detection
function handleFetchError(response) {
    if (!response.ok) {
        // Auth errors - redirect to login
        if (response.status === 401 || response.status === 403) {
            console.log('[Auth] Unauthorized - redirecting to login');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/dev/login';
            return true;
        }
        // Server offline errors - reload to show server_offline page
        if (response.status === 502 || response.status === 503 || response.status === 504) {
            console.log('[Server] Server offline - reloading page');
            window.location.reload();
            return true;
        }
    }
    return false;
}

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

function renderBreadcrumbs(path, isFilesView = false) {
    // Split by / and filter out empty strings
    let segments = path.split('/').filter(s => s);

    // If path starts with ~, ensure it's the first segment (not duplicated)
    if (path.startsWith('~')) {
        // Remove any ~ that was already in segments from split
        segments = segments.filter(s => s !== '~');
        // Add it once at the beginning
        segments.unshift('~');
    }

    if (segments.length === 0) {
        segments.push('~');
    }

    // Build breadcrumbs HTML
    let breadcrumbsHTML = '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px; min-height: 48px;">';

    segments.forEach((segment, index) => {
        // Build the full path for this segment
        let segmentPath;
        if (index === 0 && segment === '~') {
            segmentPath = '~';
        } else if (segments[0] === '~') {
            segmentPath = '~/' + segments.slice(1, index + 1).join('/');
        } else {
            segmentPath = segments.slice(0, index + 1).join('/');
        }

        // Add separator if not first
        if (index > 0) {
            breadcrumbsHTML += '<span style="color: #666; padding: 0 4px; user-select: none;">/</span>';
        }

        // Use different click handler based on context
        const clickHandler = isFilesView ? 'navigateToBreadcrumbFromFiles' : 'navigateToBreadcrumb';

        // Add clickable segment
        breadcrumbsHTML += `
            <span onclick="${clickHandler}('${segmentPath.replace(/'/g, "\\'")}')"
                  style="color: #888; cursor: pointer; padding: 4px 8px; border-radius: 4px; transition: all 0.2s; font-family: monospace; font-size: 13px; min-height: 40px; display: flex; align-items: center;"
                  onmouseover="this.style.background='#444'; this.style.color='#fff';"
                  onmouseout="this.style.background='transparent'; this.style.color='#888';">
                ${segment}
            </span>
        `;
    });

    breadcrumbsHTML += '</div>';

    return breadcrumbsHTML;
}

function navigateToBreadcrumb(path) {
    currentFilePath = path;
    loadFileBrowser(path);
}

async function loadFileBrowser(path) {
    const tabContent = document.getElementById('tabContent');
    const token = localStorage.getItem('access_token');

    tabContent.innerHTML = `
        <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
            <div style="margin-bottom: 12px; overflow-x: auto; -webkit-overflow-scrolling: touch;" id="breadcrumbContainer">
                ${renderBreadcrumbs(path)}
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

        if (handleFetchError(response)) return;

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

        if (handleFetchError(response)) return;

        if (response.ok) {
            // It's a directory
            currentFilePath = path;
            const breadcrumbContainer = document.getElementById('breadcrumbContainer');
            if (breadcrumbContainer) {
                breadcrumbContainer.innerHTML = renderBreadcrumbs(path);
            }
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

// Global state for file editing
let currentEditingFile = null;
let originalFileContent = null;
let isEditMode = false;

// Detect if file is editable by extension
function isEditableFile(path) {
    const editableExtensions = [
        'js', 'py', 'html', 'css', 'md', 'txt', 'json',
        'yml', 'yaml', 'xml', 'sh', 'bash', 'env',
        'gitignore', 'config', 'ini', 'toml'
    ];
    const ext = path.split('.').pop().toLowerCase();
    return editableExtensions.includes(ext) || path.endsWith('Dockerfile');
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';

    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 14px;
        font-weight: 500;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Fade in
    setTimeout(() => toast.style.opacity = '1', 10);

    // Fade out and remove
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

// Enter edit mode
function enterEditMode(path, content) {
    isEditMode = true;
    currentEditingFile = path;
    originalFileContent = content;

    const tabContent = document.getElementById('tabContent');
    const isMobile = window.innerWidth < 768;

    tabContent.innerHTML = `
        <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
            <div style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;">
                <span style="color: #888; font-size: 13px; font-family: monospace; flex: 1; min-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${path}</span>
                <div style="display: flex; gap: 8px;">
                    <button id="saveBtn" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: ${isMobile ? '13px' : '14px'};">Save</button>
                    <button id="cancelBtn" style="background: #6b7280; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: ${isMobile ? '13px' : '14px'};">Cancel</button>
                </div>
            </div>
            <textarea id="fileEditor" style="flex: 1; background: #1a1a1a; color: #f8f8f8; padding: 16px; border: 1px solid #444; border-radius: 4px; font-family: 'Courier New', Menlo, monospace; font-size: ${isMobile ? '13px' : '14px'}; line-height: 1.5; resize: none; width: 100%;">${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>
        </div>
    `;

    // Add event listeners
    document.getElementById('saveBtn').addEventListener('click', saveFile);
    document.getElementById('cancelBtn').addEventListener('click', cancelEdit);

    // Warn before leaving if unsaved changes
    window.addEventListener('beforeunload', beforeUnloadHandler);
}

// Check if there are unsaved changes
function hasUnsavedChanges() {
    if (!isEditMode) return false;
    const editor = document.getElementById('fileEditor');
    if (!editor) return false;
    const currentContent = editor.value;
    return currentContent !== originalFileContent;
}

// Before unload handler
function beforeUnloadHandler(e) {
    if (hasUnsavedChanges()) {
        e.preventDefault();
        e.returnValue = '';
        return '';
    }
}

// Save file
async function saveFile() {
    const editor = document.getElementById('fileEditor');
    const saveBtn = document.getElementById('saveBtn');

    if (!editor || !currentEditingFile) return;

    const content = editor.value;
    const token = localStorage.getItem('access_token');

    // Show loading state
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        const response = await fetch('/dev/api/save-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                path: currentEditingFile,
                content: content
            })
        });

        if (handleFetchError(response)) return;

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save file');
        }

        const result = await response.json();
        showToast(`File saved successfully (${result.bytes_written} bytes)`, 'success');

        // Exit edit mode and return to view mode
        exitEditMode();
        viewFile(currentEditingFile);

    } catch (error) {
        showToast(`Failed to save: ${error.message}`, 'error');
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
    }
}

// Cancel edit
function cancelEdit() {
    if (hasUnsavedChanges()) {
        if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
            return;
        }
    }

    exitEditMode();
    viewFile(currentEditingFile);
}

// Exit edit mode
function exitEditMode() {
    isEditMode = false;
    currentEditingFile = null;
    originalFileContent = null;
    window.removeEventListener('beforeunload', beforeUnloadHandler);
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

        if (handleFetchError(response)) return;

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
            // PDF - open directly via API endpoint (blob URLs don't work)
            const token = localStorage.getItem('access_token');
            const apiUrl = `/dev/api/read-file?path=${encodeURIComponent(path)}&token=${encodeURIComponent(token)}`;

            tabContent.innerHTML = `
                <div style="padding: 32px; text-align: center;">
                    <div style="color: #888; margin-bottom: 24px; font-size: 18px;">📄 PDF File</div>
                    <div style="color: #ccc; margin-bottom: 24px; font-size: 14px; word-break: break-all;">${path}</div>
                    <button onclick="window.open('${apiUrl}')" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600;">
                        Open PDF in New Tab
                    </button>
                    <div style="color: #666; margin-top: 16px; font-size: 12px;">
                        Opens PDF directly from server
                    </div>
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
            const editable = isEditableFile(path);

            tabContent.innerHTML = `
                <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
                    <div style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;">
                        <span style="color: #888; font-size: 13px; font-family: monospace; flex: 1; min-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${path}</span>
                        ${editable ? '<button id="editBtn" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: 600;">Edit</button>' : ''}
                    </div>
                    <pre style="flex: 1; overflow: auto; background: #1a1a1a; color: #f8f8f8; padding: 16px; border-radius: 4px; margin: 0; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5;">${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                </div>
            `;

            // Add edit button listener
            if (editable) {
                document.getElementById('editBtn').addEventListener('click', () => {
                    enterEditMode(path, text);
                });
            }
        }
    } catch (error) {
        tabContent.innerHTML = `<div style="padding: 16px; color: #f88;">Failed to load file: ${error.message}</div>`;
    }
}

async function navigateUp() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/dev/api/parent-directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ path: currentFilePath })
        });

        if (handleFetchError(response)) return;

        const data = await response.json();
        if (data.parent) {
            currentFilePath = data.parent;
            loadFileBrowser(data.parent);
        }
    } catch (error) {
        console.error('Error navigating up:', error);
    }
}

// Load file browser into the dedicated files section (for mobile files view)
let currentFilesPath = localStorage.getItem('working_directory') || '~';

async function loadFileBrowserForFiles(path) {
    const filesTabContent = document.getElementById('filesTabContent');
    const token = localStorage.getItem('access_token');

    if (!filesTabContent) return;

    filesTabContent.innerHTML = `
        <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
            <div style="margin-bottom: 12px; overflow-x: auto; -webkit-overflow-scrolling: touch;" id="filesBreadcrumbContainer">
                ${renderBreadcrumbs(path, true)}
            </div>
            <div id="filesFileList" style="flex: 1; overflow-y: auto; background: #2d2d2d; border-radius: 4px; padding: 8px;">
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

        if (handleFetchError(response)) return;

        const data = await response.json();
        const allItems = [...(data.directories || []), ...(data.files || [])];
        displayFilesForFilesView(allItems, path);
    } catch (error) {
        document.getElementById('filesFileList').innerHTML = '<div style="color: #f88; padding: 20px;">Error loading files</div>';
    }
}

function displayFilesForFilesView(files, path) {
    const fileList = document.getElementById('filesFileList');

    if (!fileList) return;

    if (files.length === 0) {
        fileList.innerHTML = '<div style="color: #888; padding: 20px;">No files or folders</div>';
        return;
    }

    fileList.innerHTML = files.map(file => {
        const icon = file.type === 'directory' ? '📁' : '📄';
        return `
            <div onclick="openFileFromFilesView('${file.path}')" style="padding: 8px 12px; margin: 4px 0; background: #383838; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s;"
                 onmouseover="this.style.background='#444'" onmouseout="this.style.background='#383838'">
                <span style="font-size: 16px;">${icon}</span>
                <span style="color: #f8f8f8; font-size: 14px;">${file.name}</span>
            </div>
        `;
    }).join('');
}

async function openFileFromFilesView(path) {
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

        if (handleFetchError(response)) return;

        if (response.ok) {
            // It's a directory
            currentFilesPath = path;
            const breadcrumbContainer = document.getElementById('filesBreadcrumbContainer');
            if (breadcrumbContainer) {
                breadcrumbContainer.innerHTML = renderBreadcrumbs(path, true);
            }
            const data = await response.json();
            const allItems = [...(data.directories || []), ...(data.files || [])];
            displayFilesForFilesView(allItems, path);
        } else {
            // It's a file - switch to preview view and show the file
            Alpine.store('dashboard').switchView('preview');
            viewFile(path);
        }
    } catch (error) {
        console.error('Error opening file:', error);
    }
}

function navigateToBreadcrumbFromFiles(path) {
    currentFilesPath = path;
    loadFileBrowserForFiles(path);
}
