document.addEventListener("DOMContentLoaded", () => {
    let sidebar = document.querySelector(".sidebar-scroll");
    let top = localStorage.getItem("sidebar-scroll");
    if (sidebar && top !== null) {
        sidebar.scrollTo({
            top: parseInt(top),
            behavior: "instant",
        });
    }
    window.addEventListener("beforeunload", () => {
        localStorage.setItem("sidebar-scroll", sidebar.scrollTop);
    });
});