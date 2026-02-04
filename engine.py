import numpy as np
from scipy.integrate import odeint

class AeroDynEngine:
    def __init__(self):
        self.formula_code = """
def deriv(y, t, params):
    S, I, R = y
    N = params['S0'] + 1
    beta_eff = params['beta'] * (1 - params['sigma'])
    
    # Goulot d'étranglement industriel
    if I > params['capacity'] and I > 0:
        gamma_eff = params['gamma'] * (params['capacity'] / I)
    else:
        gamma_eff = params['gamma']
        
    dSdt = -(beta_eff * S * I) / N
    dIdt = (beta_eff * S * I) / N - (gamma_eff * I)
    dRdt = gamma_eff * I
    return [dSdt, dIdt, dRdt]
"""
        self._compile()

    def _compile(self):
        local_ns = {}
        exec(self.formula_code, globals(), local_ns)
        self.deriv_func = local_ns['deriv']

    def run(self, params):
        t = np.linspace(0, params['t_max'], 200) # Points optimisés pour fluidité
        y0 = [params['S0'], 1, 0]
        sol = odeint(self.deriv_func, y0, t, args=(params,))
        return t.tolist(), sol[:, 0].tolist(), sol[:, 1].tolist(), sol[:, 2].tolist()