import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ====== Validar argumentos ======
if len(sys.argv) < 4:
    print("Uso: python 12-rnmc_consulta.py <cedula> <fecha_exp> <carpeta_destino_id>")
    sys.exit(1)

CEDULA = sys.argv[1]
FECHA_EXP = sys.argv[2]  # Formato DD/MM/AAAA
CARPETA_ID = sys.argv[3]

ARCHIVO_HTML = f"resultado_rnmc_{CEDULA}.html"
ARCHIVO_PDF = f"resultado_rnmc_{CEDULA}.pdf"

# ====== Automatizar Navegación en Sitio Web ======
URL = "https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx"

opts = Options()
opts.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 20)
acts = ActionChains(driver)

driver.get(URL)

# 1. Tipo de documento
combo = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_ddlTipoDoc")))
Select(combo).select_by_value("55")  # Cédula de Ciudadanía

# 2. Número de cédula
campo_cedula = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_txtExpediente")))
campo_cedula.clear()
acts.move_to_element(campo_cedula).click().pause(0.2).send_keys(CEDULA).send_keys(Keys.TAB).perform()

# 3. Fecha de expedición
campo_fecha = wait.until(EC.element_to_be_clickable((By.ID, "txtFechaexp")))
campo_fecha.clear()
acts.move_to_element(campo_fecha).click().pause(0.2).send_keys(FECHA_EXP).send_keys(Keys.TAB).perform()

# 4. Clic en lupa
btn = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_btnConsultar2")))
btn.click()
time.sleep(6)

# 5. Guardar HTML
with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
    f.write(driver.page_source)

# ====== Generar PDF usando Chrome Headless ======
try:
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--print-to-pdf=' + os.path.abspath(ARCHIVO_PDF))

    driver.quit()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("file://" + os.path.abspath(ARCHIVO_HTML))
    time.sleep(5)

    print("PDF generado usando Chrome Headless:", ARCHIVO_PDF)
except Exception as e:
    print("Error al generar PDF con Chrome Headless:", e)
    sys.exit(1)

# ====== Subir a Google Drive ======
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SERVICE_ACCOUNT_FILE = "credentials.json"

try:
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': ARCHIVO_PDF,
        'parents': [CARPETA_ID]
    }
    media = MediaFileUpload(ARCHIVO_PDF, mimetype='application/pdf')
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"Archivo subido con ID: {uploaded_file['id']}")
except Exception as e:
    print(f"Error al subir el archivo a Drive: {e}")
    sys.exit(1)
