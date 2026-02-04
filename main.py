from flask import Flask, render_template, request, jsonify
from engine import AeroDynEngine
import datetime

app = Flask(__name__)
engine = AeroDynEngine()
audit_logs = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    params = request.json
    t, s, i, r = engine.run(params)
    return jsonify({'t': t, 's': s, 'i': i, 'r': r, 'formula': engine.formula_code})

@app.route('/llm_update', methods=['POST'])
def llm_update():
    user_req = request.json['prompt']
    # Simulation de la réponse LLM (on modifie une partie du code source)
    current_code = engine.formula_code
    new_code = current_code.replace("gamma_eff = params['gamma']", "gamma_eff = params['gamma'] * 1.2 # Boosté par IA")
    
    engine.update_logic(new_code)
    log = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "request": user_req,
        "change": "Optimisation du flux gamma_eff injectée."
    }
    audit_logs.append(log)
    return jsonify({"status": "success", "log": log})

if __name__ == '__main__':
    app.run(debug=True)