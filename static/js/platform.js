(function () {
    const sidebar = document.getElementById("platformSidebar");
    const backdrop = document.getElementById("platformBackdrop");
    const toggle = document.getElementById("platformSidebarToggle");

    if (!sidebar || !toggle) {
        return;
    }

    function closeSidebar() {
        sidebar.classList.remove("show");
        backdrop.classList.remove("show");
        document.body.style.overflow = "";
    }

    toggle.addEventListener("click", function () {
        const isOpen = sidebar.classList.contains("show");
        if (isOpen) {
            closeSidebar();
        } else {
            sidebar.classList.add("show");
            backdrop.classList.add("show");
            document.body.style.overflow = "hidden";
        }
    });

    backdrop.addEventListener("click", closeSidebar);

    window.addEventListener("resize", function () {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
})();
