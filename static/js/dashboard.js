(function () {
    const data = window.dashboardChartData || {};
    const monthlySales = data.monthlySales || [];
    const topProducts = data.topProducts || [];

    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
        },
    };

    const monthlyCanvas = document.getElementById("monthlySalesChart");
    if (monthlyCanvas && typeof Chart !== "undefined") {
        new Chart(monthlyCanvas, {
            type: "line",
            data: {
                labels: monthlySales.map((item) => item.month_label),
                datasets: [{
                    label: "Sales",
                    data: monthlySales.map((item) => Number(item.total)),
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.12)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 4,
                    pointBackgroundColor: "#2563eb",
                }],
            },
            options: {
                ...chartDefaults,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => "৳" + Number(value).toLocaleString(),
                        },
                        grid: { color: "#f1f5f9" },
                    },
                    x: {
                        grid: { display: false },
                    },
                },
            },
        });
    }

    const topCanvas = document.getElementById("topProductsChart");
    if (topCanvas && topProducts.length && typeof Chart !== "undefined") {
        new Chart(topCanvas, {
            type: "bar",
            data: {
                labels: topProducts.map((item) => item.product_name),
                datasets: [{
                    label: "Units Sold",
                    data: topProducts.map((item) => Number(item.units_sold)),
                    backgroundColor: [
                        "#2563eb",
                        "#7c3aed",
                        "#0891b2",
                        "#059669",
                        "#d97706",
                    ],
                    borderRadius: 8,
                }],
            },
            options: {
                ...chartDefaults,
                indexAxis: "y",
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: "#f1f5f9" },
                    },
                    y: {
                        grid: { display: false },
                    },
                },
            },
        });
    }
})();
