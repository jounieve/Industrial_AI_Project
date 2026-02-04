import numpy as np
from scipy.integrate import odeint

class AeroDynEngine:
    def __init__(self):
        # Modèle de base : S (Marché), I (Intégration), R (Revenu), Rep (Réputation)
        self.formula_code = """
def deriv(y, t, params):
    S, I, R, Rep = y
    N = params['S0'] + 1
    
    # Mécanisme de Réputation : Si Rep < 50, le frein politique sigma augmente
    reputation_drag = 2.0 if Rep < 50 else 1.0
    sigma_eff = min(params['sigma'] * reputation_drag, 0.95)
    
    # Efficacité commerciale impactée par le climat politique
    beta_eff = params['beta'] * (1 - sigma_eff)
    
    # Goulot d'étranglement industriel
    if I > params['capacity'] and I > 0:
        gamma_eff = params['gamma'] * (params['capacity'] / I)
    else:
        gamma_eff = params['gamma']
        
    # Équations du système
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma_eff * I)
    dRdt = gamma_eff * I
    
    # Dynamique de la Réputation : baisse avec l'autonomie (beta), remonte par l'éthique
    dRepdt = -0.05 * params['beta'] * I + 0.1 * (100 - Rep)
    
    return [dSdt, dIdt, dRdt, dRepdt]
"""
        self._compile()

    def _compile(self):
        local_ns = {}
        exec(self.formula_code, globals(), local_ns)
        self.deriv_func = local_ns['deriv']

    def update_logic(self, new_code):
        try:
            self.formula_code = new_code
            self._compile()
            return True
        except:
            return False

    def run(self, params):
        t = np.linspace(0, 160, 200) 
        y0 = [params['S0'], 1, 0, 100]
        sol = odeint(self.deriv_func, y0, t, args=(params,))
        return (t.tolist(), sol[:, 0].tolist(), sol[:, 1].tolist(), 
                sol[:, 2].tolist(), sol[:, 3].tolist())