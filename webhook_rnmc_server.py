from flask import Flask, request, jsonify
import subprocess
import traceback
import os

app = Flask(__name__)

@app.route("/ejecutar_rnmc", methods=["POST"])
def ejecutar_rnmc():
    try:
        # Obtener los datos JSON del cuerpo de la solicitud
        data = request.get_json(force=True)
        print("JSON recibido:", data)

        cedula = data.get("cedula")
        fecha_exp = data.get("fecha_expedicion")
        carpeta_destino_id = data.get("carpeta_destino_id")

        # Validar datos
        if not all([cedula, fecha_exp, carpeta_destino_id]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        # Construir comando
        comando = [
            "python",
            "12-rnmc_consulta.py",
            cedula,
            fecha_exp,
            carpeta_destino_id
        ]

        # Ejecutar en segundo plano y redirigir salida a archivo de log
        with open("rnmc_log.txt", "a") as logfile:
            subprocess.Popen(comando, stdout=logfile, stderr=logfile)

        return jsonify({
            "estado": "en_proceso",
            "mensaje": "Script lanzado en segundo plano"
        }), 202

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Usar puerto 10000 por compatibilidad con Render (puedes cambiarlo si lo configuras en el entorno)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
