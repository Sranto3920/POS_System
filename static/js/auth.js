(function () {
    document.querySelectorAll(".password-toggle-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const input = document.getElementById(btn.getAttribute("data-target"));
            if (!input) return;
            const isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            const icon = btn.querySelector("i");
            if (icon) {
                icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
            }
        });
    });
})();
