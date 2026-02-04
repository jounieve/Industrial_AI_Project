/**
 * @file app.js
 * @description Moteur de rendu dynamique pour le Strategic Control Tower AeroDyn.
 * Optimisé pour la fluidité des transitions et l'analyse décisionnelle.
 */

let mainChart;

/**
 * Initialisation unique du graphique Chart.js
 * Configure l'esthétique et les options de performance.
 */
function initChart() {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { 
                    label: 'REVENUS (OPÉRATIONNEL)', 
                    data: [], 
                    borderColor: '#10b981', 
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0
                },
                { 
                    label: 'RÉPUTATION STRATÉGIQUE', 
                    data: [], 
                    borderColor: '#f59e0b', 
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'ZONE D\'ALERTE ÉTHIQUE',
                    data: [],
                    borderColor: '#ef4444',
                    borderWidth: 4,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Force le graphique à s'adapter au rectangle
            animation: {
                duration: 400, // Fluidité du mouvement
                easing: 'easeInOutQuart'
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        font: { size: 12, weight: '600', family: 'Plus Jakarta Sans' }
                    }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#3b82f6',
                    bodyColor: '#f8fafc',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b', maxRotation: 0 }
                },
                y: { 
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#64748b' },
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Fonction principale de mise à jour des simulations
 * Appelé à chaque modification des leviers par le CEO.
 */
async function update() {
    // Collecte des paramètres depuis l'interface
    const params = {
        S0: parseInt(document.getElementById('S0').value) || 100,
        beta: parseFloat(document.getElementById('beta').value),
        sigma: 0.2, // Pression politique structurelle
        capacity: parseInt(document.getElementById('capacity').value),
        gamma: parseFloat(document.getElementById('gamma').value),
        t_max: 160
    };

    try {
        const res = await fetch('/simulate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await res.json();

        // Initialisation si premier passage
        if (!mainChart) initChart();

        // Mise à jour fluide des datasets sans destruction d'objet
        mainChart.data.labels = data.t.map(v => `T${Math.floor(v/4)}`);
        mainChart.data.datasets[0].data = data.r; // Courbe des Revenus
        mainChart.data.datasets[1].data = data.rep; // Courbe de Réputation
        mainChart.data.datasets[2].data = data.rep.map(v => v < 50 ? v : null); // Surbrillance Alerte

        mainChart.update('none'); // Utilisation de 'none' pour une réactivité instantanée des curseurs

        // Mise à jour des indicateurs de performance et d'analyse
        updateKPIs(data, params);
        updateCEOAnalysis(data, params);
        
        // Affichage de la logique mathématique pour transparence
        document.getElementById('formula-display').textContent = data.formula;
        
    } catch (error) {
        console.error("Erreur lors de la simulation stratégique:", error);
    }
}

/**
 * Mise à jour des indicateurs clés (KPIs) en temps réel
 */
function updateKPIs(data, params) {
    const finalSuccess = data.r[data.r.length - 1];
    const peakLoad = Math.max(...data.i);
    const finalRep = data.rep[data.rep.length - 1];

    document.getElementById('kpi-success').innerText = `${finalSuccess.toFixed(1)}%`;
    document.getElementById('kpi-peak').innerText = peakLoad.toFixed(1);

    const riskElement = document.getElementById('kpi-risk');
    const riskDot = document.getElementById('risk-dot');
    
    // Logique de seuils de risque
    if (finalRep < 45 || peakLoad > params.capacity * 1.2) {
        riskElement.innerText = "CRITIQUE";
        riskElement.style.color = "#ef4444";
        riskDot.style.backgroundColor = "#ef4444";
    } else if (finalRep < 70) {
        riskElement.innerText = "SOUS TENSION";
        riskElement.style.color = "#f59e0b";
        riskDot.style.backgroundColor = "#f59e0b";
    } else {
        riskElement.innerText = "STABLE";
        riskElement.style.color = "#10b981";
        riskDot.style.backgroundColor = "#10b981";
    }
}

/**
 * Génération de l'analyse textuelle contextuelle
 */
function updateCEOAnalysis(data, p) {
    const expl = document.getElementById('dynamic-expl');
    const lowRep = data.rep.some(v => v < 50);
    const saturation = Math.max(...data.i) > p.capacity;

    let analysis = "";
    if (lowRep) {
        analysis = `<p class="warning"><strong>ALERTE RÉPUTATION :</strong> L'agressivité actuelle (β=${p.beta}) sature les mécanismes d'acceptabilité. Un frein réglementaire automatique réduit votre efficacité commerciale.</p>`;
    } else {
        analysis = `<p class="success"><strong>CONTRÔLE OPÉRATIONNEL :</strong> La trajectoire est conforme aux objectifs. Le capital réputationnel permet de maintenir une croissance stable.</p>`;
    }
    
    if (saturation) {
        analysis += `<p style="color: #f59e0b;"><strong>NOTE :</strong> Goulot d'étranglement détecté. La capacité usine limite la conversion des contrats en revenus.</p>`;
    }

    expl.innerHTML = analysis;
}

/**
 * Gestion de la reconfiguration via IA (Model Factory)
 */
document.getElementById('btn-llm').onclick = async () => {
    const prompt = document.getElementById('llm-prompt').value;
    const btn = document.getElementById('btn-llm');
    
    if(!prompt) return;

    btn.innerText = "RECONFIGURATION...";
    
    try {
        const res = await fetch('/llm_update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: prompt })
        });
        const result = await res.json();
        
        if (result.status === "success") {
            btn.innerText = "SYSTÈME MIS À JOUR";
            btn.style.background = "#10b981";
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE SYSTÈME"; 
                btn.style.background = "#3b82f6";
            }, 2000);
            update();
        }
    } catch (e) {
        btn.innerText = "ERREUR SYSTÈME";
        console.error(e);
    }
};

/**
 * Gestion de la modale "Guide de Pilotage"
 */
const modal = document.getElementById("strategy-modal");
const openBtn = document.getElementById("open-help");
const closeSpan = document.getElementsByClassName("close-modal")[0];

if (openBtn) openBtn.onclick = () => modal.style.display = "block";
if (closeSpan) closeSpan.onclick = () => modal.style.display = "none";
window.onclick = (event) => { if (event == modal) modal.style.display = "none"; }

// Écouteurs d'événements sur les entrées (Inputs)
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', update);
});

// Initialisation au chargement de la page
window.onload = () => {
    initChart();
    update();
};