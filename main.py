from flask import Flask, render_template, request, jsonify
from engine import AeroDynEngine
import datetime
import ollama
import json
import re

app = Flask(__name__)
engine = AeroDynEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    params = request.json
    results = engine.run(params)
    return jsonify(results)

@app.route('/llm_update', methods=['POST'])
def llm_update():
    user_req = request.json.get('prompt', '').lower()
    print(f"\n[STRATEGIC LOG] User Request: {user_req}")
    
    # --- FORCE RESET ---
    if any(word in user_req for word in ["reset", "revenir", "initial", "baseline"]):
        print("[SYSTEM] Force Resetting to Baseline...")
        engine.reset_to_baseline()
        return jsonify({"status": "success", "new_code": engine.formula_code})

    # --- VARIABLE REMOVAL ---
    removal_keywords = ["supprime", "enlève", "retire", "delete", "remove"]
    if any(word in user_req for word in removal_keywords):
        base_vars = ['S', 'I', 'R', 'Rep']
        current_vars = list(engine.model_state["stocks"].keys())
        removable_vars = [v for v in current_vars if v not in base_vars]
        
        target_var = None
        for var in removable_vars:
            if var.lower() in user_req:
                target_var = var
                break
        
        if target_var:
            print(f"[SYSTEM] Removing variable: {target_var}")
            engine.remove_stock(target_var)
            return jsonify({"status": "success", "new_code": engine.formula_code})

    # --- DIFF-BASED SYSTEM PROMPT ---
    system_prompt = (
        "You are a System Dynamics expert. Instead of generating full Python code, "
        "you will provide STRUCTURED JSON instructions for adding/modifying model elements.\n\n"
        
        f"CURRENT MODEL STATE:\n{engine.get_current_state()}\n\n"
        
        "### YOUR TASK ###\n"
        "Analyze the user request and return a JSON object with this EXACT structure:\n\n"
        
        "```json\n"
        "{\n"
        '  "operation": "add_stock",\n'
        '  "stock_name": "Lobbying",\n'
        '  "initial_value": 0,\n'
        '  "description": "Political influence",\n'
        '  "inflow": "0.1 * (gamma_param * I)",\n'
        '  "outflow": "0.05 * Lobbying"\n'
        "}\n"
        "```\n\n"
        
        "### CRITICAL RULES ###\n"
        "1. **STOCK NAME**: Capitalized (e.g., 'Lobbying', 'Sanctions', 'Budget')\n\n"
        
        "2. **REVENUE FLOW**: For growth from revenue, ALWAYS use:\n"
        "   'gamma_param * I' (this is the revenue FLOW)\n"
        "   NEVER use 'R' (accumulated stock)\n"
        "   Example: \"inflow\": \"0.1 * (gamma_param * I)\"\n\n"
        
        "3. **OUTFLOW**: Use the stock variable name:\n"
        "   Example: \"outflow\": \"0.05 * Lobbying\"\n\n"
        
        "4. **CONDITIONAL LOGIC**: For triggers, use ternary:\n"
        "   Example: \"inflow\": \"1.0 if Rep < 40 else 0.0\"\n\n"
        
        "5. **SATURATION**: Apply in inflow:\n"
        "   Example: \"inflow\": \"0.1 * (gamma_param * I) * (100 - Research) / 100\"\n\n"
        
        "### EXAMPLES ###\n\n"
        
        "**Example 1: Revenue-based growth**\n"
        "User: 'ajoute lobbying alimenté par 10% des revenus avec 5% dépréciation'\n"
        "```json\n"
        "{\n"
        '  "operation": "add_stock",\n'
        '  "stock_name": "Lobbying",\n'
        '  "initial_value": 0,\n'
        '  "description": "Political lobbying influence",\n'
        '  "inflow": "0.1 * (gamma_param * I)",\n'
        '  "outflow": "0.05 * Lobbying"\n'
        "}\n"
        "```\n\n"
        
        "**Example 2: Conditional trigger**\n"
        "User: 'ajoute sanctions activées si réputation < 40'\n"
        "```json\n"
        "{\n"
        '  "operation": "add_stock",\n'
        '  "stock_name": "Sanctions",\n'
        '  "initial_value": 0,\n'
        '  "description": "Economic sanctions level",\n'
        '  "inflow": "0.5 if Rep < 40 else 0.0",\n'
        '  "outflow": "0.1 * Sanctions"\n'
        "}\n"
        "```\n\n"
        
        "**Example 3: Complex calculation**\n"
        "User: 'ajoute budget avec 15% revenus moins 10% coûts'\n"
        "```json\n"
        "{\n"
        '  "operation": "add_stock",\n'
        '  "stock_name": "Budget",\n'
        '  "initial_value": 0,\n'
        '  "description": "Operational budget",\n'
        '  "inflow": "0.15 * (gamma_param * I)",\n'
        '  "outflow": "0.10 * Budget"\n'
        "}\n"
        "```\n\n"
        
        "### OUTPUT ###\n"
        "Return ONLY the JSON object. No explanations, no markdown, just pure JSON."
    )

    def parse_ai_response(response_text):
        """
        Extract JSON from AI response.
        Handles markdown code blocks and extra text.
        """
        # Remove markdown code blocks
        clean = response_text.strip()
        clean = re.sub(r'```json\s*', '', clean)
        clean = re.sub(r'```\s*', '', clean)
        
        # Try to extract JSON object
        json_match = re.search(r'\{[^}]*\}', clean, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"[PARSE ERROR] Invalid JSON: {e}")
                return None
        
        return None

    def validate_and_fix_operation(operation):
        if not operation or "operation" not in operation:
            return None, "Missing 'operation' field"
        
        # 1. Normalisation du Nom (Strict)
        original_name = operation.get("stock_name", "")
        # On capitalise uniquement la première lettre, le reste en minuscule
        stock_name = original_name.strip().capitalize() 
        operation["stock_name"] = stock_name
        
        # 2. AUTO-FIX: Remplacement de la casse dans les formules
        # Cela évite l'erreur "not defined" si l'IA mélange FrictionAdministrative et Frictionadministrative
        for field in ["inflow", "outflow"]:
            if field in operation:
                # On remplace l'ancien nom par le nouveau dans la formule
                operation[field] = re.sub(rf'\b{original_name}\b', stock_name, operation[field], flags=re.IGNORECASE)

        # 3. AUTO-FIX: Remplacement de R par le flux (gamma_param * I)
        inflow = operation.get("inflow", "")
        if re.search(r'\b0\.\d+\s*\*\s*R\b', inflow):
            print(f"[AUTO-FIX] Replacing 'R' with '(gamma_param * I)' in inflow")
            inflow = re.sub(r'\b0\.(\d+)\s*\*\s*R\b', r'0.\1 * (gamma_param * I)', inflow)
            operation["inflow"] = inflow

        # 4. AUTO-FIX: Garantie de l'Outflow
        outflow = operation.get("outflow", "")
        if stock_name.lower() not in outflow.lower():
            coeff_match = re.search(r'0\.\d+', outflow)
            coeff = coeff_match.group(0) if coeff_match else "0.1"
            operation["outflow"] = f"{coeff} * {stock_name}"
            
        return operation, None

    def apply_operation(operation):
        """
        Apply the validated operation to the engine.
        """
        try:
            if operation["operation"] == "add_stock":
                engine.add_stock(
                    stock_name=operation["stock_name"],
                    initial_value=operation["initial_value"],
                    description=operation["description"],
                    inflow=operation["inflow"],
                    outflow=operation["outflow"]
                )
                
                # Validate physics
                is_stable, msg = engine.validate_logic()
                if not is_stable:
                    return False, f"Physics validation failed: {msg}"
                
                return True, None
            
            return False, "Unknown operation type"
            
        except Exception as e:
            return False, f"Operation failed: {str(e)}"

    def get_ai_operation(prompt):
        """
        Get structured JSON operation from AI.
        """
        print(f"[OLLAMA] Requesting JSON operation...")
        
        resp = ollama.generate(model='qwen2.5-coder:7b', system=system_prompt, prompt=prompt)
        raw_text = resp['response'].strip()
        
        print(f"[OLLAMA] Raw response:\n{raw_text}\n")
        
        operation = parse_ai_response(raw_text)
        if not operation:
            print("[PARSE] Failed to extract JSON")
            return None
        
        print(f"[PARSE] Extracted operation: {json.dumps(operation, indent=2)}")
        
        # Validate and auto-fix
        fixed_op, error = validate_and_fix_operation(operation)
        if error:
            print(f"[VALIDATION] Error: {error}")
            return None
        
        print(f"[VALIDATION] ✓ Operation validated")
        return fixed_op

    try:
        # Attempt 1
        operation = get_ai_operation(f"User request: {user_req}")
        
        if not operation:
            print("[OLLAMA] First attempt failed, retrying with clarification...")
            
            # Attempt 2: More explicit
            clarification = (
                f"User request: {user_req}\n\n"
                f"Generate a JSON operation to add a new stock variable.\n"
                f"CRITICAL: Use 'gamma_param * I' for revenue flow, NOT 'R'.\n"
                f"Return ONLY valid JSON, no other text."
            )
            
            operation = get_ai_operation(clarification)
            
            if not operation:
                return jsonify({
                    "status": "error",
                    "message": "AI failed to generate valid JSON operation"
                })
        
        print(f"[OPERATION] Applying: {json.dumps(operation, indent=2)}")
        
        # Apply the operation
        success, error = apply_operation(operation)
        
        if not success:
            print(f"[ENGINE] Operation failed: {error}")
            return jsonify({"status": "error", "message": error})
        
        print(f"[ENGINE] ✓ SUCCESS")
        print(f"[ENGINE] Active stocks: {list(engine.model_state['stocks'].keys())}")
        
        return jsonify({
            "status": "success",
            "new_code": engine.formula_code,
            "operation": operation
        })
        
    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)