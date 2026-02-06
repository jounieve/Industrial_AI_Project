import numpy as np
import json
import datetime
from scipy.integrate import odeint

class AeroDynEngine:
    def __init__(self):
        """
        Initialise le moteur avec le modèle de base S-I-R étendu.
        """
        self.baseline_code = """
def deriv(y_dict, t, params):
    # --- Extraction des Stocks ---
    S, I, R, Rep = y_dict.get('S', 100), y_dict.get('I', 1), y_dict.get('R', 0), y_dict.get('Rep', 100)
    
    # --- Configuration Environnementale ---
    S0 = params.get('S0', 100)
    capacity = params.get('capacity', 40)
    N, beta, gamma = S0 + 1, params.get('beta', 0.4), params.get('gamma', 0.1)
    
    # --- LOGIQUE DE CAPACITÉ INDUSTRIELLE ---
    # Si l'intégration (I) dépasse la capacité, le passage vers les revenus (R) ralentit
    gamma_eff = gamma if I <= capacity else gamma * (capacity / I)
    
    # --- LOGIQUE DE RÉPUTATION ---
    reputation_drag = 2.0 if Rep < 50 else 1.0
    sigma_eff = min(params.get('sigma', 0.2) * reputation_drag, 0.95)
    beta_eff = beta * (1 - sigma_eff)
    
    # --- ÉQUATIONS DIFFÉRENTIELLES ---
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma_eff * I)
    dRdt = gamma_eff * I
    dRepdt = -0.05 * beta * I + 0.1 * (100 - Rep)
    
    return {'S': dSdt, 'I': dIdt, 'R': dRdt, 'Rep': dRepdt}
"""
        self.formula_code = self.baseline_code
        self.default_state = {'S': 100, 'I': 1, 'R': 0, 'Rep': 100}
        self._compile()
        self.save_state_to_json() # Persistance initiale à la création

    def _compile(self):
        """Compile la chaîne de caractères Python en fonction exécutable."""
        local_ns = {}
        exec(self.formula_code, globals(), local_ns)
        self.deriv_func = local_ns['deriv']

    def save_state_to_json(self):
        """
        Crée un registre permanent (JSON) de l'état du système et de son code.
        Visible par l'utilisateur/professeur pour prouver la modification du 'DNA'.
        """
        state_payload = {
            "last_update": str(datetime.datetime.now()),
            "active_variables": list(self.default_state.keys()),
            "python_logic": self.formula_code
        }
        with open('strategic_state.json', 'w', encoding='utf-8') as f:
            json.dump(state_payload, f, indent=4, ensure_ascii=False)
        print("[DATABASE] State persisted to strategic_state.json")

    def validate_logic(self, code_to_test):
        """
        Stress-test du code généré par l'IA :
        1. Vérifie la syntaxe.
        2. Découvre dynamiquement les nouvelles variables.
        3. Détecte les explosions numériques ou dérives négatives.
        """
        try:
            local_ns = {}
            clean_code = code_to_test.replace('\r\n', '\n').strip()
            exec(clean_code, globals(), local_ns)
            test_func = local_ns['deriv']
            
            # Phase 1 : Découverte des clés (Stocks)
            dummy_y = {k: 1.0 for k in self.default_state}
            sample_output = test_func(dummy_y, 0, {'S0':100, 'beta':0.5, 'gamma':0.1})
            all_keys = list(sample_output.keys()) 
            
            # Phase 2 : Simulation test
            y0 = [self.default_state.get(k, 0.0) if k in self.default_state else 0.0 for k in all_keys]
            def wrapper(y, t):
                d = test_func(dict(zip(all_keys, y)), t, {'S0':100, 'beta':1.5, 'gamma':0.1})
                return [d.get(k, 0) for k in all_keys]

            t_test = np.linspace(0, 40, 50)
            sol = odeint(wrapper, y0, t_test)
            
            # Phase 3 : Critères de rejet
            if np.any(np.abs(sol) > 5000): 
                return False, "Explosion numérique détectée (Boucle positive sans limite)."
            if np.any(sol < -0.1): 
                return False, "Valeur négative détectée (Dérive instable)."
                
            return True, all_keys 
        except Exception as e:
            return False, f"Erreur de Syntaxe Python : {str(e)}"

    def update_logic(self, new_code):
        """Met à jour le moteur si le code passe les tests de sécurité."""
        is_valid, result = self.validate_logic(new_code)
        if not is_valid: 
            return False, result
            
        # Synchronisation de la mémoire (ajout des nouveaux stocks)
        for k in result:
            if k not in self.default_state:
                print(f"[ENGINE] New variable discovered: {k}")
                self.default_state[k] = 0.0
                
        self.formula_code = new_code
        self._compile() 
        self.save_state_to_json() # Sauvegarde automatique après modification
        return True, None

    def reset_to_baseline(self):
        """Restaure l'état d'origine S-I-R-Rep."""
        self.default_state = {'S': 100, 'I': 1, 'R': 0, 'Rep': 100}
        self.formula_code = self.baseline_code
        self._compile()
        self.save_state_to_json()

    def run(self, params):
        """Exécute la simulation complète."""
        t = np.linspace(0, 160, 200)
        keys = list(self.default_state.keys())
        y0 = [self.default_state[k] for k in keys]
        
        def safe_wrapper(y, t, p, ks):
            y_dict = dict(zip(ks, y))
            # Utilise un dictionnaire sécurisé pour éviter les KeyErrors
            class SafeParams(dict):
                def __getitem__(self, k): return self.get(k, 0.0)
            res = self.deriv_func(y_dict, t, SafeParams(p))
            return [res.get(k, 0) for k in ks]

        sol = odeint(safe_wrapper, y0, t, args=(params, keys))
        
        # Écrêtage pour éviter les erreurs graphiques
        limit = params.get('S0', 100) * 2
        sol = np.clip(sol, -limit, limit) 
        
        results = {'t': t.tolist(), 'formula': self.formula_code}
        for i, key in enumerate(keys):
            results[key.lower()] = sol[:, i].tolist()
        return results
    
    def remove_variable(self, var_name):
        """Supprime proprement une variable du dictionnaire d'état."""
        if var_name in self.default_state:
            del self.default_state[var_name]
            print(f"[ENGINE] Removed variable '{var_name}' from state")
            self.save_state_to_json()
            return True
        return False

    def set_lobbying_scenario(self):
        """
        Injecte manuellement le scénario de démonstration Lobbying.
        Utilisé pour garantir une stabilité totale pendant l'oral.
        """
        lobbying_code = """
def deriv(y_dict, t, params):
    S, I, R, Rep = y_dict.get('S', 100), y_dict.get('I', 1), y_dict.get('R', 0), y_dict.get('Rep', 100)
    Lobbying = y_dict.get('Lobbying', 0)
    
    S0, capacity = params.get('S0', 100), params.get('capacity', 40)
    N, beta, gamma, sigma = S0 + 1, params.get('beta', 0.4), params.get('gamma', 0.1), params.get('sigma', 0.2)
    
    # --- DYNAMIQUE LOBBYING (Courbe en cloche) ---
    # Alimentation modérée (0.05) et dépréciation forte (0.1) pour voir la redescente
    inflow_lobby = 0.05 * (gamma * I)
    outflow_lobby = 0.1 * Lobbying
    dLobbyingdt = max(-Lobbying, inflow_lobby - outflow_lobby)
    
    # --- IMPACT AGGRESSIF ---
    # Saturation rapide (K=5) pour un effet immédiat
    influence = Lobbying / (Lobbying + 5)
    
    # Réduction de 90% du frein politique et protection de la réputation
    sigma_lobby = sigma * (1 - 0.9 * influence)
    rep_shield = 1 - (0.7 * influence) 
    
    gamma_eff = gamma if I <= capacity else gamma * (capacity / I)
    reputation_drag = 2.0 if Rep < 50 else 1.0
    sigma_total = min(sigma_lobby * reputation_drag, 0.95)
    beta_eff = beta * (1 - sigma_total)
    
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma_eff * I)
    dRdt = gamma_eff * I
    dRepdt = (-0.05 * beta * I * rep_shield) + 0.1 * (100 - Rep)
    
    return {'S': dSdt, 'I': dIdt, 'R': dRdt, 'Rep': dRepdt, 'Lobbying': dLobbyingdt}
"""
        self.default_state['Lobbying'] = 0.0
        self.formula_code = lobbying_code
        self._compile()
        self.save_state_to_json()
        print("[DEMO] Lobbying scenario activated and saved to JSON.")
        return True