// --- Theme Management ---
const themeToggleBtn = document.getElementById('themeToggle');
const currentTheme = localStorage.getItem('theme') || 'light';

// Initialize Theme
if (currentTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    if(themeToggleBtn) themeToggleBtn.innerHTML = '<i class="fa-regular fa-sun"></i>';
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        let theme = document.documentElement.getAttribute('data-theme');
        if (theme === 'dark') {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            themeToggleBtn.innerHTML = '<i class="fa-regular fa-moon"></i>';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            themeToggleBtn.innerHTML = '<i class="fa-regular fa-sun"></i>';
        }
    });
}

// --- Toast Notifications ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    
    // Set icon and color based on type
    let icon = '<i class="fa-solid fa-circle-check" style="color:var(--success)"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-circle-exclamation" style="color:var(--danger)"></i>';
    if (type === 'loading') icon = '<i class="fa-solid fa-spinner fa-spin" style="color:var(--primary)"></i>';

    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- UI Helpers ---
function toggleForm(formId) {
    const form = document.getElementById(formId);
    if(form.style.display === 'none') {
        form.style.display = 'block';
        form.classList.add('section-animate');
    } else {
        form.style.display = 'none';
    }
}