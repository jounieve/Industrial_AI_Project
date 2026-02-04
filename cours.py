import streamlit as st
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Configuration de la page
st.set_page_config(page_title="Erodyn Strategic Simulator", layout="wide")

# --- MOTEUR DE CALCUL (LOGIQUE SYSTÈME) ---
def erodyn_engine(S0, I0, beta, gamma, sigma, capacity, t_max):
    N = S0 + I0
    t = np.linspace(0, t_max, 500)
    
    def deriv(y, t):
        S, I, R = y
        # RELATION 1 : Frein politique sur l'efficacité des ventes
        beta_eff = beta * (1 - sigma)
        
        # RELATION 2 : Goulot d'étranglement industriel (Saturation)
        # Si le nombre d'intégrations (I) dépasse la capacité, le flux vers 'R' ralentit
        gamma_eff = gamma if I <= capacity else gamma * (capacity / I)
        
        dSdt = -(beta_eff * S * I) / N
        dIdt = (beta_eff * S * I) / N - (gamma_eff * I)
        dRdt = gamma_eff * I
        return [dSdt, dIdt, dRdt]

    res = odeint(deriv, [S0, I0, 0], t)
    return t, res.T

# --- INTERFACE UTILISATEUR ---
st.title("Erodyn : Simulateur de Dynamique des Systèmes IA")
st.markdown("---")

# Layout en colonnes : Paramètres à gauche, Graphique au centre, Guide à droite
col_params, col_plot, col_guide = st.columns([1, 2, 1])

with col_params:
    st.header("Paramètres")
    
    with st.expander("Marché & Ventes", expanded=True):
        S0 = st.number_input("Taille du Marché (N)", 10, 500, 100, help="Nombre total de Ministères de la Défense ciblés.")
        beta = st.slider("Agressivité Commerciale (β)", 0.05, 1.0, 0.4, help="Vitesse à laquelle vos équipes signent des contrats.")

    with st.expander("Éthique & Politique", expanded=True):
        sigma = st.slider("Scrutin Politique (σ)", 0.0, 0.9, 0.2, help="Niveau de blocage réglementaire. Réduit directement l'impact de vos ventes.")

    with st.expander("Opérations & Usine", expanded=True):
        capacity = st.slider("Capacité de Livraison", 5, 100, 40, help="Nombre max de systèmes que vous pouvez gérer en simultané.")
        gamma = st.slider("Efficacité Intégration (γ)", 0.01, 0.3, 0.1, help="Rapidité de passage du test à l'opérationnel.")
    
    t_max = st.number_input("Durée Simulation (Trimestres)", 50, 500, 160)

# --- CALCULS ---
t, (S, I, R) = erodyn_engine(S0, 1, beta, gamma, sigma, capacity, t_max)

with col_plot:
    # Création du graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(t, S, color="#34495e", alpha=0.1, label='Marché Restant (Prospects)')
    ax.plot(t, I, color="#c0392b", lw=4, label='Intégration Active (Risque Ops)')
    ax.plot(t, R, color="#27ae60", lw=3, label='Systèmes Matures (Revenus)')
    
    # Ligne de capacité
    ax.axhline(y=capacity, color='orange', ls='--', alpha=0.6, label='Limite Capacité Industrielle')
    
    ax.set_title("Dynamique d'Adoption du Marché", fontsize=14)
    ax.set_xlabel("Trimestres")
    ax.set_ylabel("Nombre de Ministères")
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)

    # Indicateurs clés sous le graphique
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Pic de Charge", f"{int(max(I))} MoD")
    kpi2.metric("Ventes Nettes (Beta Eff.)", f"{beta*(1-sigma):.2f}")
    kpi3.metric("Succès Final", f"{int(R[-1])} %")

with col_guide:
    st.header("Guide d'Analyse")
    
    # Analyse dynamique contextuelle
    st.subheader("Diagnostic en temps réel")
    if max(I) > capacity:
        st.error("🚨 **CRITICAL BOTTLE NECK** : Votre agressivité commerciale dépasse votre capacité de livraison. Les clients vont s'accumuler en phase de test.")
    elif sigma > 0.5:
        st.warning("⚠️ **FREIN POLITIQUE** : La pression éthique est si forte qu'elle neutralise vos efforts de vente. L'adoption sera très lente.")
    else:
        st.success("✅ **FLUX OPTIMISÉ** : Le système semble équilibré entre ventes et livraisons.")

    st.info("""
    **Comment tester ?**
    - **Pour tester la saturation :** Montez l'Agressivité et baissez la Capacité.
    - **Pour tester le Lobbying :** Baissez le Scrutin Politique (sigma) et observez l'accélération de la courbe verte.
    - **Pour tester l'Obsolescence :** Baissez l'Efficacité (gamma) ; si la courbe rouge reste haute trop longtemps, vous risquez de perdre le marché.
    """)

# Affichage de la structure de données pour transparence
with st.expander("Structure de données (Matrice de simulation)"):
    import pandas as pd
    data_log = pd.DataFrame({'Trimestre': t, 'S_Stock': S, 'I_Stock': I, 'R_Stock': R})
    st.dataframe(data_log.head(10))