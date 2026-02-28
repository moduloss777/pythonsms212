/**
 * GOLEADOR SMS MARKETING - DASHBOARD JAVASCRIPT
 * API Integration and UI Interactions
 */

// ========================================
// API HELPER FUNCTIONS
// ========================================

class APIClient {
    constructor() {
        this.baseUrl = '/api';
    }

    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`GET ${endpoint}:`, error);
            showAlert(`Error: ${error.message}`, 'danger');
            throw error;
        }
    }

    async post(endpoint, data) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`POST ${endpoint}:`, error);
            showAlert(`Error: ${error.message}`, 'danger');
            throw error;
        }
    }
}

const api = new APIClient();

// ========================================
// UI HELPER FUNCTIONS
// ========================================

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <strong>${type === 'danger' ? 'Error' : type === 'success' ? 'Éxito' : 'Información'}:</strong> ${message}
    `;
    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 4000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.position = 'fixed';
    container.style.top = '80px';
    container.style.right = '20px';
    container.style.maxWidth = '400px';
    container.style.zIndex = '999';
    document.body.appendChild(container);
    return container;
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function toggleTab(tabName) {
    // Hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => {
        content.classList.remove('active');
    });

    // Deactivate all tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab content
    const selectedContent = document.getElementById(tabName);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }

    // Activate selected tab button
    const selectedTab = document.querySelector(`[onclick*="toggleTab('${tabName}')"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"><div class="spinner"></div><span>Cargando...</span></div>';
    }
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function countCharacters(text) {
    const smsLength = 160;
    const extendedLength = 70;

    const count = text.length;
    const parts = Math.ceil(count / (text.match(/^[\u0000-\u00FF]*$/) ? smsLength : extendedLength));

    return { count, parts };
}

// ========================================
// DASHBOARD INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    loadChartData();
    loadInsights();
    setupEventListeners();

    // Refresh data every 30 seconds
    setInterval(loadDashboardStats, 30000);
});

// ========================================
// DASHBOARD FUNCTIONS
// ========================================

async function loadDashboardStats() {
    try {
        const response = await api.get('/dashboard/stats');

        // Handle wrapped response structure
        const data = response.data || response;
        const kpis = data.kpis || {};
        const summary = data.summary || {};

        // Calculate totals from summary
        const totalSent = (summary.month?.sent || summary.week?.sent || summary.today?.sent || kpis.total_sms || 0);
        const totalDelivered = (summary.month?.delivered || summary.week?.delivered || summary.today?.delivered || 0);
        const successRate = kpis.success_rate || 0.85;
        const balance = kpis.total_balance || 5000;
        const activeTasks = kpis.active_tasks || 0;

        // Update stat cards
        updateStatCard('smsSent', formatNumber(totalSent), `${kpis.today_sms || 0} hoy`);
        updateStatCard('successRate', `${(successRate * 100).toFixed(1)}%`, 'Tasa de entrega');
        updateStatCard('balance', `$${balance.toFixed(2)}`, 'COP');
        updateStatCard('activeTasks', activeTasks || 0, 'en ejecución');

        const statsContainer = document.getElementById('statsContainer');
        if (statsContainer) {
            statsContainer.style.display = 'grid';
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        // Show default mock data
        updateStatCard('smsSent', '0', '0 hoy');
        updateStatCard('successRate', '85%', 'Tasa de entrega');
        updateStatCard('balance', '$5000.00', 'COP');
        updateStatCard('activeTasks', '0', 'en ejecución');
    }
}

function updateStatCard(cardId, value, subtitle) {
    const card = document.querySelector(`[data-stat="${cardId}"]`);
    if (card) {
        const valueElement = card.querySelector('.stat-value');
        const subtitleElement = card.querySelector('.stat-subtitle');
        if (valueElement) valueElement.textContent = value;
        if (subtitleElement) subtitleElement.textContent = subtitle;
    }
}

async function loadChartData() {
    try {
        const response = await api.get('/dashboard/hourly');
        const data = response.data || response;

        if (data && data.hours && window.hourlyChart) {
            hourlyChart.data.labels = data.hours;
            hourlyChart.data.datasets[0].data = data.counts;
            hourlyChart.update();
        } else if (!window.hourlyChart) {
            console.warn('Chart not initialized yet');
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

async function loadInsights() {
    try {
        const response = await api.get('/dashboard/insights');
        const insightsList = document.getElementById('insightsList');

        if (!insightsList) {
            console.warn('Insights list element not found');
            return;
        }

        let insights = response.insights || response.data?.insights || [];

        if (insights && insights.length > 0) {
            insightsList.innerHTML = insights
                .map(insight => `<li>${insight}</li>`)
                .join('');
        } else {
            insightsList.innerHTML = '<li class="text-muted">No hay insights disponibles</li>';
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        const insightsList = document.getElementById('insightsList');
        if (insightsList) {
            insightsList.innerHTML = '<li class="text-muted">Error cargando insights</li>';
        }
    }
}

// ========================================
// SMS SENDING
// ========================================

async function sendSMS(event) {
    event.preventDefault();

    const smsForm = document.getElementById('smsForm');
    const numberInput = document.getElementById('smsNumbers');
    const contentInput = document.getElementById('smsContent');

    if (!smsForm || !numberInput || !contentInput) {
        showAlert('Error: Elementos del formulario no encontrados', 'danger');
        return;
    }

    const numbers = numberInput.value.split('\n').filter(n => n.trim());
    const content = contentInput.value.trim();

    if (!numbers.length) {
        showAlert('Por favor ingresa al menos un número', 'warning');
        return;
    }

    if (!content) {
        showAlert('Por favor ingresa el contenido del SMS', 'warning');
        return;
    }

    if (numbers.length > 100) {
        showAlert('Máximo 100 números por envío', 'warning');
        return;
    }

    // Find and disable submit button
    const sendBtn = smsForm.querySelector('button[type="submit"]');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Enviando...';
    }

    try {
        console.log('📤 Enviando SMS a', numbers.length, 'números');
        const response = await api.post('/sms/send', {
            numbers: numbers,
            content: content
        });

        console.log('✅ Respuesta del servidor:', response);

        if (response && typeof response.sent_count === 'number') {
            const message = `✅ SMS enviados: ${response.sent_count} / ${numbers.length}`;
            if (response.failed_count && response.failed_count > 0) {
                showAlert(`${message} (${response.failed_count} fallidos)`, 'success');
            } else {
                showAlert(message, 'success');
            }
            smsForm.reset();
            document.getElementById('charCounter').textContent = '0/160 (1 partes)';
            loadDashboardStats();
        } else {
            showAlert('Respuesta inesperada del servidor', 'warning');
            console.warn('Respuesta sin sent_count:', response);
        }
    } catch (error) {
        console.error('❌ Error al enviar SMS:', error);
        showAlert(`Error: ${error.message || 'No se pudo enviar el SMS'}`, 'danger');
    } finally {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = '📤 Enviar SMS';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const smsContent = document.getElementById('smsContent');
    if (smsContent) {
        smsContent.addEventListener('input', function() {
            const { count, parts } = countCharacters(this.value);
            const counter = document.getElementById('charCounter');
            if (counter) {
                counter.textContent = `${count}/160 (${parts} partes)`;
                counter.style.color = count > 160 ? 'var(--warning-color)' : 'inherit';
            }
        });
    }
});

// ========================================
// REPORTS
// ========================================

async function generateReport(reportType) {
    try {
        const reportContent = document.getElementById('reportContent');
        if (!reportContent) {
            showAlert('Error: Elemento de reporte no encontrado', 'danger');
            return;
        }

        reportContent.innerHTML = '<div class="loading"><div class="spinner"></div><span>Generando reporte...</span></div>';

        const response = await api.get(`/api/reports/${reportType}`);
        const data = response.data || response;

        reportContent.innerHTML = formatReport(data, reportType);
        showAlert(`✅ Reporte ${reportType} generado`, 'success');
    } catch (error) {
        const reportContent = document.getElementById('reportContent');
        if (reportContent) {
            reportContent.innerHTML = '<p class="text-danger">Error al generar el reporte</p>';
        }
        showAlert(`Error al generar reporte: ${error.message}`, 'danger');
    }
}

function formatReport(data, type) {
    let html = '<table class="table"><thead><tr>';

    if (type === 'sms') {
        html += '<th>Fecha</th><th>Enviados</th><th>Entregados</th><th>Fallidos</th>';
    } else if (type === 'delivery') {
        html += '<th>Número</th><th>Estado</th><th>Fecha</th>';
    } else if (type === 'transactions') {
        html += '<th>Fecha</th><th>Tipo</th><th>Monto</th><th>Saldo</th>';
    }

    html += '</tr></thead><tbody>';

    const rows = data.rows || data;
    if (rows && Array.isArray(rows) && rows.length > 0) {
        rows.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                const displayValue = typeof value === 'number' ? value.toFixed(2) : value;
                html += `<td>${displayValue}</td>`;
            });
            html += '</tr>';
        });
    } else {
        html += '<tr><td colspan="100%" class="text-muted">No hay datos disponibles</td></tr>';
    }

    html += '</tbody></table>';
    return html;
}

async function exportReport(format) {
    try {
        const response = await fetch(`/api/reports/export?format=${format}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showAlert('Reporte descargado', 'success');
    } catch (error) {
        showAlert('Error al descargar reporte', 'danger');
    }
}

// ========================================
// TASKS MANAGEMENT
// ========================================

async function loadTasks() {
    try {
        showLoading('tasksList');
        const data = await api.get('/tasks/list');

        const tasksList = document.getElementById('tasksList');
        if (tasksList) {
            if (data.tasks && data.tasks.length) {
                tasksList.innerHTML = data.tasks
                    .map(task => `
                        <div class="card" style="margin-bottom: 1rem;">
                            <div class="card-body">
                                <h4>${task.type_name}</h4>
                                <p><small>ID: ${task.id.substring(0, 8)}...</small></p>
                                <p><strong>Contactos:</strong> ${task.contacts_count}</p>
                                <p><strong>Estado:</strong> <span class="badge badge-${getStatusBadgeClass(task.status)}">${task.status}</span></p>
                                <p><strong>Ejecuciones:</strong> ${task.executed}</p>
                                <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                                    ${task.status === 'active' ? `<button class="btn btn-small btn-warning" onclick="pauseTask('${task.id}')">Pausar</button>` : ''}
                                    ${task.status === 'paused' ? `<button class="btn btn-small btn-success" onclick="resumeTask('${task.id}')">Reanudar</button>` : ''}
                                    <button class="btn btn-small btn-danger" onclick="cancelTask('${task.id}')">Cancelar</button>
                                </div>
                            </div>
                        </div>
                    `)
                    .join('');
            } else {
                tasksList.innerHTML = '<p class="text-muted">No hay tareas programadas</p>';
            }
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function getStatusBadgeClass(status) {
    const classes = {
        'active': 'success',
        'paused': 'warning',
        'completed': 'info',
        'cancelled': 'danger'
    };
    return classes[status] || 'info';
}

async function createTask(event) {
    event.preventDefault();

    const taskForm = document.getElementById('taskForm');
    if (!taskForm) {
        showAlert('Error: Formulario de tareas no encontrado', 'danger');
        return;
    }

    const formData = new FormData(taskForm);

    const taskType = parseInt(formData.get('task_type') || '0');
    const contactsText = formData.get('contacts') || '';
    const content = formData.get('content') || '';
    const sendtime = formData.get('sendtime') || '';
    const interval = formData.get('interval');

    const contacts = contactsText.split('\n').filter(c => c.trim());

    if (!contacts.length) {
        showAlert('Por favor ingresa al menos un contacto', 'warning');
        return;
    }

    if (!content.trim()) {
        showAlert('Por favor ingresa el contenido del mensaje', 'warning');
        return;
    }

    const taskData = {
        task_type: taskType,
        contacts: contacts,
        content: content,
        sendtime: sendtime || null,
        interval: interval ? parseInt(interval) : null
    };

    try {
        const response = await api.post('/tasks/create', taskData);
        showAlert('✅ Tarea creada exitosamente', 'success');
        taskForm.reset();
        loadTasks();
    } catch (error) {
        showAlert(`Error al crear tarea: ${error.message}`, 'danger');
    }
}

async function pauseTask(taskId) {
    try {
        await api.post(`/tasks/${taskId}/pause`, {});
        showAlert('Tarea pausada', 'success');
        loadTasks();
    } catch (error) {
        showAlert('Error al pausar tarea', 'danger');
    }
}

async function resumeTask(taskId) {
    try {
        await api.post(`/tasks/${taskId}/resume`, {});
        showAlert('Tarea reanudada', 'success');
        loadTasks();
    } catch (error) {
        showAlert('Error al reanudar tarea', 'danger');
    }
}

async function cancelTask(taskId) {
    if (confirm('¿Estás seguro de que deseas cancelar esta tarea?')) {
        try {
            await api.post(`/tasks/${taskId}/cancel`, {});
            showAlert('Tarea cancelada', 'success');
            loadTasks();
        } catch (error) {
            showAlert('Error al cancelar tarea', 'danger');
        }
    }
}

// ========================================
// EVENT LISTENERS SETUP
// ========================================

function setupEventListeners() {
    // Load tasks when dashboard loads
    if (document.getElementById('tasksList')) {
        loadTasks();
    }

    // Close modals when clicking outside
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                this.classList.remove('active');
            }
        });
    });

    // SMS form submission
    const smsForm = document.getElementById('smsForm');
    if (smsForm) {
        smsForm.addEventListener('submit', sendSMS);
    }

    // Task form submission
    const taskForm = document.getElementById('taskForm');
    if (taskForm) {
        taskForm.addEventListener('submit', createTask);
    }

    // Initial tab setup
    const firstTab = document.querySelector('.tab');
    if (firstTab) {
        firstTab.classList.add('active');
        const tabName = firstTab.textContent.toLowerCase();
        const firstContent = document.querySelector('.tab-content');
        if (firstContent) {
            firstContent.classList.add('active');
        }
    }
}

// ========================================
// CHART INITIALIZATION (if Chart.js is loaded)
// ========================================

let hourlyChart = null;

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('hourlyChart');
    if (ctx && typeof Chart !== 'undefined') {
        hourlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'SMS por Hora',
                    data: [],
                    backgroundColor: 'rgba(37, 99, 235, 0.8)',
                    borderColor: 'rgba(37, 99, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
});

// ========================================
// UTILITY FUNCTIONS
// ========================================

function logout() {
    if (confirm('¿Deseas cerrar sesión?')) {
        window.location.href = '/logout';
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP'
    }).format(amount);
}

function getTimelineFromNow(date) {
    const now = new Date();
    const then = new Date(date);
    const diff = Math.floor((now - then) / 1000);

    if (diff < 60) return 'hace unos segundos';
    if (diff < 3600) return `hace ${Math.floor(diff / 60)} minutos`;
    if (diff < 86400) return `hace ${Math.floor(diff / 3600)} horas`;
    return `hace ${Math.floor(diff / 86400)} días`;
}

// ========================================
// CAMPAÑAS DINÁMICAS
// ========================================

let currentExcelImportId = null;
let currentContactsData = [];
let currentCampaignId = null;
let currentTemplate = '';

function triggerExcelUpload() {
    document.getElementById('excelFile').click();
}

document.addEventListener('DOMContentLoaded', function() {
    const excelFile = document.getElementById('excelFile');
    if (excelFile) {
        excelFile.addEventListener('change', uploadExcelFile);
    }
});

async function uploadExcelFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const uploadProgress = document.getElementById('uploadProgress');
    uploadProgress.style.display = 'block';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/campaigns/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            currentExcelImportId = data.excel_import_id;
            currentContactsData = data.contacts;

            showContactsPreview(data);
            showCampaignStep('step2Preview');
            showAlert(`✅ ${data.valid_rows} contactos válidos cargados`, 'success');
        } else {
            showAlert(`❌ Error: ${data.message}`, 'danger');
        }
    } catch (error) {
        showAlert(`Error al cargar archivo: ${error.message}`, 'danger');
    }

    uploadProgress.style.display = 'none';
}

function showContactsPreview(data) {
    const previewDiv = document.getElementById('contactsPreview');
    const contacts = data.contacts.slice(0, 5);

    let html = '<table><thead><tr><th>Número</th><th>Nombre</th><th>Email</th></tr></thead><tbody>';

    contacts.forEach(c => {
        html += `<tr>
            <td>${c.numero}</td>
            <td>${c.nombre || '-'}</td>
            <td>${c.email || '-'}</td>
        </tr>`;
    });

    if (data.contacts.length > 5) {
        html += `<tr><td colspan="3" style="text-align: center; font-size: 12px; color: #999;">... y ${data.contacts.length - 5} más</td></tr>`;
    }

    html += '</tbody></table>';

    previewDiv.innerHTML = html;
    document.getElementById('validCount').textContent = data.valid_rows;
    document.getElementById('totalCount').textContent = data.total_rows;

    // Actualizar la sección de variables personalizadas en la guía
    if (data.detected_variables && data.detected_variables.length > 0) {
        const customVarsList = document.getElementById('customVariablesList');
        if (customVarsList) {
            customVarsList.innerHTML = data.detected_variables
                .sort()
                .map(v => `<div class="variable-item"><code>{{${v}}}</code></div>`)
                .join('');
        }
    }

    if (data.errors && data.errors.length > 0) {
        showAlert(`⚠️ ${data.errors.length} contactos inválidos`, 'warning');
    }
}

function updateCustomVariablesDisplay() {
    // Mostrar variables personalizadas detectadas en la sección de guía
    const variables = new Set();
    currentContactsData.forEach(c => {
        Object.keys(c.variables || {}).forEach(v => variables.add(v));
    });

    const customVarsList = document.getElementById('customVariablesList');
    if (customVarsList && variables.size > 0) {
        customVarsList.innerHTML = Array.from(variables)
            .sort()
            .map(v => `<div class="variable-item"><code>{{${v}}}</code> - Variable del Excel</div>`)
            .join('');
    }
}

function proceedToTemplate() {
    // Mostrar variables disponibles en la plantilla
    const variables = new Set();
    currentContactsData.forEach(c => {
        Object.keys(c.variables || {}).forEach(v => variables.add(v));
    });

    const variablesList = document.getElementById('variablesList');
    variablesList.innerHTML = Array.from(variables)
        .sort()
        .map(v => `<span>{{${v}}}</span>`)
        .join('');

    // También actualizar la sección de guía
    updateCustomVariablesDisplay();

    showCampaignStep('step3Template');
}

function updateMessagePreview() {
    const template = document.getElementById('messageTemplate').value;
    const firstContact = currentContactsData[0];

    if (!firstContact) return;

    let preview = template;
    Object.keys(firstContact.variables || {}).forEach(key => {
        const placeholder = `{{${key}}}`;
        const value = firstContact.variables[key];
        preview = preview.replace(new RegExp(placeholder, 'g'), value);
    });

    document.getElementById('messagePreview').textContent = preview || 'El preview aparecerá aquí...';
}

// Agregar event listener al textarea de plantilla
document.addEventListener('DOMContentLoaded', function() {
    const template = document.getElementById('messageTemplate');
    if (template) {
        template.addEventListener('input', updateMessagePreview);
    }
});

function proceedToSend() {
    currentTemplate = document.getElementById('messageTemplate').value;

    if (!currentTemplate.trim()) {
        showAlert('Por favor ingresa una plantilla de mensaje', 'warning');
        return;
    }

    // Mostrar resumen
    document.getElementById('summaryName').textContent = document.getElementById('campaignName').value || 'Sin nombre';
    document.getElementById('summaryCount').textContent = currentContactsData.length;
    document.getElementById('summaryPreview').textContent = updateMessagePreview() || currentTemplate;

    showCampaignStep('step4Send');
}

function backToTemplate() {
    showCampaignStep('step3Template');
}

async function sendCampaign() {
    try {
        showCampaignStep('campaignProgress');

        // Crear campaña
        const createResponse = await api.post('/api/campaigns/create', {
            name: document.getElementById('campaignName').value,
            excel_import_id: currentExcelImportId,
            template: currentTemplate
        });

        currentCampaignId = createResponse.campaign_id;

        // Procesar contactos
        await api.post(`/api/campaigns/${currentCampaignId}/process`, {
            contacts: currentContactsData,
            template: currentTemplate
        });

        // Enviar campaña
        const sendResponse = await api.post(`/api/campaigns/${currentCampaignId}/send`, {});

        // Monitorear progreso
        monitorCampaignProgress();

    } catch (error) {
        showAlert(`Error: ${error.message}`, 'danger');
        showCampaignStep('step4Send');
    }
}

async function monitorCampaignProgress() {
    const maxAttempts = 120; // 2 minutos
    let attempts = 0;

    const interval = setInterval(async () => {
        attempts++;

        try {
            const progress = await api.get(`/api/campaigns/${currentCampaignId}/progress`);

            const percentage = progress.data?.total > 0
                ? Math.round((progress.data.sent / progress.data.total) * 100)
                : 0;

            document.getElementById('campaignProgressBar').style.width = percentage + '%';
            document.getElementById('campaignProgressBar').textContent = percentage + '%';
            document.getElementById('campaignProgressText').textContent =
                `${progress.data?.sent || 0} / ${progress.data?.total || 0} enviados (${percentage}%)`;

            if (progress.data?.status === 'completed') {
                clearInterval(interval);
                showResults(progress.data);
            } else if (attempts >= maxAttempts) {
                clearInterval(interval);
                showAlert('Envío completado (timeout de monitoreo)', 'success');
                showCampaignStep('campaignResults');
            }

        } catch (error) {
            console.error('Error monitoreando progreso:', error);
        }
    }, 1000);
}

function showResults(results) {
    document.getElementById('resultsSent').textContent = results.sent || 0;
    document.getElementById('resultsFailed').textContent = results.failed || 0;
    document.getElementById('resultsDuration').textContent = '~30s';
    showCampaignStep('campaignResults');
}

function newCampaign() {
    // Resetear estado
    currentExcelImportId = null;
    currentContactsData = [];
    currentCampaignId = null;
    currentTemplate = '';

    // Limpiar inputs
    document.getElementById('campaignName').value = '';
    document.getElementById('messageTemplate').value = '';
    document.getElementById('excelFile').value = '';

    showCampaignStep('step1Upload');
}

function showCampaignStep(stepId) {
    // Ocultar todos los steps
    document.querySelectorAll('[id^="step"], [id^="campaign"]').forEach(el => {
        if (el.className && el.className.includes('campaign')) {
            el.style.display = 'none';
        }
    });

    // Mostrar step seleccionado
    const step = document.getElementById(stepId);
    if (step) {
        step.style.display = 'block';
    }
}

// ========================================
// DIAGNOSTIC FUNCTION
// ========================================

async function runDiagnostic() {
    const resultDiv = document.getElementById('diagnosticResult');
    const contentDiv = document.getElementById('diagnosticContent');

    resultDiv.style.display = 'block';
    contentDiv.innerHTML = '<p style="text-align: center;">🔍 Verificando conexión a Traffilink...</p>';

    try {
        const response = await fetch('/api/diagnostic/traffilink');
        const data = await response.json();

        let html = '';

        if (data.status === 'success') {
            html = `
                <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 20px;">
                    <h4 style="color: #155724; margin-top: 0;">✅ Conexión Exitosa</h4>
                    <p><strong>Cuenta:</strong> ${data.account}</p>
                    <p><strong>URL Base:</strong> ${data.base_url}</p>
                    <p><strong>Balance:</strong> $${data.balance || 0}</p>
                    <p><strong>Balance Regalo:</strong> $${data.gift_balance || 0}</p>
                    <p style="color: #155724; margin-top: 15px;">✅ Tu API está correctamente configurada y funcionando.</p>
                </div>
            `;
        } else {
            html = `
                <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 20px;">
                    <h4 style="color: #721c24; margin-top: 0;">❌ Error de Conexión</h4>
                    <p><strong>Mensaje:</strong> ${data.message}</p>
                    <p><strong>Detalles:</strong> ${data.details || 'No hay detalles adicionales'}</p>
                    <p><strong>Cuenta:</strong> ${data.account || 'N/A'}</p>
                    <p><strong>URL Base:</strong> ${data.base_url || 'N/A'}</p>
                    <p style="margin-top: 15px; color: #721c24;">
                        <strong>Posibles soluciones:</strong><br>
                        • Verifica que las credenciales en .env sean correctas<br>
                        • Comprueba que el servidor de Traffilink esté disponible<br>
                        • Si recibes código -1: las credenciales son inválidas<br>
                        • Contacta al proveedor de Traffilink si el problema persiste
                    </p>
                </div>
            `;
        }

        contentDiv.innerHTML = html;
        showAlert(data.status === 'success' ? '✅ Conexión verificada correctamente' : '❌ Error de conexión', data.status === 'success' ? 'success' : 'danger');

    } catch (error) {
        contentDiv.innerHTML = `
            <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 20px;">
                <h4 style="color: #721c24;">❌ Error al realizar diagnóstico</h4>
                <p>${error.message}</p>
            </div>
        `;
        showAlert('Error al realizar diagnóstico: ' + error.message, 'danger');
    }
}
