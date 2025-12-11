// ================== GLOBAL THEME-AWARE STYLE ==================
function getCssVar(v, fallback = "#fff") {
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || fallback;
}

Chart.defaults.color = getCssVar("--admin-text");
Chart.defaults.borderColor = "rgba(255,255,255,0.1)";
Chart.defaults.font.family = "Inter, system-ui, sans-serif";

const chartAnim = { duration: 900, easing: "easeOutQuart" };

function createGradient(ctx, color) {
    const g = ctx.createLinearGradient(0, 0, 0, 300);
    g.addColorStop(0, color + "dd");
    g.addColorStop(1, color + "22");
    return g;
}


// ================== COUNTRY NAME → ISO CODE MAP ==================
const countryToISO = {
    "India": "IN",
    "United States": "US",
    "USA": "US",
    "Canada": "CA",
    "United Kingdom": "GB",
    "UK": "GB",
    "Germany": "DE",
    "France": "FR",
    "Australia": "AU",
    "Brazil": "BR",
    "Japan": "JP",
    "China": "CN",
    "Russia": "RU",
    "Spain": "ES",
    "Italy": "IT"
    // Add more if needed
};


// ================== USERS GROWTH ==================
fetch("/admin/api/analytics/users-growth")
    .then(r => r.json())
    .then(data => {
        const c = document.getElementById("usersGrowthChart");
        if (!c) return;
        const ctx = c.getContext("2d");

        new Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Users (7 days)",
                    data: data.data,
                    tension: 0.35,
                    fill: true,
                    borderColor: "#4da3ff",
                    borderWidth: 2,
                    backgroundColor: createGradient(ctx, "#4da3ff")
                }]
            },
            options: { responsive: true, animation: chartAnim, plugins: { legend: { display: false } } }
        });
    });


// ================== TOP SEARCHED CITIES ==================
fetch("/admin/api/analytics/top-cities")
    .then(r => r.json())
    .then(data => {
        const c = document.getElementById("topCitiesChart");
        if (!c) return;

        // If no DB data → show placeholder
        const labels = data.labels.length ? data.labels : ["Mumbai", "Delhi", "Dubai", "London", "New York"];
        const values = data.data.length ? data.data : [5, 3, 2, 1, 1];

        new Chart(c, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Search Count",
                    data: values,
                    backgroundColor: "#7f5af0cc",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                animation: {
                    duration: 900,
                    easing: "easeOutQuart"
                }
            }
        });
    });



// ================== DEVICE CHART ==================
fetch("/admin/api/analytics/devices")
    .then(r => r.json())
    .then(data => {
        const c = document.getElementById("deviceChart");
        if (!c) return;

        new Chart(c, {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{ data: data.values, backgroundColor: ["#4da3ff", "#ff6b6b", "#7f5af0"], borderWidth: 0 }]
            },
            options: { animation: chartAnim, plugins: { legend: { position: "bottom" } } }
        });
    });


// ================== BROWSER CHART ==================
fetch("/admin/api/analytics/browsers")
    .then(r => r.json())
    .then(data => {
        const c = document.getElementById("browserChart");
        if (!c) return;

        new Chart(c, {
            type: "pie",
            data: {
                labels: data.labels,
                datasets: [{ data: data.values, backgroundColor: ["#4da3ff", "#ffcb77", "#ff6b6b", "#2cb67d"], borderWidth: 0 }]
            }
        });
    });


// ================== COUNTRY CHART ==================
fetch("/admin/api/analytics/countries")
    .then(r => r.json())
    .then(data => {
        const c = document.getElementById("countryChart");
        if (!c) return;

        if (!data.labels.length) {
            console.warn("No country data found");
            return;
        }

        new Chart(c, {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: "#7f5af0bb",
                    borderRadius: 6
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                responsive: true,
            }
        });
    });


// ================== RECENT ACTIVITY ==================
fetch("/admin/api/analytics/recent")
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById("recentActivityBody");
        if (!tbody) return;

        tbody.innerHTML = data.rows.map(r => `
            <tr>
                <td>${r.email}</td>
                <td>${r.city}</td>
                <td>${r.country}</td>
                <td>${r.browser}</td>
                <td>${r.device}</td>
                <td>${r.created_at}</td>
            </tr>
        `).join("");
    });


// ================== LIVE STATS REFRESH ==================
setInterval(() => {
    fetch("/admin/api/stats")
        .then(r => r.json())
        .then(stats => {
            statUsers.innerText = stats.users;
            statFlights.innerText = stats.flights;
            statWeather.innerText = stats.weather;
        });
}, 5000);
