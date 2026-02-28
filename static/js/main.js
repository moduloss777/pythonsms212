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
        showLoading('statsContainer');
        const data = await api.get('/dashboard/stats');

        // Update stat cards
        updateStatCard('smsSent', data.total_sent || 0, data.sent_today || 0);
        updateStatCard('successRate', `${(data.success_rate * 100).toFixed(1)}%`, `${(data.success_today * 100).toFixed(1)}% hoy`);
        updateStatCard('balance', `$${data.balance.toFixed(2)}`, `${data.credit_remaining} créditos`);
        updateStatCard('activeTasks', data.active_tasks || 0, `${data.paused_tasks || 0} pausadas`);

        document.getElementById('statsContainer').style.display = 'grid';
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
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
        showLoading('chartContainer');
        const data = await api.get('/dashboard/hourly');

        if (data && data.hours && window.hourlyChart) {
            hourlyChart.data.labels = data.hours;
            hourlyChart.data.datasets[0].data = data.counts;
            hourlyChart.update();
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

async function loadInsights() {
    try {
        const data = await api.get('/dashboard/insights');
        const insightsList = document.getElementById('insightsList');

        if (insightsList && data.insights) {
            insightsList.innerHTML = data.insights
                .map(insight => `<li>${insight}</li>`)
                .join('');
        }
    } catch (error) {
        console.error('Error loading insights:', error);
    }
}

// ========================================
// SMS SENDING
// ========================================

async function sendSMS(event) {
    event.preventDefault();

    const formData = new FormData(document.getElementById('smsForm'));
    const numbers = document.getElementById('smsNumbers').value.split('\n').filter(n => n.trim());
    const content = document.getElementById('smsContent').value;

    if (!numbers.length) {
        showAlert('Por favor ingresa al menos un número', 'warning');
        return;
    }

    if (!content.trim()) {
        showAlert('Por favor ingresa el contenido del SMS', 'warning');
        return;
    }

    const sendBtn = document.querySelector('button[onclick="sendSMS(event)"]');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Enviando...';

    try {
        const response = await api.post('/sms/send', {
            numbers: numbers,
            content: content
        });

        showAlert(`SMS enviados: ${response.sent_count}`, 'success');
        document.getElementById('smsForm').reset();
        document.getElementById('charCounter').textContent = '0/160';
        loadDashboardStats();
    } catch (error) {
        showAlert('Error al enviar SMS', 'danger');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Enviar SMS';
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
        showLoading('reportContent');
        const data = await api.get(`/reports/${reportType}`);

        const content = document.getElementById('reportContent');
        content.innerHTML = formatReport(data, reportType);
    } catch (error) {
        showAlert('Error al generar reporte', 'danger');
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

    if (data.rows) {
        data.rows.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
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
    const formData = new FormData(taskForm);

    const taskData = {
        task_type: parseInt(formData.get('task_type')),
        contacts: formData.get('contacts').split('\n').filter(c => c.trim()),
        content: formData.get('content'),
        sendtime: formData.get('sendtime'),
        interval: formData.get('interval') ? parseInt(formData.get('interval')) : null
    };

    try {
        const response = await api.post('/tasks/create', taskData);
        showAlert('Tarea creada exitosamente', 'success');
        taskForm.reset();
        hideModal('createTaskModal');
        loadTasks();
    } catch (error) {
        showAlert('Error al crear tarea', 'danger');
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
