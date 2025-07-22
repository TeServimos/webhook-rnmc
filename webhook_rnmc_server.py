from flask import Flask, request, jsonify
import subprocess
import traceback
import os
import re

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

        print("Ejecutando comando:", " ".join(comando))
        resultado = subprocess.run(comando, capture_output=True, text=True)

        print("\n--- Salida estándar ---")
        print(resultado.stdout)

        print("\n--- Errores (si hay) ---")
        print(resultado.stderr)

        if resultado.returncode != 0:
            raise RuntimeError("El script Python falló")

        return jsonify({"estado": "ok", "mensaje": "Script ejecutado correctamente"}), 200

    except Exception as e:
        print("Error al ejecutar:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Servidor webhook RNMC escuchando en http://127.0.0.1:5000/ejecutar_rnmc")
    app.run(port=5000)
