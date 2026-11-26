document.addEventListener("DOMContentLoaded", function () {
  const source = document.getElementById("dashboard-metrics");
  if (!source || typeof Chart === "undefined") {
    return;
  }

  let metrics;
  try {
    metrics = JSON.parse(source.textContent);
  } catch (error) {
    return;
  }

  const roleCanvas = document.getElementById("role-chart");
  if (roleCanvas && metrics.role_distribution.length) {
    new Chart(roleCanvas, {
      type: "doughnut",
      data: {
        labels: metrics.role_distribution.map(function (item) { return item.label; }),
        datasets: [{
          data: metrics.role_distribution.map(function (item) { return item.value; }),
          backgroundColor: ["#d4af37", "#6ea8fe", "#4fd1a5", "#cbd5e1", "#ff6b6b"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#cbd5e1" } } }
      }
    });
  }

  const trendCanvas = document.getElementById("event-trend-chart");
  if (trendCanvas) {
    new Chart(trendCanvas, {
      type: "line",
      data: {
        labels: metrics.event_trend.map(function (item) { return item.date; }),
        datasets: [{
          label: "Access events",
          data: metrics.event_trend.map(function (item) { return item.count; }),
          borderColor: "#d4af37",
          backgroundColor: "rgba(212, 175, 55, 0.16)",
          fill: true,
          tension: 0.35
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#cbd5e1" } } },
        scales: {
          x: { ticks: { color: "#8d9bb4" }, grid: { color: "rgba(255,255,255,0.05)" } },
          y: { ticks: { color: "#8d9bb4" }, grid: { color: "rgba(255,255,255,0.05)" }, beginAtZero: true }
        }
      }
    });
  }

  const zeroTrustCanvas = document.getElementById("zero-trust-trend-chart");
  if (zeroTrustCanvas && metrics.zero_trust_trend.length) {
    new Chart(zeroTrustCanvas, {
      type: "line",
      data: {
        labels: metrics.zero_trust_trend.map(function (item) { return item.date; }),
        datasets: [{
          label: "Zero Trust score",
          data: metrics.zero_trust_trend.map(function (item) { return item.score; }),
          borderColor: "#4fd1a5",
          backgroundColor: "rgba(79, 209, 165, 0.16)",
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#cbd5e1" } } },
        scales: {
          x: { ticks: { color: "#8d9bb4" }, grid: { display: false } },
          y: { ticks: { color: "#8d9bb4" }, grid: { color: "rgba(255,255,255,0.05)" }, min: 0, max: 100 }
        }
      }
    });
  }

  const riskCanvas = document.getElementById("risk-category-chart");
  if (riskCanvas && metrics.risk_by_category.length) {
    new Chart(riskCanvas, {
      type: "bar",
      data: {
        labels: metrics.risk_by_category.map(function (item) { return item.label; }),
        datasets: [{
          label: "Findings",
          data: metrics.risk_by_category.map(function (item) { return item.value; }),
          backgroundColor: "rgba(110, 168, 254, 0.72)",
          borderColor: "#6ea8fe",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#cbd5e1" } } },
        scales: {
          x: { ticks: { color: "#8d9bb4" }, grid: { display: false } },
          y: { ticks: { color: "#8d9bb4" }, grid: { color: "rgba(255,255,255,0.05)" }, beginAtZero: true }
        }
      }
    });
  }
});
