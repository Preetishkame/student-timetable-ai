const API_BASE = "";
const userId = localStorage.getItem("user_id");

// Protect Dashboard Route
if (!userId) {
    window.location.href = "/login-page";
}

// Set Welcome Name
const storedName = localStorage.getItem("username");
if (storedName && document.getElementById('welcome-user')) {
    // If username is saved during login, display it. Otherwise defaults to HTML placeholder
    document.getElementById('welcome-user').innerText = storedName;
}

// Logout Handler
const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("user_id");
        localStorage.removeItem("username");
        window.location.href = "/login-page";
    });
}

// --- Tab Switching ---
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    // Remove active class from menu
    document.querySelectorAll('.sidebar-menu a').forEach(link => {
        link.classList.remove('active');
    });

    // Show target tab
    document.getElementById(`tab-${tabId}`).style.display = 'block';
    event.currentTarget.classList.add('active');

    // Trigger specific data loads based on tab
    if(tabId === 'homework') fetchHomework();
    if(tabId === 'attendance') fetchAttendance();
}

// --- Global API Wrapper Function ---
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        "X-User-Id": userId,
        "Content-Type": "application/json"
    };
    
    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "API Error");
        return data;
    } catch (error) {
        showToast(error.message, "error");
        return null;
    }
}

// --- AI Generator Submit ---
document.getElementById('ai-generator-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    showToast("AI is crafting your timetable...", "loading");
    
    const payload = {
        subjects: document.getElementById('ai-subjects').value.split(','),
        hours: document.getElementById('ai-hours').value,
        wake: document.getElementById('ai-wake').value,
        sleep: document.getElementById('ai-sleep').value,
        difficulty: document.getElementById('ai-difficulty').value
    };

    const res = await apiCall('/ai-timetable', 'POST', payload);
    if(res) {
        showToast("Timetable Generated!", "success");
        switchTab('timetable');
        // Logic to render new timetable array into UI table goes here
    }
});

// --- Homework CRUD ---
async function fetchHomework() {
    const data = await apiCall('/homework');
    if(!data) return;

    const container = document.getElementById('homework-container');
    container.innerHTML = ''; // Clear existing

    data.forEach(hw => {
        const card = document.createElement('div');
        card.className = 'widget card-lift';
        card.innerHTML = `
            <div class="widget-header">
                <span>${hw.subject}</span>
                <span class="badge ${hw.status === 'Completed' ? 'badge-success' : 'badge-warning'}">${hw.status}</span>
            </div>
            <h4>${hw.title}</h4>
            <p style="color:var(--text-muted); font-size:0.9rem; margin-top:5px;"><i class="fa-regular fa-clock"></i> Due: ${hw.due_date}</p>
            <div style="margin-top:1rem; display:flex; gap:10px;">
                <button class="btn-outline" style="padding:0.3rem 0.6rem" onclick="deleteHomework(${hw.id})"><i class="fa-solid fa-trash"></i></button>
                <button class="btn-primary" style="padding:0.3rem 0.6rem" onclick="markHwComplete(${hw.id})"><i class="fa-solid fa-check"></i></button>
            </div>
        `;
        container.appendChild(card);
    });
}

document.getElementById('add-hw-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        title: document.getElementById('hw-title').value,
        subject: document.getElementById('hw-subject').value,
        due_date: document.getElementById('hw-due').value,
        status: "Pending"
    };

    const res = await apiCall('/homework', 'POST', payload);
    if(res) {
        showToast("Homework added!", "success");
        document.getElementById('add-hw-form').reset();
        toggleForm('homework-form');
        fetchHomework();
    }
});

async function deleteHomework(id) {
    const res = await apiCall(`/homework/${id}`, 'DELETE');
    if(res) { showToast("Deleted", "success"); fetchHomework(); }
}

// --- Attendance Visualization ---
async function fetchAttendance() {
    // Simulating frontend render logic for the Circular/Card progress
    const data = await apiCall('/attendance') || [
        { subject: "Mathematics", attended: 35, total: 40 },
        { subject: "Science", attended: 22, total: 40 } // Example fallback for UI testing
    ];
    
    const container = document.getElementById('attendance-container');
    container.innerHTML = '';

    data.forEach(att => {
        const percentage = Math.round(
    (att.classes_attended / att.total_classes) * 100
);
        let colorClass = 'badge-success';
        if(percentage < 75) colorClass = 'badge-warning';
        if(percentage < 60) colorClass = 'badge-danger';

        container.innerHTML += `
            <div class="widget card-lift">
                <div class="widget-header">
                    <span>${att.subject}</span>
                    <span class="badge ${colorClass}">${percentage}%</span>
                </div>
                <p>${att.attended} / ${att.total} Classes Attended</p>
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${percentage}%; background-color: var(--${colorClass.split('-')[1]});"></div>
                </div>
            </div>
        `;
    });
}

// Initial Load
document.addEventListener("DOMContentLoaded", () => {
    // Load initial dashboard data here
});