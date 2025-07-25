
import sys
import time
import pdfkit
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# === Validar argumentos de entrada ===
if len(sys.argv) != 4:
    print("Uso: script.py <cedula> <fecha_exp> <folder_id>")
    sys.exit(1)

CEDULA = sys.argv[1]
FECHA_EXP = sys.argv[2]
FOLDER_ID = sys.argv[3]
ARCHIVO_PDF = f"resultado_rnmc_{CEDULA}.pdf"
ARCHIVO_HTML = f"resultado_rnmc_{CEDULA}.html"

print(">>> INICIO DE CONSULTA RNMC <<<")
print("Cargando página...")

# === Automatización con Selenium ===
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 20)
acts = ActionChains(driver)

try:
    driver.get("https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx")
    print("Página cargada.")

    # Tipo de documento: Cédula de ciudadanía (valor 55)
    Select(wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_ddlTipoDoc")))).select_by_value("55")
    print("Tipo de documento seleccionado.")

    # Ingresar cédula
    campo_cedula = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_txtExpediente")))
    campo_cedula.clear()
    acts.move_to_element(campo_cedula).click().pause(0.2).send_keys(CEDULA).perform()
    print("Cédula ingresada.")

    # Ingresar fecha de expedición
    campo_fecha = wait.until(EC.element_to_be_clickable((By.ID, "txtFechaexp")))
    campo_fecha.clear()
    acts.move_to_element(campo_fecha).click().pause(0.2).send_keys(FECHA_EXP).perform()
    print("Fecha de expedición ingresada.")

    # Enviar formulario
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_btnConsultar2"))).click()
    print("Consulta enviada. Esperando resultado...")
    time.sleep(6)

    # === Capturar HTML ===
    html_content = driver.page_source
    html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<link.*?>', '', html_content)
    html_content = f"""<html><head><meta charset='UTF-8'>
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 12px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ border: 1px solid #ddd; padding: 8px; }}
    </style></head><body>{html_content}</body></html>"""

    with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML guardado.")

    # === Generar PDF ===
    try:
        pdfkit.from_file(ARCHIVO_HTML, ARCHIVO_PDF, options={
            'enable-local-file-access': '',
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'encoding': 'utf-8',
            'quiet': ''
        })
        print("PDF generado correctamente.")
    except Exception as e:
        print("Error al generar PDF:", e)
        sys.exit(1)

    # === Subir a Google Drive ===
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'credentials.json'  # Ajustar si el nombre es distinto
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': ARCHIVO_PDF, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(ARCHIVO_PDF, mimetype='application/pdf')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    # Hacer público
    service.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    public_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    print(f"ENLACE_PUBLICO::{public_link}")

except Exception as e:
    print("[ERROR] Excepción en el proceso:")
    print(e)
    sys.exit(1)
finally:
    driver.quit()
