const API_BASE = "http://127.0.0.1:5000"; // Adjust if your Flask port is different

// Login Handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        showToast("Logging in...", "loading");

        try {
            const response = await fetch("/login", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem("user_id", data.user_id);
                localStorage.setItem("username", username); // Save username for welcome msg
                showToast("Login successful!", "success");
                setTimeout(() => window.location.href = "/dashboard", 1000);
            } else {
                showToast(data.error || data.message || "Invalid credentials", "error");
            }
        } catch (error) {
            console.error("Login error:", error);
            showToast("Network failure. Backend might be down.", "error");
        }
    });
}

// Register Handler
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;

        if (password !== confirm) {
            showToast("Passwords do not match!", "error");
            return;
        }

        showToast("Creating account...", "loading");

        try {
            const response = await fetch("/register", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                showToast("Registration successful! Please login.", "success");
                setTimeout(() => window.location.href = "/login-page", 1500);
            } else {
                showToast(data.error || data.message || "Invalid credentials", "error");
            }
        } catch (error) {
            showToast("Network failure. Backend might be down.", "error");
        }
    });
}