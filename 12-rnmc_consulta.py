import sys
import time
import pdfkit
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException

# Parámetros esperados: cedula, fecha_exp, folder_id
if len(sys.argv) != 4:
    print("Uso: script.py <cedula> <fecha_exp> <folder_id>")
    sys.exit(1)

CEDULA = sys.argv[1]
FECHA_EXP = sys.argv[2]
FOLDER_ID = sys.argv[3]
ARCHIVO_PDF = f"resultado_rnmc_{CEDULA}.pdf"
ARCHIVO_HTML = f"resultado_rnmc_{CEDULA}.html"

print(">>> INICIO DE CONSULTA RNMC <<<")

# === Configurar navegador ===
opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 20)

# === Cargar la página
print("Cargando página...")
driver.get("https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx")
print("Página cargada.")

# === Seleccionar tipo de documento
select_tipo_doc = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_ddlTipoDoc")))
Select(select_tipo_doc).select_by_value("55")  # Cédula de Ciudadanía
print("Tipo de documento seleccionado.")

# Esperar a que el campo de cédula esté estable después del postback
time.sleep(1)

# === Ingresar número de cédula
for intento in range(3):
    try:
        campo_cedula = wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder3_txtExpediente")))
        campo_cedula.clear()
        campo_cedula.send_keys(CEDULA)
        print("Cédula ingresada.")
        break
    except StaleElementReferenceException:
        print("Reintentando campo cédula...")
        time.sleep(1)

# === Ingresar fecha de expedición
for intento in range(3):
    try:
        campo_fecha = wait.until(EC.element_to_be_clickable((By.ID, "txtFechaexp")))
        campo_fecha.clear()
        campo_fecha.send_keys(FECHA_EXP)
        print("Fecha de expedición ingresada.")
        break
    except StaleElementReferenceException:
        print("Reintentando campo fecha...")
        time.sleep(1)

# === Hacer clic en consultar
wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder3_btnConsultar2"))).click()
print("Consulta enviada. Esperando resultado...")
time.sleep(6)

# === Guardar HTML
html_content = driver.page_source
html_content = html_content.replace("<head>", "<head><meta charset='UTF-8'>")
with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)
print("HTML guardado.")

# === Generar PDF
try:
    pdfkit.from_file(ARCHIVO_HTML, ARCHIVO_PDF, options={
        'enable-local-file-access': '',
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
        'encoding': 'utf-8'
    })
    print("PDF generado con éxito.")
except Exception as e:
    print("Error al generar PDF:", e)
    driver.quit()
    sys.exit(1)

# === Subir a Google Drive
print("Subiendo a Google Drive...")
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

file_metadata = {
    'name': ARCHIVO_PDF,
    'parents': [FOLDER_ID]
}
media = MediaFileUpload(ARCHIVO_PDF, mimetype='application/pdf')
file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

# Hacer el archivo público
file_id = file['id']
service.permissions().create(fileId=file_id, body={'role': 'reader', 'type': 'anyone'}).execute()
public_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

print(f"ENLACE_PUBLICO::{public_link}")
print(">>> FIN DEL PROCESO RNMC <<<")
driver.quit()
