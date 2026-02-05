from flask import Flask, render_template, request, jsonify
from engine import AeroDynEngine
import datetime
import ollama
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
        current_vars = list(engine.default_state.keys())
        removable_vars = [v for v in current_vars if v not in base_vars]
        
        target_var = None
        for var in removable_vars:
            if var.lower() in user_req:
                target_var = var
                break
        
        if target_var:
            print(f"[SYSTEM] Removing variable: {target_var}")
            
            try:
                lines = engine.formula_code.split('\n')
                new_lines = []
                in_return = False
                return_dict_lines = []
                skip_derivative = False
                
                for line in lines:
                    if 'return {' in line:
                        in_return = True
                        return_dict_lines.append(line)
                        continue
                    
                    if in_return:
                        return_dict_lines.append(line)
                        if '}' in line:
                            in_return = False
                            return_text = ' '.join(return_dict_lines)
                            return_text = re.sub(rf"'?{target_var}'?\s*:\s*[^,}}]+,?\s*", "", return_text)
                            return_text = re.sub(r',\s*,', ',', return_text)
                            return_text = re.sub(r',\s*}', '}', return_text)
                            return_text = re.sub(r'{\s*,', '{', return_text)
                            new_lines.append(return_text)
                            return_dict_lines = []
                        continue
                    
                    if f"{target_var} = y_dict.get('{target_var}'" in line:
                        continue
                    
                    if f"d{target_var}dt" in line and '=' in line:
                        skip_derivative = True
                    
                    if skip_derivative:
                        if line.strip() and not line.strip().startswith('#'):
                            if '=' not in line or 'd' not in line:
                                skip_derivative = False
                            else:
                                continue
                    
                    if target_var.lower() in line.lower() and line.strip().startswith('#'):
                        continue
                    
                    new_lines.append(line)
                
                new_code = '\n'.join(new_lines)
                success, error_msg = engine.update_logic(new_code)
                
                if success:
                    engine.remove_variable(target_var)
                    return jsonify({"status": "success", "new_code": new_code})
                else:
                    return jsonify({"status": "error", "message": f"Validation failed: {error_msg}"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": f"Removal failed: {str(e)}"})

    # --- GENERIC SYSTEM PROMPT ---
    system_prompt = (
        "You are a System Dynamics expert modifying a differential equation model.\n\n"
        
        f"CURRENT STOCKS: {list(engine.default_state.keys())}\n\n"
        
        "### MANDATORY STRUCTURE ###\n"
        "def deriv(y_dict, t, params):\n"
        "    # 1. EXTRACT ALL STOCKS (existing + new)\n"
        "    S = y_dict.get('S', 100)\n"
        "    I = y_dict.get('I', 1)\n"
        "    R = y_dict.get('R', 0)\n"
        "    Rep = y_dict.get('Rep', 100)\n"
        "    NewVar = y_dict.get('NewVar', 0)  # For any new variable\n"
        "    \n"
        "    # 2. EXTRACT PARAMETERS\n"
        "    N = params.get('S0', 100) + 1\n"
        "    beta = params.get('beta', 0.4)\n"
        "    gamma = params.get('gamma', 0.1)\n"
        "    \n"
        "    # 3. SYSTEM DYNAMICS\n"
        "    reputation_drag = 2.0 if Rep < 50 else 1.0\n"
        "    sigma_eff = min(params.get('sigma', 0.2) * reputation_drag, 0.95)\n"
        "    beta_eff = beta * (1 - sigma_eff)\n"
        "    \n"
        "    # 4. BASE DERIVATIVES (NEVER MODIFY)\n"
        "    dSdt = -(beta_eff * S * I) / N\n"
        "    dIdt = (beta_eff * S * I) / N - (gamma * I)\n"
        "    dRdt = gamma * I\n"
        "    dRepdt = -0.05 * beta * I + 0.1 * (100 - Rep)\n"
        "    \n"
        "    # 5. NEW VARIABLE DERIVATIVE (Stock-Flow model)\n"
        "    # ALWAYS follow this pattern:\n"
        "    # inflow = <source expression>\n"
        "    # outflow = <decay expression>\n"
        "    # dNewVardt = max(-NewVar, inflow - outflow)\n"
        "    \n"
        "    # 6. RETURN ALL STOCKS\n"
        "    return {'S': dSdt, 'I': dIdt, 'R': dRdt, 'Rep': dRepdt, 'NewVar': dNewVardt}\n\n"
        
        "### CRITICAL RULES ###\n"
        "1. STOCK-FLOW PRINCIPLE:\n"
        "   - R is accumulated revenue (STOCK)\n"
        "   - (gamma * I) is revenue per time period (FLOW)\n"
        "   - For growth from revenue: use FLOW (gamma * I), never STOCK (R)\n"
        "   - For growth from other vars: use FLOWS, not accumulated stocks\n\n"
        
        "2. EXTRACTION:\n"
        "   - ALWAYS extract new variables: NewVar = y_dict.get('NewVar', 0)\n"
        "   - Place extractions at the TOP with S, I, R, Rep\n\n"
        
        "3. POSITIVITY GUARD:\n"
        "   - ALWAYS use: dNewVardt = max(-NewVar, inflow - outflow)\n"
        "   - The guard variable MUST match the stock name exactly\n\n"
        
        "4. CONSISTENCY:\n"
        "   - Use extracted variable name throughout\n"
        "   - NEVER use y_dict['NewVar'] in calculations\n"
        "   - ALWAYS use the extracted variable: NewVar\n\n"
        
        "5. NAMING:\n"
        "   - Stock name: Capitalized (e.g., Lobbying, Sanctions, Budget)\n"
        "   - Derivative: d<Stock>dt (e.g., dLobbyingdt, dSanctionsdt)\n\n"
        
        "6. BASE DERIVATIVES:\n"
        "   - ALWAYS include all four: dSdt, dIdt, dRdt, dRepdt\n"
        "   - NEVER modify them unless user explicitly asks\n\n"
        
        "OUTPUT: Complete Python function only. Short French comments allowed.\n"
        "ONLY add variables the user explicitly requests. No extra variables."
    )

    def generic_semantic_validator(code_block, new_vars):
        """
        Generic validator that checks mathematical correctness for ANY variable.
        Returns: (is_valid, error_messages)
        """
        errors = []
        
        for var in new_vars:
            var_lower = var.lower()
            
            # UNIVERSAL CHECK 1: Variable must be extracted
            extraction_pattern = rf"{var}\s*=\s*y_dict\.get\('{var}'(?:,\s*0)?\)"
            if not re.search(extraction_pattern, code_block):
                errors.append(f"{var}: Not extracted with y_dict.get('{var}', 0)")
            
            # UNIVERSAL CHECK 2: Must have a derivative defined
            deriv_name = f"d{var}dt"
            if deriv_name not in code_block:
                errors.append(f"{var}: Missing derivative definition '{deriv_name}'")
            
            # UNIVERSAL CHECK 3: Derivative must use correct variable in positivity guard
            deriv_pattern = rf"d{var}dt\s*=\s*max\(\s*-(\w+)\s*,"
            match = re.search(deriv_pattern, code_block, re.IGNORECASE)
            if match:
                guard_var = match.group(1)
                if guard_var.lower() != var_lower:
                    errors.append(f"{var}: Positivity guard uses '{guard_var}' instead of '{var}'")
            elif f"d{var}dt" in code_block:
                # Derivative exists but doesn't use max() guard
                # Check if it's a simple assignment without positivity check
                simple_pattern = rf"d{var}dt\s*=\s*(?!max\()"
                if re.search(simple_pattern, code_block):
                    # This might be intentional (e.g., for trigger variables), so just warn
                    print(f"[WARNING] {var}: No positivity guard found (might be intentional)")
            
            # UNIVERSAL CHECK 4: Must not use y_dict['var'] or y_dict["var"] in calculations
            # Only check after the extraction line
            extraction_match = re.search(rf"{var}\s*=\s*y_dict\.get", code_block)
            if extraction_match:
                code_after_extraction = code_block[extraction_match.end():]
                if f"y_dict['{var}']" in code_after_extraction or f'y_dict["{var}"]' in code_after_extraction:
                    errors.append(f"{var}: Uses y_dict['{var}'] after extraction instead of '{var}'")
            
            # UNIVERSAL CHECK 5: Stock-Flow principle
            # Look for patterns that use accumulated stocks (R) instead of flows
            deriv_section_match = re.search(rf"(d{var}dt\s*=.*)", code_block)
            if deriv_section_match:
                deriv_section = deriv_section_match.group(1)
                # Find all inflow/outflow calculations leading to this derivative
                lines_before_deriv = code_block[:deriv_section_match.start()].split('\n')
                relevant_lines = []
                for line in reversed(lines_before_deriv[-20:]):  # Check last 20 lines
                    if 'inflow' in line.lower() or 'outflow' in line.lower() or var_lower in line.lower():
                        relevant_lines.insert(0, line)
                
                relevant_code = '\n'.join(relevant_lines) + '\n' + deriv_section
                
                # Pattern 1: Direct use of R (stock) without gamma (flow)
                # Match: 0.X * R but NOT 0.X * (gamma * I)
                if re.search(r'\b0\.\d+\s*\*\s*R\b', relevant_code) and 'gamma' not in relevant_code:
                    errors.append(f"{var}: Uses stock 'R' instead of flow '(gamma * I)'")
                
                # Pattern 2: Using Rep as a growth source (usually wrong unless it's feedback)
                # This is a softer check - only flag if it seems like the main growth term
                if re.search(r'inflow.*=.*Rep', relevant_code, re.IGNORECASE):
                    # Check if this seems to be using Rep as a revenue source
                    if not any(word in user_req for word in ['rep', 'réputation', 'image']):
                        print(f"[WARNING] {var}: Inflow uses 'Rep' - verify this is intentional")
            
            # UNIVERSAL CHECK 6: Derivative must be in return dict
            return_match = re.search(r"return\s+\{([^}]+)\}", code_block)
            if return_match:
                return_content = return_match.group(1)
                if f"'{var}':" not in return_content and f'"{var}":' not in return_content:
                    errors.append(f"{var}: Not included in return dictionary")
        
        return len(errors) == 0, errors

    def auto_repair_code(code_block):
        """Generic auto-repair that works for ANY variable"""
        try:
            # Check base derivatives
            required = ['dSdt', 'dIdt', 'dRdt', 'dRepdt']
            for deriv in required:
                if deriv not in code_block:
                    print(f"[AUTO-REPAIR] Missing base derivative: {deriv}")
                    return None, []
            
            # Find return dict variables
            return_match = re.search(r"return\s+\{([^}]+)\}", code_block, re.DOTALL)
            if not return_match:
                print("[AUTO-REPAIR] No return statement")
                return None, []
            
            returned_keys = re.findall(r"'(\w+)':", return_match.group(1))
            base_keys = ['S', 'I', 'R', 'Rep']
            
            # FIX 1: Normalize all variable names
            key_mapping = {}
            for key in returned_keys:
                if key not in base_keys:
                    original_key = key
                    
                    # Fix lowercase derivative names: 'dlobbyingt' -> 'Lobbying'
                    if key.startswith('d') and (key.endswith('dt') or key.endswith('t')):
                        stock_name = key.lstrip('d').rstrip('dt').rstrip('t')
                        stock_name = stock_name.capitalize()
                        if stock_name != original_key:
                            print(f"[AUTO-REPAIR] Fixing derivative name: {original_key} -> {stock_name}")
                            key_mapping[original_key] = stock_name
                            code_block = code_block.replace(f"'{original_key}':", f"'{stock_name}':")
                    # Fix 'New' prefix: 'NewLobbying' -> 'Lobbying'
                    elif key.startswith('New') and len(key) > 3:
                        stock_name = key[3:]  # Remove 'New'
                        print(f"[AUTO-REPAIR] Removing 'New' prefix: {original_key} -> {stock_name}")
                        key_mapping[original_key] = stock_name
                        code_block = code_block.replace(f"'{original_key}':", f"'{stock_name}':")
                    # Fix lowercase: 'lobbying' -> 'Lobbying'
                    elif key.islower() and len(key) > 1:
                        stock_name = key.capitalize()
                        print(f"[AUTO-REPAIR] Capitalizing: {original_key} -> {stock_name}")
                        key_mapping[original_key] = stock_name
                        code_block = code_block.replace(f"'{original_key}':", f"'{stock_name}':")
            
            # Build new_vars list
            new_vars = []
            for key in returned_keys:
                if key in key_mapping:
                    new_vars.append(key_mapping[key])
                elif key not in base_keys:
                    new_vars.append(key)
            
            # FIX 2: Add missing extractions
            lines = code_block.split('\n')
            extraction_section = []
            for line in lines:
                if 'params.get' in line or 'N =' in line:
                    break
                extraction_section.append(line)
            
            extraction_text = '\n'.join(extraction_section)
            
            missing = []
            for var in new_vars:
                if f"{var} = y_dict.get('{var}'" not in extraction_text:
                    missing.append(var)
            
            if missing:
                print(f"[AUTO-REPAIR] Adding missing extractions: {missing}")
                for idx, line in enumerate(lines):
                    if "Rep = y_dict.get('Rep'" in line:
                        for var in missing:
                            lines.insert(idx + 1, f"    {var} = y_dict.get('{var}', 0)")
                        break
                code_block = '\n'.join(lines)
            
            # FIX 3: Replace y_dict['Var'] with extracted variable
            for var in new_vars:
                # Replace all forms of y_dict access
                code_block = re.sub(rf"y_dict\['{var}'\]", var, code_block)
                code_block = re.sub(rf'y_dict\["{var}"\]', var, code_block)
                # Also replace y_dict.get() calls (except the extraction line)
                # This is tricky - we need to skip the extraction line
                lines = code_block.split('\n')
                for idx, line in enumerate(lines):
                    if f"{var} = y_dict.get('{var}'" not in line:
                        lines[idx] = re.sub(rf"y_dict\.get\('{var}'(?:,\s*0)?\)", var, line)
                code_block = '\n'.join(lines)
            
            # FIX 4: Fix positivity guards
            for var in new_vars:
                # Find derivative with wrong guard variable
                deriv_pattern = rf"(d{var}dt\s*=\s*max\(\s*-)(\w+)(\s*,)"
                match = re.search(deriv_pattern, code_block, re.IGNORECASE)
                if match:
                    wrong_var = match.group(2)
                    if wrong_var.lower() != var.lower():
                        print(f"[AUTO-REPAIR] Fixing positivity guard: max(-{wrong_var},...) -> max(-{var},...)")
                        code_block = re.sub(
                            deriv_pattern,
                            rf"\1{var}\3",
                            code_block,
                            flags=re.IGNORECASE
                        )
            
            # FIX 5: Fix stock-vs-flow issues (generic)
            # Pattern: inflow = 0.X * R (should be 0.X * (gamma * I))
            # Only fix if 'gamma' is not already present in the expression
            for var in new_vars:
                # Find inflow variables related to this derivative
                inflow_pattern = r'(\w*inflow\w*)\s*=\s*(0\.\d+)\s*\*\s*R\b'
                matches = re.findall(inflow_pattern, code_block)
                for inflow_var, coefficient in matches:
                    # Check if this inflow is used in the derivative for our variable
                    # Look for the derivative definition
                    deriv_context = ""
                    lines = code_block.split('\n')
                    for idx, line in enumerate(lines):
                        if f"d{var}dt" in line:
                            # Get surrounding context (5 lines before)
                            start = max(0, idx - 5)
                            deriv_context = '\n'.join(lines[start:idx+1])
                            break
                    
                    if inflow_var in deriv_context and 'gamma' not in deriv_context:
                        print(f"[AUTO-REPAIR] Fixing stock-to-flow: {inflow_var} = {coefficient} * R -> {coefficient} * (gamma * I)")
                        code_block = re.sub(
                            rf"{inflow_var}\s*=\s*{coefficient}\s*\*\s*R\b",
                            f"{inflow_var} = {coefficient} * (gamma * I)",
                            code_block
                        )
            
            return code_block, new_vars
            
        except Exception as e:
            print(f"[AUTO-REPAIR] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, []

    def get_ai_code(prompt):
        print(f"[OLLAMA] Generating model logic...")
        
        resp = ollama.generate(model='qwen2.5-coder:7b', system=system_prompt, prompt=prompt)
        raw_text = resp['response'].strip()
        
        clean_text = raw_text.replace("```python", "").replace("```", "").strip()
        
        match = re.search(r"(def deriv\(.*?\):.*?return\s+\{[^}]+\})", clean_text, re.DOTALL)
        
        if match:
            code_block = match.group(1)
            code_block = re.sub(r"def deriv\(.*?\):", "def deriv(y_dict, t, params):", code_block)
            
            repaired, new_vars = auto_repair_code(code_block)
            
            if repaired:
                # Generic semantic validation
                is_valid, errors = generic_semantic_validator(repaired, new_vars)
                if not is_valid:
                    print("[SEMANTIC VALIDATION] Failed:")
                    for error in errors:
                        print(f"  ✗ {error}")
                    return None
                else:
                    print(f"[SEMANTIC VALIDATION] ✓ Passed for variables: {new_vars}")
                
                return repaired
            
            return None
        
        return None

    try:
        # Attempt 1
        new_code = get_ai_code(f"Current code:\n{engine.formula_code}\n\nUser request: {user_req}")
        
        if not new_code:
            print("[OLLAMA] First generation failed validation, retrying with detailed guidance...")
            
            # Attempt 2: Explicit refinement
            refinement = (
                f"The previous attempt had errors. Follow these rules STRICTLY:\n\n"
                f"1. EXTRACTION at top:\n"
                f"   NewVar = y_dict.get('NewVar', 0)\n\n"
                f"2. STOCK-FLOW principle:\n"
                f"   - Revenue FLOW: (gamma * I) ← Use this for growth\n"
                f"   - Revenue STOCK: R ← Don't use for inflow\n"
                f"   - For other flows: use rate × source, not accumulated stock\n\n"
                f"3. POSITIVITY guard:\n"
                f"   dNewVardt = max(-NewVar, inflow - outflow)\n"
                f"   ↑ Must use extracted variable name\n\n"
                f"4. NO y_dict in calculations:\n"
                f"   Use: NewVar\n"
                f"   NOT: y_dict['NewVar']\n\n"
                f"5. NAMING:\n"
                f"   Stock: Capitalized (Lobbying, Sanctions, Budget)\n"
                f"   Derivative: d<Stock>dt\n\n"
                f"Current working code:\n{engine.formula_code}\n\n"
                f"User request: {user_req}\n\n"
                f"Generate the COMPLETE function following the template."
            )
            
            new_code = get_ai_code(refinement)
            
            if not new_code:
                print("[OLLAMA] Both attempts failed validation")
                return jsonify({
                    "status": "error", 
                    "message": "AI failed to generate valid code after 2 attempts. Check console for validation errors."
                })
        
        print("[OLLAMA] Generated code:\n", new_code)
        
        # Engine validation
        success, error_msg = engine.update_logic(new_code)
        
        if not success:
            print(f"[ENGINE] Validation failed: {error_msg}")
            return jsonify({"status": "error", "message": f"Engine rejected code: {error_msg}"})

        print("[ENGINE] ✓ SUCCESS")
        print(f"[ENGINE] Active stocks: {list(engine.default_state.keys())}")
        return jsonify({"status": "success", "new_code": new_code})
        
    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)