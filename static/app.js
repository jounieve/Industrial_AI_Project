let mainChart;

/**
 * Fonction principale de mise à jour des simulations
 */
async function update() {
    const params = {
        S0: 100, // Taille fixe du marché pour la cohérence
        beta: parseFloat(document.getElementById('beta').value),
        sigma: 0.2, // Pression politique de base
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

        renderChart(data);
        updateKPIs(data, params);
        updateCEOAnalysis(data, params);
        
        // Affichage de la logique mathématique injectée par l'IA
        document.getElementById('formula-display').textContent = data.formula;
    } catch (error) {
        console.error("Erreur lors de la simulation:", error);
    }
}

/**
 * Rendu du graphique avec Chart.js
 */
// Ajoutez ceci dans votre app.js pour gérer la modale
const modal = document.getElementById("strategy-modal");
const btn = document.getElementById("open-help");
const span = document.getElementsByClassName("close-modal")[0];

btn.onclick = () => modal.style.display = "block";
span.onclick = () => modal.style.display = "none";
window.onclick = (event) => { if (event == modal) modal.style.display = "none"; }

// Modification de la fonction renderChart pour plus d'interactivité
function renderChart(data) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    if (mainChart) mainChart.destroy();
    
    // Ajout d'une zone de danger visuelle si la réputation baisse trop
    const lowReputationThreshold = data.rep.map(v => v < 50 ? v : null);

    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.t.map(v => `Trimestre ${Math.floor(v/4)}`),
            datasets: [
                { 
                    label: 'Revenus (Systèmes Livrés)', 
                    data: data.r, 
                    borderColor: '#10b981', 
                    fill: true,
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    tension: 0.4 
                },
                { 
                    label: 'Réputation Politique', 
                    data: data.rep, 
                    borderColor: '#f59e0b', 
                    borderDash: [5, 5],
                    tension: 0.4 
                },
                {
                    label: 'Zone d\'Alerte Ethique',
                    data: lowReputationThreshold,
                    borderColor: '#ef4444',
                    borderWidth: 10,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        footer: (items) => {
                            const val = items[0].parsed.y;
                            if (items[0].datasetIndex === 1 && val < 50) 
                                return "⚠️ Attention: Risque de sanctions internationales imminent.";
                            return "";
                        }
                    }
                }
            },
            scales: {
                y: { grid: { color: '#1e293b' } }
            }
        }
    });
}

/**
 * Mise à jour des indicateurs clés (KPIs)
 */
function updateKPIs(data, params) {
    const finalSuccess = data.r[data.r.length - 1];
    const finalRep = data.rep[data.rep.length - 1];
    const peakLoad = Math.max(...data.i);

    document.getElementById('kpi-success').innerText = `${finalSuccess.toFixed(1)}%`;
    document.getElementById('kpi-peak').innerText = peakLoad.toFixed(1);

    const riskElement = document.getElementById('kpi-risk');
    const riskDot = document.getElementById('risk-dot');
    
    if (finalRep < 40 || peakLoad > params.capacity) {
        riskElement.innerText = "CRITIQUE";
        riskElement.style.color = "#ef4444";
        riskDot.style.backgroundColor = "#ef4444";
    } else if (finalRep < 75) {
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
 * Analyse textuelle pour le CEO
 */
function updateCEOAnalysis(data, p) {
    const expl = document.getElementById('dynamic-expl');
    const lowRep = data.rep.some(v => v < 50);

    let analysis = "";
    if (lowRep) {
        analysis = `<p class="warning"><strong>Risque de Réputation :</strong> L'agressivité de l'IA (β=${p.beta}) provoque un effondrement de la confiance. Prévoyez un moratoire ou augmentez les garde-fous éthiques.</p>`;
    } else {
        analysis = `<p class="success"><strong>Flux Sécurisé :</strong> La trajectoire actuelle maximise l'adoption sans franchir le seuil de rejet réglementaire.</p>`;
    }
    
    analysis += `<p>Le pic industriel à <strong>${Math.max(...data.i).toFixed(1)}</strong> unités nécessite une validation de la chaîne logistique.</p>`;
    expl.innerHTML = analysis;
}

/**
 * Gestion de la reconfiguration via IA
 */
document.getElementById('btn-llm').onclick = async () => {
    const prompt = document.getElementById('llm-prompt').value;
    const btn = document.getElementById('btn-llm');
    
    btn.innerText = "RECONFIGURATION EN COURS...";
    
    try {
        const res = await fetch('/llm_update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: prompt })
        });
        const result = await res.json();
        
        if (result.status === "success") {
            btn.innerText = "MODÈLE MIS À JOUR !";
            btn.style.background = "#10b981";
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE MODÈLE"; 
                btn.style.background = "#3b82f6";
            }, 2000);
            update();
        }
    } catch (e) {
        btn.innerText = "ERREUR";
        console.error(e);
    }
};

// Écouteurs d'événements
document.querySelectorAll('input').forEach(i => i.oninput = update);

// Initialisation au chargement
window.onload = update;