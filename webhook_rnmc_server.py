from flask import Flask, request, jsonify
import subprocess
import traceback
import os
import json
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

        comando = ["python", "12-rnmc_consulta.py", cedula, fecha_exp, carpeta_destino_id]
        print(f"== Ejecutando comando: {' '.join(comando)}", flush=True)

        resultado = subprocess.run(comando, capture_output=True, text=True)

        print("=== STDOUT ===", flush=True)
        print(resultado.stdout, flush=True)
        print("=== STDERR ===", flush=True)
        print(resultado.stderr, flush=True)

        # Intentar extraer JSON de la salida
        resultado_final = {}
        try:
            match = re.search(r'\{.*"link_drive_pdf".*?\}', resultado.stdout, re.DOTALL)
            if match:
                resultado_final = json.loads(match.group())
        except Exception as e:
            resultado_final = {"error_extraer_resultado": str(e)}

        return jsonify({
            "estado": "finalizado",
            "codigo_retorno": resultado.returncode,
            "mensaje": "Script ejecutado en primer plano",
            "resultado_archivos": resultado_final
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
