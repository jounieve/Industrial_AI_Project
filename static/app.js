let mainChart;

async function update() {
    const params = {
        S0: parseInt(document.getElementById('S0').value),
        beta: parseFloat(document.getElementById('beta').value),
        sigma: parseFloat(document.getElementById('sigma').value),
        capacity: parseInt(document.getElementById('capacity').value),
        gamma: 0.1, t_max: 160
    };

    const res = await fetch('/simulate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(params)
    });
    const data = await res.json();

    renderChart(data);
    updateMetrics(data, params);
    updateExplanation(params, Math.max(...data.i));
}

function updateMetrics(data, params) {
    const peak = Math.max(...data.i);
    document.getElementById('kpi-peak').innerText = peak.toFixed(2);
    document.getElementById('kpi-success').innerText = data.r[data.r.length-1].toFixed(2) + "%";
    
    const risk = document.getElementById('kpi-risk');
    if(peak > params.capacity) {
        risk.innerText = "OVERLOAD"; risk.style.color = "#ef4444";
    } else {
        risk.innerText = "STABLE"; risk.style.color = "#10b981";
    }
}

function updateExplanation(p, peak) {
    const expl = document.getElementById('dynamic-expl');
    expl.innerHTML = `
        <p><strong>Structure des données :</strong> Le système gère 100 unités MoD. Vos contrats passent du stock <em>Susceptible</em> au stock <em>Intégration Active</em> via le paramètre β.</p>
        <p><strong>Impact actuel :</strong> Avec une pression politique de <strong>${(p.sigma*100).toFixed(0)}%</strong>, votre vitesse de signature est bridée. 
        Le pic de charge de <strong>${peak.toFixed(2)}</strong> montre que vous exploitez <strong>${((peak/p.capacity)*100).toFixed(0)}%</strong> de votre capacité industrielle.</p>
    `;
}

function renderChart(data) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    if (mainChart) mainChart.destroy();
    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.t.map(v => v.toFixed(0)),
            datasets: [
                { label: 'Intégration', data: data.i, borderColor: '#3b82f6', tension: 0.4, pointRadius: 0, borderWidth: 3 },
                { label: 'Maturité', data: data.r, borderColor: '#10b981', tension: 0.4, pointRadius: 0, borderWidth: 2 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            animation: { duration: 800, easing: 'easeOutQuart' },
            scales: { y: { grid: { color: '#1e293b' }, border: { display: false } }, x: { grid: { display: false } } }
        }
    });
}

document.querySelectorAll('input').forEach(i => i.oninput = update);
update();