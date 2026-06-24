// dashboard.js — netdefense D3.js frontend
// Author: Chad Hackerman

const socket = io();
const MAX_FEED_ROWS = 200;
let events = [];

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

socket.on("connect", () => {
    document.getElementById("connection-status").className = "status-dot connected";
});

socket.on("disconnect", () => {
    document.getElementById("connection-status").className = "status-dot disconnected";
});

socket.on("new_event", (event) => {
    events.unshift(event);
    if (events.length > MAX_FEED_ROWS) events.pop();
    addTableRow(event);
    updateStats();
    updateSeverityChart();
    updateTimeline();
});

// ---------------------------------------------------------------------------
// Bootstrap — load existing events on page load
// ---------------------------------------------------------------------------

async function loadInitialData() {
    try {
        const [eventsResp, statsResp] = await Promise.all([
            fetch("/api/events?limit=100"),
            fetch("/api/stats")
        ]);
        events = await eventsResp.json();
        const stats = await statsResp.json();

        events.forEach(addTableRow);
        renderStats(stats);
        updateSeverityChart();
        updateTimeline();
    } catch (err) {
        console.error("Failed to load initial data:", err);
    }
}

// ---------------------------------------------------------------------------
// Stats bar
// ---------------------------------------------------------------------------

async function updateStats() {
    try {
        const resp = await fetch("/api/stats");
        const stats = await resp.json();
        renderStats(stats);
    } catch (err) {}
}

function renderStats(stats) {
    document.getElementById("stat-total").textContent    = stats.total_events ?? "—";
    document.getElementById("stat-critical").textContent = stats.critical ?? "—";
    document.getElementById("stat-high").textContent     = stats.high ?? "—";
    document.getElementById("stat-sources").textContent  = Object.keys(stats.sources ?? {}).length;
}

// ---------------------------------------------------------------------------
// Event feed table
// ---------------------------------------------------------------------------

function addTableRow(event) {
    const tbody = document.getElementById("event-tbody");
    const tr = document.createElement("tr");
    const time = new Date(event.timestamp).toLocaleTimeString();
    const severity = event.severity || "UNKNOWN";

    tr.innerHTML = `
        <td>${time}</td>
        <td><span class="severity-badge severity-${severity}">${severity}</span></td>
        <td>${event.source ?? ""}</td>
        <td>${event.category ?? ""}</td>
        <td>${event.src_ip ?? ""}</td>
        <td>${event.dst_ip ?? ""}</td>
        <td title="${event.description ?? ""}">${(event.description ?? "").slice(0, 80)}</td>
    `;

    tbody.insertBefore(tr, tbody.firstChild);
    // Trim table to MAX_FEED_ROWS
    while (tbody.rows.length > MAX_FEED_ROWS) {
        tbody.deleteRow(tbody.rows.length - 1);
    }
}

// ---------------------------------------------------------------------------
// D3 — Severity donut chart
// ---------------------------------------------------------------------------

function updateSeverityChart() {
    const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, UNKNOWN: 0 };
    events.forEach(e => { counts[e.severity] = (counts[e.severity] ?? 0) + 1; });

    const data = Object.entries(counts)
        .filter(([, v]) => v > 0)
        .map(([k, v]) => ({ label: k, value: v }));

    const colors = {
        CRITICAL: "#d32f2f",
        HIGH:     "#f57c00",
        MEDIUM:   "#f9a825",
        LOW:      "#388e3c",
        UNKNOWN:  "#555"
    };

    const container = document.getElementById("severity-chart");
    const width = container.clientWidth || 260;
    const height = 200;
    const radius = Math.min(width, height) / 2 - 10;

    d3.select("#severity-chart").selectAll("*").remove();

    const svg = d3.select("#severity-chart")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${width / 2},${height / 2})`);

    const pie = d3.pie().value(d => d.value).sort(null);
    const arc = d3.arc().innerRadius(radius * 0.55).outerRadius(radius);

    svg.selectAll("path")
        .data(pie(data))
        .join("path")
        .attr("d", arc)
        .attr("fill", d => colors[d.data.label])
        .attr("stroke", "#161b22")
        .attr("stroke-width", 2);

    svg.selectAll("text")
        .data(pie(data))
        .join("text")
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .attr("text-anchor", "middle")
        .attr("font-size", "11px")
        .attr("fill", "#fff")
        .text(d => d.data.value > 0 ? d.data.label.slice(0, 4) : "");
}

// ---------------------------------------------------------------------------
// D3 — Event timeline (bar chart by minute)
// ---------------------------------------------------------------------------

function updateTimeline() {
    const container = document.getElementById("timeline-chart");
    const width = container.clientWidth || 500;
    const height = 180;
    const margin = { top: 10, right: 10, bottom: 30, left: 36 };
    const W = width - margin.left - margin.right;
    const H = height - margin.top - margin.bottom;

    // Bucket events by minute
    const buckets = {};
    events.forEach(e => {
        const key = new Date(e.timestamp).toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM
        buckets[key] = (buckets[key] ?? 0) + 1;
    });

    const data = Object.entries(buckets)
        .map(([k, v]) => ({ time: new Date(k), count: v }))
        .sort((a, b) => a.time - b.time)
        .slice(-20); // last 20 minutes

    d3.select("#timeline-chart").selectAll("*").remove();

    const svg = d3.select("#timeline-chart")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(data.map(d => d.time)).range([0, W]).padding(0.2);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.count) || 1]).nice().range([H, 0]);

    svg.append("g").attr("transform", `translate(0,${H})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%H:%M")).ticks(5))
        .selectAll("text").attr("fill", "#8b949e").attr("font-size", "10px");

    svg.append("g")
        .call(d3.axisLeft(y).ticks(4))
        .selectAll("text").attr("fill", "#8b949e").attr("font-size", "10px");

    svg.selectAll("rect")
        .data(data)
        .join("rect")
        .attr("x", d => x(d.time))
        .attr("y", d => y(d.count))
        .attr("width", x.bandwidth())
        .attr("height", d => H - y(d.count))
        .attr("fill", "#1f6feb")
        .attr("rx", 2);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

loadInitialData();
