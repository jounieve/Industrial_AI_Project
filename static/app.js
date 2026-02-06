/**
 * @file app.js
 * @description Moteur de rendu dynamique pour le Strategic Control Tower AeroDyn.
 */

let mainChart;
let activeVariables = ['S', 'I', 'R', 'Rep'];
let colorAssignments = {}; // Persistent color mapping

/**
 * Initialisation unique du graphique Chart.js
 */
function initChart() {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [] 
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 400,
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
 * Get or assign persistent color for a variable
 */
function getColorForVariable(key) {
    const colorPalette = [
        '#10b981', // Green (R)
        '#f59e0b', // Orange (Rep)
        '#94a3b8', // Gray (S)
        '#ef4444', // Red (I)
        '#3b82f6', // Blue
        '#8b5cf6', // Purple
        '#ec4899', // Pink
        '#06b6d4', // Cyan
        '#f97316', // Dark Orange
        '#14b8a6', // Teal
        '#a855f7', // Violet
        '#f43f5e', // Rose
        '#0ea5e9', // Sky Blue
        '#84cc16', // Lime
        '#eab308', // Yellow
        '#6366f1', // Indigo
        '#22c55e', // Emerald
        '#fb923c', // Light Orange
        '#c026d3', // Fuchsia
        '#0891b2'  // Dark Cyan
    ];
    
    // Fixed base variable colors
    const baseColors = {
        'r': { color: '#10b981', fill: true },
        'rep': { color: '#f59e0b', fill: false },
        's': { color: '#94a3b8', fill: false },
        'i': { color: '#ef4444', fill: false }
    };
    
    const normalizedKey = key.toLowerCase();
    
    if (baseColors[normalizedKey]) {
        return baseColors[normalizedKey];
    }
    
    // Check if variable already has a color assigned
    if (colorAssignments[normalizedKey]) {
        return { color: colorAssignments[normalizedKey], fill: false };
    }
    
    // Assign new color from palette (skip first 4 reserved for base vars)
    const usedColors = Object.values(colorAssignments);
    const availableColors = colorPalette.slice(4).filter(c => !usedColors.includes(c));
    
    const newColor = availableColors.length > 0 ? availableColors[0] : colorPalette[4];
    colorAssignments[normalizedKey] = newColor;
    
    return { color: newColor, fill: false };
}

/**
 * Clean variable name (remove 'dt' suffix if present)
 */
function cleanVariableName(key) {
    // Remove common derivative suffixes
    let cleaned = key.replace(/dt$/i, '').replace(/^d/, '').replace(/_dt$/i, '');
    // Remove 'new' prefix if present
    cleaned = cleaned.replace(/^new/i, '');
    return cleaned || key; // Fallback to original if cleaning results in empty string
}

/**
 * Update the variable chips display with remove buttons
 */
function updateVariableChips(variables) {
    const container = document.getElementById('variable-chips');
    if (!container) return;
    
    container.innerHTML = '';
    
    const baseVariables = ['S', 'I', 'R', 'Rep'];
    
    variables.forEach(varName => {
        const cleanName = cleanVariableName(varName);
        const chip = document.createElement('div');
        chip.className = 'variable-chip';
        chip.style.borderColor = getColorForVariable(varName).color + '80'; // 50% opacity
        
        chip.innerHTML = `
            <span class="var-name">${cleanName.toUpperCase()}</span>
            ${!baseVariables.includes(varName) ? 
                `<button class="remove-var-btn" onclick="removeVariable('${varName}')" title="Supprimer cette variable">×</button>` 
                : ''}
        `;
        container.appendChild(chip);
    });
}

/**
 * Remove a variable via API
 */
async function removeVariable(varName) {
    const cleanName = cleanVariableName(varName);
    
    if (!confirm(`Voulez-vous vraiment supprimer la variable "${cleanName.toUpperCase()}" ?`)) {
        return;
    }
    
    const btn = document.getElementById('btn-llm');
    btn.innerText = "SUPPRESSION...";
    btn.disabled = true;
    
    try {
        const res = await fetch('/llm_update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: `supprime la variable ${cleanName}` })
        });
        const result = await res.json();
        
        if (result.status === "success") {
            // Remove color assignment
            delete colorAssignments[varName.toLowerCase()];
            delete colorAssignments[cleanName.toLowerCase()];
            
            btn.innerText = "VARIABLE SUPPRIMÉE";
            btn.style.background = "#10b981";
            
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE SYSTÈME"; 
                btn.style.background = "#3b82f6";
                btn.disabled = false;
            }, 2000);
            
            update();
        } else {
            btn.innerText = "ÉCHEC SUPPRESSION";
            btn.style.background = "#ef4444";
            alert("Erreur: " + result.message);
            
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE SYSTÈME"; 
                btn.style.background = "#3b82f6";
                btn.disabled = false;
            }, 3000);
        }
    } catch (e) {
        btn.innerText = "ERREUR RÉSEAU";
        btn.style.background = "#ef4444";
        console.error(e);
        setTimeout(() => { 
            btn.innerText = "RECONFIGURER LE SYSTÈME"; 
            btn.style.background = "#3b82f6";
            btn.disabled = false; 
        }, 2000);
    }
}

/**
 * Fonction principale de mise à jour des simulations
 */
async function update() {
    const params = {
        S0: parseInt(document.getElementById('S0').value) || 100,
        beta: parseFloat(document.getElementById('beta').value),
        sigma: 0.2,
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
        if (!mainChart) initChart();

        const dataKeys = Object.keys(data).filter(key => key !== 't' && key !== 'formula');
        
        // Update variable chips
        activeVariables = dataKeys.map(k => k.charAt(0).toUpperCase() + k.slice(1));
        updateVariableChips(activeVariables);

        // Base labels only
        const baseLabelMap = {
            'r': 'REVENUS',
            'rep': 'RÉPUTATION',
            's': 'MARCHÉ',
            'i': 'OPÉRATIONS'
        };

        const newDatasets = dataKeys.map((key) => {
            const colorInfo = getColorForVariable(key);
            const cleanName = cleanVariableName(key);
            const label = baseLabelMap[key.toLowerCase()] || cleanName.toUpperCase();
            
            return {
                label: label,
                data: data[key],
                borderColor: colorInfo.color,
                backgroundColor: colorInfo.color + '1A',
                fill: colorInfo.fill,
                borderWidth: 3,
                tension: 0.4,
                pointRadius: 0
            };
        });

        mainChart.data.labels = data.t.map(v => `T${Math.floor(v/4)}`);
        mainChart.data.datasets = newDatasets;
        mainChart.update('none');

        updateKPIs(data, params);
        updateCEOAnalysis(data, params);
        document.getElementById('formula-display').textContent = data.formula;
        
    } catch (error) {
        console.error("Strategic Simulation Error:", error);
    }
}

/**
 * Mise à jour des indicateurs clés (KPIs)
 */
function updateKPIs(data, params) {
    const finalSuccess = data.r[data.r.length - 1];
    const peakLoad = Math.max(...data.i);
    const finalRep = data.rep[data.rep.length - 1];

    document.getElementById('kpi-success').innerText = `${finalSuccess.toFixed(1)}%`;
    document.getElementById('kpi-peak').innerText = peakLoad.toFixed(1);

    const riskElement = document.getElementById('kpi-risk');
    const riskDot = document.getElementById('risk-dot');
    
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
    const lastR = data.r[data.r.length - 1];
    const maxI = Math.max(...data.i);
    const repTrend = data.rep[50] - data.rep[0];

    let analysis = "<strong>Rapport de Situation :</strong><br>";

    if (repTrend < -20) {
        analysis += `<p class="danger"><strong>DÉGRADATION RAPIDE :</strong> Votre image s'effondre.</p>`;
    } else if (lastR > 90) {
        analysis += `<p class="success"><strong>MONOPOLE :</strong> Marché capturé à ${lastR.toFixed(1)}%.</p>`;
    }
    if (maxI > p.capacity) {
        analysis += `<p class="warning"><strong>SATURATION :</strong> Goulot détecté (Pic: ${maxI.toFixed(1)}).</p>`;
    }

    const coreKeys = ['t', 'formula', 's', 'i', 'r', 'rep'];
    Object.keys(data).forEach(key => {
        if (!coreKeys.includes(key)) {
            const values = data[key];
            const startVal = values[0];
            const endVal = values[values.length - 1];
            const trend = endVal - startVal;
            const cleanName = cleanVariableName(key);

            if (trend > 10) {
                analysis += `<p style="color:var(--accent)"><strong>NODE DYNAMIQUE :</strong> '${cleanName.toUpperCase()}' en forte croissance (+${trend.toFixed(1)}).</p>`;
            } else if (trend < -10) {
                analysis += `<p style="color:var(--danger)"><strong>NODE DYNAMIQUE :</strong> Déplétion critique de '${cleanName.toUpperCase()}'.</p>`;
            } else {
                analysis += `<p style="color:var(--text-secondary)"><strong>NODE DYNAMIQUE :</strong> '${cleanName.toUpperCase()}' stabilisée.</p>`;
            }
        }
    });

    expl.innerHTML = analysis;
}

/**
 * Gestion de la reconfiguration via IA
 */
document.getElementById('btn-llm').onclick = async () => {
    const promptInput = document.getElementById('llm-prompt');
    const prompt = promptInput.value;
    const btn = document.getElementById('btn-llm');
    
    if(!prompt) return;

    btn.innerText = "RECONFIGURATION...";
    btn.disabled = true;
    
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
            promptInput.value = "";
            
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE SYSTÈME"; 
                btn.style.background = "#3b82f6";
                btn.disabled = false;
            }, 2000);
            
            update();
        } else {
            btn.innerText = "STABILISATION ÉCHOUÉE";
            btn.style.background = "#ef4444";
            alert("Erreur Model Factory : " + result.message);
            
            setTimeout(() => { 
                btn.innerText = "RECONFIGURER LE SYSTÈME"; 
                btn.style.background = "#3b82f6";
                btn.disabled = false;
            }, 3000);
        }
    } catch (e) {
        btn.innerText = "ERREUR RÉSEAU";
        btn.style.background = "#ef4444";
        console.error(e);
        setTimeout(() => { 
            btn.innerText = "RECONFIGURER LE SYSTÈME"; 
            btn.style.background = "#3b82f6";
            btn.disabled = false; 
        }, 2000);
    }
};

/**
 * Gestion de la modale
 */
const modal = document.getElementById("strategy-modal");
const openBtn = document.getElementById("open-help");
const closeSpan = document.getElementsByClassName("close-modal")[0];

if (openBtn) openBtn.onclick = () => modal.style.display = "block";
if (closeSpan) closeSpan.onclick = () => modal.style.display = "none";
window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; }

// Force la mise à jour pour TOUS les types d'entrées
['input', 'change', 'keyup'].forEach(eventType => {
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener(eventType, () => {
            console.log("Changement détecté sur :", input.id, "Valeur :", input.value);
            update();
        });
    });
});

window.onload = () => {
    initChart();
    update();
};

window.onload = () => {
    initChart();
    update();
};