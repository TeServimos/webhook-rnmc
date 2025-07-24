print(">>> INICIO DE CONSULTA RNMC <<<")

import sys
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from weasyprint import HTML


# ============================ #
# Función: Subir archivo a Drive
# ============================ #
def subir_a_drive(nombre_archivo_local, nombre_final_en_drive, mime_type, carpeta_destino_id):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'teservimos-ocr-1c78273f15f3.json'

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': nombre_final_en_drive,
        'parents': [carpeta_destino_id]
    }

    media = MediaFileUpload(nombre_archivo_local, mimetype=mime_type)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return file.get("id"), file.get("webViewLink")


# ============================= #
# Función: Consulta en RNMC
# ============================= #
def consultar_rnmc(cedula, fecha_expedicion, carpeta_destino_id):
    print("\n=== INICIO CONSULTA RNMC ===")
    print(f"[INFO] Cédula: {cedula}")
    print(f"[INFO] Fecha expedición: {fecha_expedicion}")
    print(f"[INFO] ID Carpeta destino: {carpeta_destino_id}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        print("[INFO] Iniciando consulta en el sitio de la Policía Nacional...")
        driver.get("https://antecedentes.policia.gov.co:7005/WebJudicial/formAntecedentes.xhtml")
        wait.until(EC.presence_of_element_located((By.ID, "formAntecedentes:numeroIdentificacion")))

        driver.find_element(By.ID, "formAntecedentes:tipoIdentificacion").send_keys("Cédula de Ciudadanía")
        driver.find_element(By.ID, "formAntecedentes:numeroIdentificacion").send_keys(cedula)
        driver.find_element(By.ID, "formAntecedentes:fechaExpedicion").send_keys(fecha_expedicion)
        driver.find_element(By.ID, "formAntecedentes:consultar").click()

        wait.until(EC.presence_of_element_located((By.ID, "formAntecedentes:j_idt39")))
        time.sleep(2)

        # Guardar HTML
        archivo_html = f"RNMC_{cedula}.html"
        with open(archivo_html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[OK] HTML guardado como: {archivo_html}")

        # Convertir a PDF
        archivo_pdf = f"RNMC_{cedula}.pdf"
        HTML(archivo_html).write_pdf(archivo_pdf)
        print(f"[OK] PDF generado como: {archivo_pdf}")

        # Verificar que exista
        if not os.path.exists(archivo_pdf):
            print(f"[ERROR] El archivo PDF '{archivo_pdf}' no fue generado.")
            return

        # Subir a Google Drive
        try:
            print("[INFO] Subiendo archivo a Google Drive...")
            id_archivo, link_publico = subir_a_drive(
                archivo_pdf,
                archivo_pdf,
                "application/pdf",
                carpeta_destino_id
            )
            print(f"[OK] Archivo subido correctamente.")
            print(f"[OK] Enlace público: {link_publico}")
        except Exception as e:
            print(f"[ERROR] Falló la subida a Google Drive: {e}")

    except Exception as e:
        print(f"[ERROR] Fallo durante la consulta RNMC: {e}")

    finally:
        driver.quit()
        print("=== FIN DEL PROCESO ===\n")


# ============================= #
# Programa principal
# ============================= #
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python 12-rnmc_consulta.py <cedula> <fecha_expedicion> <carpeta_destino_id>")
        sys.exit(1)

    cedula = sys.argv[1]
    fecha_expedicion = sys.argv[2]
    carpeta_id = sys.argv[3]

    consultar_rnmc(cedula, fecha_expedicion, carpeta_id)
