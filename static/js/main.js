// ==========================
// GLOBAL APP JS (KegTrack)
// ==========================

document.addEventListener("DOMContentLoaded", function () {

    // ==========================
    // 1. NAVBAR SCROLL EFFECT
    // ==========================
    const nav = document.getElementById("public-nav");

    if (nav) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 50) {
                nav.classList.add("nav-glass", "shadow-sm", "py-3");
                nav.classList.remove("py-4");
            } else {
                nav.classList.remove("nav-glass", "shadow-sm", "py-3");
                nav.classList.add("py-4");
            }
        });
    }


    // ==========================
    // 2. AUTO CLOSE ALERTS
    // ==========================
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach(alert => {
            alert.style.transition = "opacity 0.5s";
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 500);
        });
    }, 4000);


    // ==========================
    // 3. PASSWORD TOGGLE
    // ==========================
    document.querySelectorAll(".toggle-password").forEach(btn => {
        btn.addEventListener("click", function () {
            const input = document.querySelector(this.dataset.target);

            if (input.type === "password") {
                input.type = "text";
                this.innerHTML = "🙈";
            } else {
                input.type = "password";
                this.innerHTML = "👁️";
            }
        });
    });


    // ==========================
    // 4. LOADING BUTTON STATE
    // ==========================
    document.querySelectorAll("form").forEach(form => {
        form.addEventListener("submit", function () {
            const btn = form.querySelector("button[type='submit']");
            if (btn) {
                btn.disabled = true;
                btn.innerText = "Processing...";
            }
        });
    });


    // ==========================
    // 5. SMOOTH SCROLL LINKS
    // ==========================
    document.querySelectorAll("a[href^='#']").forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth" });
            }
        });
    });

});