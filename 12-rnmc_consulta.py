import sys
import time
import os
import json
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pdfkit

def iniciar_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def consultar_rnmc(cedula, fecha_expedicion):
    url = "https://antecedentes.policia.gov.co:7005/WebJudicial/index.xhtml"
    driver = iniciar_driver()
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "formulario:documento")))

    driver.find_element(By.ID, "formulario:tipoID_label").click()
    driver.find_element(By.XPATH, "//li[contains(text(),'Cédula de Ciudadanía')]").click()
    driver.find_element(By.ID, "formulario:documento").send_keys(cedula)
    driver.find_element(By.ID, "formulario:fechaExpedicion_input").send_keys(fecha_expedicion)
    driver.find_element(By.ID, "formulario:consultar").click()
    wait.until(EC.presence_of_element_located((By.ID, "formulario:j_idt37")))
    time.sleep(1)

    html = driver.page_source
    driver.quit()
    return html

def guardar_html_y_pdf(html, cedula):
    nombre_base = f"rnmc_{cedula}"
    archivo_html = f"{nombre_base}.html"
    archivo_pdf = f"{nombre_base}.pdf"
    archivo_txt = f"rnmc_log_{cedula}.txt"

    with open(archivo_html, "w", encoding="utf-8") as f:
        f.write(html)

    with open(archivo_txt, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        pdfkit.from_file(archivo_html, archivo_pdf)
    except Exception as e:
        print(f"[ERROR] al generar PDF: {e}")
        archivo_pdf = None

    return archivo_html, archivo_pdf, archivo_txt

def autenticar_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("teservimos-ocr-1c78273f15f3.json")
    return GoogleDrive(gauth)

def subir_a_drive(archivo_local, carpeta_id, drive):
    archivo = drive.CreateFile({
        'title': os.path.basename(archivo_local),
        'parents': [{'id': carpeta_id}]
    })
    archivo.SetContentFile(archivo_local)
    archivo.Upload()
    archivo['shared'] = True
    archivo.UploadParam({'role': 'reader', 'type': 'anyone'})
    return archivo['id'], archivo['alternateLink']

if __name__ == "__main__":
    try:
        cedula = sys.argv[1]
        fecha_exp = sys.argv[2]
        carpeta_destino_id = sys.argv[3]

        print(">>> INICIO DE CONSULTA RNMC <<<")
        html = consultar_rnmc(cedula, fecha_exp)
        archivo_html, archivo_pdf, archivo_txt = guardar_html_y_pdf(html, cedula)

        drive = autenticar_drive()
        link_publico = None
        if archivo_pdf:
            id_archivo, link_publico = subir_a_drive(archivo_pdf, carpeta_destino_id, drive)

        resultado = {
            "nombre_pdf": archivo_pdf,
            "link_drive_pdf": link_publico,
            "nombre_html": archivo_html,
            "nombre_txt": archivo_txt
        }

        print("== Resultado Final ==")
        print(json.dumps(resultado))

    except Exception as e:
        print("[ERROR] Excepción en el proceso:")
        traceback.print_exc()
