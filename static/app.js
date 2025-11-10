// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let selectedFiles = [];
let dataOverview = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
    setupEventListeners();
    refreshOverview();
});

// Check API Health
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const status = document.getElementById('api-status');
        const statusText = document.getElementById('status-text');

        if (response.ok) {
            status.className = 'api-status connected';
            statusText.textContent = 'API Connected';
        } else {
            status.className = 'api-status disconnected';
            statusText.textContent = 'API Disconnected';
        }
    } catch (error) {
        const status = document.getElementById('api-status');
        const statusText = document.getElementById('status-text');
        status.className = 'api-status disconnected';
        statusText.textContent = 'API Offline';
        console.error('API health check failed:', error);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });

    // File input
    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    const uploadBox = document.getElementById('upload-box');
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.background = '#f0f3ff';
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.style.background = '#f8f9ff';
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.background = '#f8f9ff';
        handleFileSelect({ target: { files: e.dataTransfer.files } });
    });

    // Upload button
    document.getElementById('upload-btn').addEventListener('click', uploadFiles);

    // Enter key in question input
    document.getElementById('question-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            askQuestion();
        }
    });
}

// Switch Tab
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Check if data is available for query and insights tabs
    if (tabName === 'query' || tabName === 'insights') {
        checkDataAvailability(tabName);
    }

    // Refresh overview when switching to overview tab
    if (tabName === 'overview') {
        refreshOverview();
    }
}

// Check Data Availability
async function checkDataAvailability(tabName) {
    const overview = await getOverview();
    const hasData = overview && overview.total_files > 0;

    const warningId = `${tabName}-warning`;
    const interfaceId = `${tabName}-interface`;

    if (hasData) {
        document.getElementById(warningId).style.display = 'none';
        document.getElementById(interfaceId).style.display = 'block';
    } else {
        document.getElementById(warningId).style.display = 'block';
        document.getElementById(interfaceId).style.display = 'none';
    }
}

// Handle File Selection
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    selectedFiles = files;

    const selectedFilesDiv = document.getElementById('selected-files');
    const uploadBtn = document.getElementById('upload-btn');

    if (files.length > 0) {
        selectedFilesDiv.innerHTML = `
            <h3>Selected Files (${files.length})</h3>
            ${files.map((file, index) => `
                <div class="file-item">
                    <span><i class="fas fa-file-csv"></i> ${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
                </div>
            `).join('')}
        `;
        uploadBtn.style.display = 'block';
    } else {
        selectedFilesDiv.innerHTML = '';
        uploadBtn.style.display = 'none';
    }
}

// Upload Files
async function uploadFiles() {
    if (selectedFiles.length === 0) return;

    showLoading('Uploading and processing files...');

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch(`${API_BASE_URL}/upload-multiple`, {
            method: 'POST',
            body: formData
        });

        const results = await response.json();
        displayUploadResults(results);

        // Clear selection
        selectedFiles = [];
        document.getElementById('selected-files').innerHTML = '';
        document.getElementById('upload-btn').style.display = 'none';
        document.getElementById('file-input').value = '';

        // Refresh overview
        await refreshOverview();

    } catch (error) {
        console.error('Upload error:', error);
        showError('Failed to upload files. Please try again.');
    } finally {
        hideLoading();
    }
}

// Display Upload Results
function displayUploadResults(results) {
    const resultsDiv = document.getElementById('upload-results');

    const successCount = results.filter(r => r.success).length;

    let html = `<h3>Upload Results</h3>`;

    if (successCount === results.length) {
        html += `<div class="result-item">
            <i class="fas fa-check-circle"></i>
            Successfully uploaded and processed ${successCount} file(s)!
        </div>`;
    } else {
        html += `<div class="result-item error">
            <i class="fas fa-exclamation-circle"></i>
            Processed ${successCount}/${results.length} files successfully
        </div>`;
    }

    html += '<div style="margin-top: 1rem;">';
    results.forEach(result => {
        if (result.success) {
            html += `
                <div class="result-item">
                    <strong><i class="fas fa-check"></i> ${result.file_name}</strong>
                    <p>Chunks created: ${result.chunks_created}</p>
                    ${result.insights ? `
                        <p>Rows: ${result.insights.shape.rows}, Columns: ${result.insights.shape.columns}</p>
                    ` : ''}
                </div>
            `;
        } else {
            html += `
                <div class="result-item error">
                    <strong><i class="fas fa-times"></i> ${result.file_name}</strong>
                    <p>${result.error}</p>
                </div>
            `;
        }
    });
    html += '</div>';

    resultsDiv.innerHTML = html;
}

// Set Question
function setQuestion(question) {
    document.getElementById('question-input').value = question;
}

// Ask Question
async function askQuestion() {
    const question = document.getElementById('question-input').value.trim();
    if (!question) return;

    const showSources = document.getElementById('show-sources').checked;

    showLoading('Analyzing data and generating answer...');

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, return_sources: showSources })
        });

        const result = await response.json();

        if (result.success) {
            displayChatMessage(question, result.answer, result.sources);
            document.getElementById('question-input').value = '';
        } else {
            showError(result.error || 'Failed to get answer');
        }
    } catch (error) {
        console.error('Query error:', error);
        showError('Failed to process query. Please try again.');
    } finally {
        hideLoading();
    }
}

// Display Chat Message
function displayChatMessage(question, answer, sources) {
    const chatHistory = document.getElementById('chat-history');

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <strong>📚 Sources (${sources.length}):</strong>
                ${sources.slice(0, 3).map((source, i) => {
                    const metadata = source.metadata || {};
                    return `
                        <div class="source-item">
                            <strong>Source ${i + 1}:</strong> ${metadata.file_name || 'Unknown'}
                            ${metadata.chunk_type ? `<br>Type: ${metadata.chunk_type}` : ''}
                            ${metadata.row_start !== undefined ? `<br>Rows: ${metadata.row_start}-${metadata.row_end}` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    const messageHtml = `
        <div class="chat-message user">
            <strong>🙋 You asked:</strong>
            <p>${question}</p>
        </div>
        <div class="chat-message ai">
            <strong>🤖 AI Answer:</strong>
            <p>${answer.replace(/\n/g, '<br>')}</p>
            ${sourcesHtml}
        </div>
    `;

    chatHistory.insertAdjacentHTML('afterbegin', messageHtml);
}

// Generate Insights
async function generateInsights(focus = null) {
    const focusInput = document.getElementById('focus-input');
    const focusValue = focus || focusInput.value.trim() || null;

    showLoading('Generating insights...');

    try {
        let url = `${API_BASE_URL}/insights`;
        if (focusValue) {
            url += `?focus=${encodeURIComponent(focusValue)}`;
        }

        const response = await fetch(url, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            displayInsights(result);
        } else {
            showError(result.error || 'Failed to generate insights');
        }
    } catch (error) {
        console.error('Insights error:', error);
        showError('Failed to generate insights. Please try again.');
    } finally {
        hideLoading();
    }
}

// Display Insights
function displayInsights(result) {
    const resultsDiv = document.getElementById('insights-results');

    const html = `
        <div class="insight-box">
            <h3>💡 Insights: ${result.focus || 'General'}</h3>
            <p>${result.insights.replace(/\n/g, '<br>')}</p>
            ${result.based_on_files ? `
                <p style="margin-top: 1rem; font-size: 0.9rem; color: #6b7280;">
                    <strong>Based on files:</strong> ${result.based_on_files.join(', ')}
                </p>
            ` : ''}
        </div>
    `;

    resultsDiv.innerHTML = html;
}

// Get Overview
async function getOverview() {
    try {
        const response = await fetch(`${API_BASE_URL}/overview`);
        return await response.json();
    } catch (error) {
        console.error('Overview error:', error);
        return null;
    }
}

// Refresh Overview
async function refreshOverview() {
    const overview = await getOverview();

    if (!overview) return;

    dataOverview = overview;

    // Update sidebar stats
    document.getElementById('stat-files').textContent = overview.total_files || 0;
    document.getElementById('stat-chunks').textContent = overview.total_chunks || 0;

    // Update overview tab
    const statsDiv = document.getElementById('overview-stats');
    const filesDiv = document.getElementById('overview-files');

    if (overview.total_files === 0) {
        statsDiv.innerHTML = '<p>No data uploaded yet. Upload some files to see the overview.</p>';
        filesDiv.innerHTML = '';
        return;
    }

    // Stats cards
    const totalRows = overview.files.reduce((sum, f) => sum + (f.total_rows || 0), 0);
    statsDiv.innerHTML = `
        <div class="stat-card">
            <h3>${overview.total_files}</h3>
            <p>Files Uploaded</p>
        </div>
        <div class="stat-card">
            <h3>${overview.total_chunks}</h3>
            <p>Data Chunks</p>
        </div>
        <div class="stat-card">
            <h3>${totalRows.toLocaleString()}</h3>
            <p>Total Rows</p>
        </div>
    `;

    // Files list
    filesDiv.innerHTML = `
        <h3>📁 Uploaded Files</h3>
        ${overview.files.map(file => `
            <div class="file-detail">
                <h4><i class="fas fa-file"></i> ${file.file_name}</h4>
                <div class="file-meta">
                    <div class="meta-item">
                        <div class="meta-value">${(file.total_rows || 0).toLocaleString()}</div>
                        <div class="meta-label">Rows</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-value">${(file.columns || []).length}</div>
                        <div class="meta-label">Columns</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-value">${file.chunks || 0}</div>
                        <div class="meta-label">Chunks</div>
                    </div>
                </div>
                ${file.columns && file.columns.length > 0 ? `
                    <p style="margin-top: 1rem; font-size: 0.9rem; color: #6b7280;">
                        <strong>Columns:</strong> ${file.columns.join(', ')}
                    </p>
                ` : ''}
            </div>
        `).join('')}
    `;
}

// Clear All Data
async function clearAllData() {
    if (!confirm('Are you sure you want to clear all uploaded data? This cannot be undone.')) {
        return;
    }

    showLoading('Clearing all data...');

    try {
        const response = await fetch(`${API_BASE_URL}/clear`, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            // Clear local state
            selectedFiles = [];
            dataOverview = null;

            // Clear UI
            document.getElementById('selected-files').innerHTML = '';
            document.getElementById('upload-results').innerHTML = '';
            document.getElementById('chat-history').innerHTML = '';
            document.getElementById('insights-results').innerHTML = '';
            document.getElementById('upload-btn').style.display = 'none';

            // Refresh overview
            await refreshOverview();

            alert('All data cleared successfully!');
        } else {
            showError(result.error || 'Failed to clear data');
        }
    } catch (error) {
        console.error('Clear error:', error);
        showError('Failed to clear data. Please try again.');
    } finally {
        hideLoading();
    }
}

// Loading Overlay
function showLoading(text = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    loadingText.textContent = text;
    overlay.style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Show Error
function showError(message) {
    alert(`Error: ${message}`);
}
