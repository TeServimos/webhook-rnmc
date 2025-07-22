from flask import Flask, request, jsonify
import subprocess
import traceback
import os

app = Flask(__name__)

@app.route("/ejecutar_rnmc", methods=["POST"])
def ejecutar_rnmc():
    try:
        data = request.get_json(force=True)
        cedula = data.get("cedula")
        fecha_exp = data.get("fecha_expedicion")
        carpeta_destino_id = data.get("carpeta_destino_id")

        if not all([cedula, fecha_exp, carpeta_destino_id]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        comando = [
            "python",
            "12-rnmc_consulta.py",
            cedula,
            fecha_exp,
            carpeta_destino_id
        ]

        subprocess.Popen(comando)  # Ejecutar en segundo plano
        return jsonify({"estado": "en_proceso", "mensaje": "Script lanzado en segundo plano"}), 202

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
