# 🛡️ AeroDyn Strategic Control Tower

**Aide à la décision pour l'intégration de l'IA dans les systèmes de défense.**

## 1. Vision Stratégique
L'interface **AeroDyn** est une **"Model Factory"** conçue pour explorer les conséquences systémiques de l'IA sur un horizon de 10 ans.  
Elle permet de simuler l'équilibre entre l'agressivité technologique, la capacité industrielle et l'acceptabilité politique via des équations différentielles gérées par IA.

---

## 2. Installation et Lancement

Pour garantir la stabilité du système, suivez ces étapes de déploiement :

### Prérequis
- **Python 3.9+**
- **Ollama** (installé et configuré)

### Procédure de lancement

1. **Création de l'environnement virtuel :**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Installation des dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration du moteur d'IA (LLM) :**
   - Modèle recommandé (précision logique maximale) :
     ```bash
     ollama pull qwen2.5-coder:7b
     ```
   - Alternatives légères (optimisées pour moins de RAM) :
     ```bash
     #Perforamnces moindres / Erreurs systématiques 
     ollama pull dolphin-phi
     ollama pull llama3.2:latest 
     ```

4. **Exécution du serveur :**
   ```bash
   python main.py
   ```

5. **Accès à l'interface :**
   Ouvrez votre navigateur sur **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 3. Architecture de l'Interface

Le tableau de bord est structuré pour un pilotage décisionnel fluide et modulaire :

### A. Contrôle Opérationnel *(Sidebar)*
- **Orientation IA (β)** : Ajuste l'agressivité commerciale (autonomie de l'IA).  
- **Capacité Usine** : Définit le plafond industriel pour éviter les goulots d'étranglement.  
- **Model Factory (IA)** : Reconfigure en temps réel la logique mathématique du moteur via GenAI.

### B. Visualisation Dynamique *(Centre)*
- **Graphique Temps Réel** : Visualise les stocks (Marché, Opérations, Revenus, Réputation).  
- **KPIs Flash** : Indicateurs de Pénétration Marché, Risque Réglementaire (basé sur la Réputation) et Pic de Charge.

### C. Intelligence Système *(Bas)*
- **Insights Décisionnels** : Analyse automatique des tendances et détection des nouveaux *nodes*.  
- **Logique Système (Moteur SD)** : Affiche le code Python `deriv()` compilé dynamiquement par l'IA.

---

## 4. Logique du Moteur (Moteur SD)

Le système repose sur un modèle de **dynamique des systèmes** inspiré du schéma S-I-R étendu :

- **Marché (S)** : Clients potentiels (Ministères de la Défense).  
- **Intégration (I)** : Phase opérationnelle limitée par la Capacité Usine.  
- **Revenus (R)** : Capital généré par les systèmes déployés.  
- **Réputation (Rep)** : Capital immatériel régulant l’accès au marché.

---

## 5. Scénarios de Test (Démonstration)

Utilisez ces *prompts* dans le panneau **Model Factory** pour tester la résilience du modèle :

### Scénario 1 : La Stratégie d'Influence *(Lobbying)*
**Prompt :**  
> "Ajoute une variable 'Lobbying' alimentée par 10% des revenus, avec une dépréciation de 5% et une fonction de saturation pour réduire le frein politique."

**Objectif :**  
Montrer comment une nouvelle variable stabilise la croissance malgré une faible réputation.

---

### Scénario 2 : La Crise Diplomatique *(Sanctions)*
**Prompt :**  
> "Simule des sanctions : ajoute une variable 'Sanctions' s'activant si la Réputation < 40, réduisant la capacité usine de 50%."

**Objectif :**  
Observer la chute brutale des revenus et l’alerte automatique dans les *Insights Décisionnels*.

---

### Scénario 3 : Sécurité et Réinitialisation *(Reset)*
**Prompt :**  
> "Reset au modèle de base."

**Objectif :**  
Démontrer le mécanisme de **Hard Reset** qui purge instantanément les modifications de l’IA pour restaurer la baseline d’origine.

---

## 6. Synthèse

AeroDyn transforme l’ambiguïté stratégique en **insights actionnables**,  offrant un **jumeau numérique vivant** pour la simulation et la prise de décision stratégique.
