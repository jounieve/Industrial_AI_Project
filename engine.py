import numpy as np
import json
import datetime
from scipy.integrate import odeint

class AeroDynEngine:
    def __init__(self):
        """
        Initialize engine with JSON-based model representation.
        Instead of storing Python code strings, we store structured JSON.
        """
        self.model_state = {
            "stocks": {
                "S": {"initial": 100, "description": "Market potential"},
                "I": {"initial": 1, "description": "Operations"},
                "R": {"initial": 0, "description": "Revenue"},
                "Rep": {"initial": 100, "description": "Reputation"}
            },
            "parameters": {
                "S0": 100,
                "beta": 0.4,
                "gamma": 0.1,
                "sigma": 0.2,
                "capacity": 40
            },
            "intermediates": {
                "N": "params.get('S0', 100) + 1",
                "beta_param": "params.get('beta', 0.4)",
                "gamma_param": "params.get('gamma', 0.1)",
                "capacity": "params.get('capacity', 40)",
                "gamma_eff": "gamma_param if I <= capacity else gamma_param * (capacity / I)",
                "reputation_drag": "2.0 if Rep < 50 else 1.0",
                "sigma_eff": "min(params.get('sigma', 0.2) * reputation_drag, 0.95)",
                "beta_eff": "beta_param * (1 - sigma_eff)"
            },
            "derivatives": {
                "S": {
                    "formula": "-(beta_eff * S * I) / N",
                    "description": "Market depletion"
                },
                "I": {
                    "formula": "(beta_eff * S * I) / N - (gamma_eff * I)",
                    "description": "Operations flow"
                },
                "R": {
                    "formula": "gamma_eff * I",
                    "description": "Revenue accumulation"
                },
                "Rep": {
                    "formula": "-0.05 * beta_param * I + 0.1 * (100 - Rep)",
                    "description": "Reputation dynamics"
                }
            }
        }
        
        self.baseline_state = json.loads(json.dumps(self.model_state))  # Deep copy
        self._generate_code()
        self.save_state_to_json()

    def _generate_code(self):
        """
        Automatically generate Python code from JSON state.
        This eliminates LLM from code generation - it's purely mechanical.
        """
        code_lines = ["def deriv(y_dict, t, params):"]
        
        # 1. Extract all stocks
        code_lines.append("    # --- Stock Extraction ---")
        for stock_name, stock_data in self.model_state["stocks"].items():
            initial = stock_data["initial"]
            code_lines.append(f"    {stock_name} = y_dict.get('{stock_name}', {initial})")
        code_lines.append("")
        
        # 2. Calculate intermediates
        code_lines.append("    # --- Intermediate Calculations ---")
        for var_name, formula in self.model_state["intermediates"].items():
            code_lines.append(f"    {var_name} = {formula}")
        code_lines.append("")
        
        # 3. Calculate derivatives
        code_lines.append("    # --- Derivatives ---")
        for stock_name, deriv_data in self.model_state["derivatives"].items():
            formula = deriv_data["formula"]
            desc = deriv_data.get("description", "")
            if desc:
                code_lines.append(f"    # {desc}")
            code_lines.append(f"    d{stock_name}dt = {formula}")
        code_lines.append("")
        
        # 4. Return dictionary
        code_lines.append("    # --- Return ---")
        return_items = [f"'{stock}': d{stock}dt" for stock in self.model_state["stocks"].keys()]
        code_lines.append(f"    return {{{', '.join(return_items)}}}")
        
        self.formula_code = '\n'.join(code_lines)
        self._compile()

    def _compile(self):
        """Compile the generated code into executable function."""
        local_ns = {}
        exec(self.formula_code, globals(), local_ns)
        self.deriv_func = local_ns['deriv']

    def add_stock(self, stock_name, initial_value=0, description="", inflow=None, outflow=None, custom_derivative=None):
        """
        Add a new stock to the model using diff-based approach.
        
        Args:
            stock_name: Name of the stock (e.g., 'Lobbying')
            initial_value: Initial value (default 0)
            description: Human-readable description
            inflow: Expression for inflow (e.g., '0.1 * (gamma_param * I)')
            outflow: Expression for outflow (e.g., '0.05 * Lobbying')
            custom_derivative: Full derivative formula if not using inflow-outflow pattern
        """
        print(f"[ENGINE] Adding stock: {stock_name}")
        
        # 1. Add to stocks
        self.model_state["stocks"][stock_name] = {
            "initial": initial_value,
            "description": description
        }
        
        # 2. Add intermediate calculations if using inflow-outflow
        if inflow and outflow:
            self.model_state["intermediates"][f"inflow_{stock_name.lower()}"] = inflow
            self.model_state["intermediates"][f"outflow_{stock_name.lower()}"] = outflow
            
            # 3. Add derivative with positivity guard
            derivative_formula = f"max(-{stock_name}, inflow_{stock_name.lower()} - outflow_{stock_name.lower()})"
        elif custom_derivative:
            derivative_formula = custom_derivative
        else:
            raise ValueError("Must provide either (inflow, outflow) or custom_derivative")
        
        self.model_state["derivatives"][stock_name] = {
            "formula": derivative_formula,
            "description": description
        }
        
        # 4. Regenerate code from updated JSON
        self._generate_code()
        self.save_state_to_json()
        
        return True

    def remove_stock(self, stock_name):
        """
        Remove a stock from the model.
        """
        print(f"[ENGINE] Removing stock: {stock_name}")
        
        # Remove from stocks
        if stock_name in self.model_state["stocks"]:
            del self.model_state["stocks"][stock_name]
        
        # Remove derivative
        if stock_name in self.model_state["derivatives"]:
            del self.model_state["derivatives"][stock_name]
        
        # Remove related intermediates
        inflow_key = f"inflow_{stock_name.lower()}"
        outflow_key = f"outflow_{stock_name.lower()}"
        if inflow_key in self.model_state["intermediates"]:
            del self.model_state["intermediates"][inflow_key]
        if outflow_key in self.model_state["intermediates"]:
            del self.model_state["intermediates"][outflow_key]
        
        # Regenerate code
        self._generate_code()
        self.save_state_to_json()
        
        return True

    def modify_intermediate(self, var_name, new_formula):
        """Modify an intermediate calculation."""
        print(f"[ENGINE] Modifying intermediate: {var_name}")
        self.model_state["intermediates"][var_name] = new_formula
        self._generate_code()
        self.save_state_to_json()

    def modify_derivative(self, stock_name, new_formula):
        """Modify a derivative formula."""
        print(f"[ENGINE] Modifying derivative for: {stock_name}")
        if stock_name in self.model_state["derivatives"]:
            self.model_state["derivatives"][stock_name]["formula"] = new_formula
            self._generate_code()
            self.save_state_to_json()

    def get_current_state(self):
        """Return the current model state as JSON."""
        return json.dumps(self.model_state, indent=2)

    def validate_logic(self):
        """
        Test the current model for stability.
        Since code generation is mechanical, we only need to test physics.
        """
        try:
            # Get initial values
            stocks = list(self.model_state["stocks"].keys())
            y0 = [self.model_state["stocks"][s]["initial"] for s in stocks]
            
            def wrapper(y, t):
                y_dict = dict(zip(stocks, y))
                params = self.model_state["parameters"]
                d = self.deriv_func(y_dict, t, params)
                return [d.get(k, 0) for k in stocks]
            
            # Test simulation
            t_test = np.linspace(0, 40, 50)
            sol = odeint(wrapper, y0, t_test)
            
            # Check for explosions or negative values
            if np.any(np.abs(sol) > 5000):
                return False, "Explosion détectée (valeurs > 5000)"
            if np.any(sol < -0.1):
                return False, "Valeurs négatives détectées"
            
            return True, "Stable"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def reset_to_baseline(self):
        """Reset to original baseline model."""
        print("[ENGINE] Resetting to baseline...")
        self.model_state = json.loads(json.dumps(self.baseline_state))
        self._generate_code()
        self.save_state_to_json()

    def save_state_to_json(self):
        """Save the current model state as JSON history."""
        new_entry = {
            "timestamp": str(datetime.datetime.now()),
            "model_state": self.model_state,
            "generated_code": self.formula_code
        }
        
        history = []
        try:
            with open('strategic_state.json', 'r', encoding='utf-8') as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = [history]
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        
        history.append(new_entry)
        
        with open('strategic_state.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        print(f"[DATABASE] Version {len(history)} saved")

    def run(self, params):
        """Execute simulation."""
        t = np.linspace(0, 160, 200)
        stocks = list(self.model_state["stocks"].keys())
        y0 = [self.model_state["stocks"][s]["initial"] for s in stocks]
        
        def safe_wrapper(y, t, p, ks):
            y_dict = dict(zip(ks, y))
            
            class SafeParams(dict):
                def __getitem__(self, k):
                    return self.get(k, 0.0)
            
            res = self.deriv_func(y_dict, t, SafeParams(p))
            return [res.get(k, 0) for k in ks]
        
        sol = odeint(safe_wrapper, y0, t, args=(params, stocks))
        
        # Clip to prevent graph errors
        limit = params.get('S0', 100) * 2
        sol = np.clip(sol, -limit, limit)
        
        results = {'t': t.tolist(), 'formula': self.formula_code}
        for i, stock in enumerate(stocks):
            results[stock.lower()] = sol[:, i].tolist()
        
        return results

    @property
    def default_state(self):
        """Compatibility property for old code."""
        return {k: v["initial"] for k, v in self.model_state["stocks"].items()}