import numpy as np
from scipy.integrate import odeint

class AeroDynEngine:
    def __init__(self):
        # Dans engine.py, modifiez le bloc baseline_code :
        self.baseline_code = """
def deriv(y_dict, t, params):
    S, I, R, Rep = y_dict.get('S', 100), y_dict.get('I', 1), y_dict.get('R', 0), y_dict.get('Rep', 100)
    S0 = params.get('S0', 100)
    capacity = params.get('capacity', 40)
    N, beta, gamma = S0 + 1, params.get('beta', 0.4), params.get('gamma', 0.1)
    
    # --- LOGIQUE DE CAPACITÉ (C'est ce qui fera bouger les courbes !) ---
    # Si l'intégration (I) dépasse la capacité, le passage vers les revenus (R) ralentit
    gamma_eff = gamma if I <= capacity else gamma * (capacity / I)
    
    reputation_drag = 2.0 if Rep < 50 else 1.0
    sigma_eff = min(params.get('sigma', 0.2) * reputation_drag, 0.95)
    beta_eff = beta * (1 - sigma_eff)
    
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma_eff * I) # Utilise gamma_eff
    dRdt = gamma_eff * I                          # Utilise gamma_eff
    dRepdt = -0.05 * beta * I + 0.1 * (100 - Rep)
    
    return {'S': dSdt, 'I': dIdt, 'R': dRdt, 'Rep': dRepdt}
"""
        self.formula_code = self.baseline_code
        self.default_state = {'S': 100, 'I': 1, 'R': 0, 'Rep': 100}
        self._compile()

    def _compile(self):
        local_ns = {}
        exec(self.formula_code, globals(), local_ns)
        self.deriv_func = local_ns['deriv']

    def validate_logic(self, code_to_test):
        """Stress-Test identifying math explosions or negative drifting."""
        try:
            local_ns = {}
            clean_code = code_to_test.replace('\r\n', '\n').strip()
            exec(clean_code, globals(), local_ns)
            test_func = local_ns['deriv']
            
            # Discovery phase: determine all stocks the AI created
            dummy_y = {k: 1.0 for k in self.default_state}
            sample_output = test_func(dummy_y, 0, {'S0':100, 'beta':0.5, 'gamma':0.1})
            all_keys = list(sample_output.keys()) 
            
            # Simulation test
            y0 = [self.default_state.get(k, 0.0) if k in self.default_state else 0.0 for k in all_keys]
            def wrapper(y, t):
                d = test_func(dict(zip(all_keys, y)), t, {'S0':100, 'beta':1.5, 'gamma':0.1})
                return [d.get(k, 0) for k in all_keys]

            t_test = np.linspace(0, 40, 50)
            sol = odeint(wrapper, y0, t_test)
            
            # Validation criteria
            if np.any(np.abs(sol) > 5000): 
                return False, "Explosion numérique détectée (Boucle positive sans limite)."
            if np.any(sol < -0.1): 
                return False, "Valeur négative détectée (Dérive instable)."
                
            return True, all_keys 
        except Exception as e:
            return False, f"Erreur de Syntaxe Python : {str(e)}"

    def update_logic(self, new_code):
        is_valid, result = self.validate_logic(new_code)
        if not is_valid: 
            return False, result # Returns the error message
            
        # Update internal memory with new keys
        for k in result:
            if k not in self.default_state:
                self.default_state[k] = 0.0
                
        self.formula_code = new_code
        self._compile() 
        return True, None

    def reset_to_baseline(self):
        self.default_state = {'S': 100, 'I': 1, 'R': 0, 'Rep': 100}
        self.formula_code = self.baseline_code
        self._compile()

    def run(self, params):
        t = np.linspace(0, 160, 200)
        keys = list(self.default_state.keys())
        y0 = [self.default_state[k] for k in keys]
        
        def safe_wrapper(y, t, p, ks):
            y_dict = dict(zip(ks, y))
            class SafeParams(dict):
                def __getitem__(self, k): return self.get(k, 0.0)
            res = self.deriv_func(y_dict, t, SafeParams(p))
            return [res.get(k, 0) for k in ks]

        sol = odeint(safe_wrapper, y0, t, args=(params, keys))
        
        # Hard clipping ceiling to prevent graph display issues
        limit = params.get('S0', 100) * 2
        sol = np.clip(sol, -limit, limit) 
        
        results = {'t': t.tolist(), 'formula': self.formula_code}
        for i, key in enumerate(keys):
            results[key.lower()] = sol[:, i].tolist()
        return results
    
    def remove_variable(self, var_name):
        """Remove a variable from the system state"""
        if var_name in self.default_state:
            del self.default_state[var_name]
            print(f"[ENGINE] Removed variable '{var_name}' from state")
            return True
        return False
    # Dans engine.py, à l'intérieur de la classe AeroDynEngine

    def set_lobbying_scenario(self):
        """Injecte manuellement le scénario de démonstration Lobbying"""
        lobbying_code = """
def deriv(y_dict, t, params):
    # 1. Extraction des stocks
    S = y_dict.get('S', 100)
    I = y_dict.get('I', 1)
    R = y_dict.get('R', 0)
    Rep = y_dict.get('Rep', 100)
    Lobbying = y_dict.get('Lobbying', 0)
    
    # 2. Paramètres
    N = params.get('S0', 100) + 1
    beta = params.get('beta', 0.4)
    gamma = params.get('gamma', 0.1)
    sigma = params.get('sigma', 0.2)
    
    # 3. Logique Lobbying (10% des revenus convertis en influence, dépréciation 5%)
    # On utilise le flux (gamma * I) pour l'entrée du lobbying (Stock-Flow)
    inflow_lobby = 0.10 * (gamma * I)
    outflow_lobby = 0.05 * Lobbying
    dLobbyingdt = max(-Lobbying, inflow_lobby - outflow_lobby)
    
    # 4. Effet de saturation sur le frein politique (sigma)
    # Le lobbying réduit sigma (max 50% de réduction) via une fonction de saturation
    saturation_effect = Lobbying / (Lobbying + 10) # Courbe de saturation
    sigma_eff_lobby = sigma * (1 - 0.5 * saturation_effect)
    
    # 5. Dynamique de base AeroDyn
    reputation_drag = 2.0 if Rep < 50 else 1.0
    sigma_total = min(sigma_eff_lobby * reputation_drag, 0.95)
    beta_eff = beta * (1 - sigma_total)
    
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma * I)
    dRdt = gamma * I
    dRepdt = -0.05 * beta * I + 0.1 * (100 - Rep)
    
    return {'S': dSdt, 'I': dIdt, 'R': dRdt, 'Rep': dRepdt, 'Lobbying': dLobbyingdt}
"""
        # Mises à jour internes
        self.default_state['Lobbying'] = 0.0
        self.formula_code = lobbying_code
        self._compile()
        return True