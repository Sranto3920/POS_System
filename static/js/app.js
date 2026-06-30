(function () {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    const toggle = document.getElementById("sidebarToggle");

    if (!sidebar || !toggle) {
        return;
    }

    function openSidebar() {
        sidebar.classList.add("show");
        backdrop.classList.add("show");
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        sidebar.classList.remove("show");
        backdrop.classList.remove("show");
        document.body.style.overflow = "";
    }

    toggle.addEventListener("click", function () {
        if (sidebar.classList.contains("show")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    backdrop.addEventListener("click", closeSidebar);

    window.addEventListener("resize", function () {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
})();
