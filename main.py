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
    current_code = engine.formula_code
    
    # Simulation de la logique de transformation (en prod, appeler l'API OpenAI/Gemini ici)
    # Ici on simule une modification de règle métier demandée par le CEO
    new_code = current_code.replace("0.05 * (100 - Rep)", "0.15 * (100 - Rep) # Boosté par IA")
    
    success = engine.update_logic(new_code)
    
    if success:
        return jsonify({"status": "success", "new_code": engine.formula_code})
    else:
        return jsonify({"status": "error", "message": "Échec de la reconfiguration"})
if __name__ == '__main__':
    app.run(debug=True)