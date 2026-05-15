document.addEventListener("DOMContentLoaded", function () {

    // Sidebar toggle
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("hidden");
        });
    }

    // Active link highlight
    document.querySelectorAll(".sidebar-link").forEach(link => {
        if (link.href === window.location.href) {
            link.classList.add("bg-indigo-600", "text-white");
        }
    });

    // Auto alerts
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach(alert => {
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 500);
        });
    }, 3000);

    // Confirm actions
    document.querySelectorAll(".confirm-action").forEach(btn => {
        btn.addEventListener("click", function (e) {
            if (!confirm("Are you sure?")) {
                e.preventDefault();
            }
        });
    });

});