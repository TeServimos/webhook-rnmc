import sys
import time
import traceback
import pdfkit
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

try:
    print(">>> INICIO DE CONSULTA RNMC <<<")

    # === Configurar navegador ===
    opts = Options()
    opts.add_argument("--headless")  # importante en Render
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 20)
    acts = ActionChains(driver)

    # === Ingresar a la página de la Policía ===
    driver.get("https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx")
    print("Página cargada.")

    # === Llenar el formulario ===
    Select(wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_ddlTipoDoc")))).select_by_value("55")

    campo_cedula = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_txtExpediente")))
    campo_cedula.clear()
    acts.move_to_element(campo_cedula).click().pause(0.2).send_keys(CEDULA).send_keys(Keys.TAB).perform()

    campo_fecha = wait.until(EC.element_to_be_clickable((By.ID, "txtFechaexp")))
    campo_fecha.clear()
    acts.move_to_element(campo_fecha).click().pause(0.2).send_keys(FECHA_EXP).send_keys(Keys.TAB).perform()

    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_btnConsultar2"))).click()

    print("Formulario enviado. Esperando resultados...")
    time.sleep(6)

    # === Guardar HTML ===
    html_content = driver.page_source
    html_content = html_content.replace("<head>", "<head><meta charset='UTF-8'>")
    with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    # === Convertir a PDF ===
    print("Generando PDF...")
    pdfkit.from_file(ARCHIVO_HTML, ARCHIVO_PDF, options={
        'enable-local-file-access': '',
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
        'encoding': 'utf-8'
    })

    print("PDF generado con éxito.")

    # === Subir a Google Drive ===
    print("Subiendo a Google Drive...")
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'teservimos-ocr-1c78273f15f3.json'
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': ARCHIVO_PDF,
        'parents': [FOLDER_ID]
    }
    media = MediaFileUpload(ARCHIVO_PDF, mimetype='application/pdf')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Hacer público
    file_id = file['id']
    service.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    public_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    print(f"ENLACE_PUBLICO::{public_link}")
    print(">>> CONSULTA COMPLETADA CON ÉXITO <<<")
    driver.quit()
    sys.exit(0)

except Exception as e:
    print("[ERROR] Excepción en el proceso:")
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass
    sys.exit(1)
