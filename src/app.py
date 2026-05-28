import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from algoritmo_genetico import ejecutar_algoritmo
from services.horario_service import guardar_horarios, limpiar_horarios_ia

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "IA Programación Académica"})


@app.route("/api/generar-horarios", methods=["POST"])
def generar_horarios():
    data = request.json
    per_id = data.get("per_id")
    car_id = data.get("car_id")
    esc_id = data.get("esc_id")

    if not per_id or not car_id or not esc_id:
        return jsonify({"error": "per_id, car_id y esc_id son obligatorios"}), 400

    try:
        resultado = ejecutar_algoritmo(per_id, car_id, esc_id)

        if "error" in resultado:
            return jsonify(resultado), 400

        return jsonify(
            {
                "message": "Horarios generados exitosamente",
                "preview": True,
                "resultado": resultado,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/confirmar-horarios", methods=["POST"])
def confirmar_horarios():
    data = request.json
    horarios = data.get("horarios")
    per_id = data.get("per_id")
    car_id = data.get("car_id")

    if not horarios or not per_id or not car_id:
        return jsonify({"error": "horarios, per_id y car_id son obligatorios"}), 400

    try:
        eliminados = limpiar_horarios_ia(per_id, car_id)
        ids = guardar_horarios(horarios)

        return jsonify(
            {
                "message": f"Horarios confirmados: {len(ids)} guardados, {eliminados} anteriores eliminados",
                "horarios_guardados": ids,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/limpiar-horarios-ia", methods=["POST"])
def limpiar_horarios():
    data = request.json
    per_id = data.get("per_id")
    car_id = data.get("car_id")

    if not per_id or not car_id:
        return jsonify({"error": "per_id y car_id son obligatorios"}), 400

    try:
        eliminados = limpiar_horarios_ia(per_id, car_id)
        return jsonify(
            {"message": f"{eliminados} horarios generados por IA eliminados"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
