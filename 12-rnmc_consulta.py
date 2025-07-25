print(">>> INICIO DE CONSULTA RNMC <<<")

import sys
import time
import os
import base64
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
    driver = webdriver.Chrome(options=chrome_options)
    return driver

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

    time.sleep(1)  # Asegura carga de resultado
    html = driver.page_source
    driver.quit()
    return html

def guardar_html_y_pdf(html, cedula):
    nombre_base = f"rnmc_{cedula}"
    html_file = f"{nombre_base}.html"
    pdf_file = f"{nombre_base}.pdf"

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML guardado: {html_file}")

    try:
        pdfkit.from_file(html_file, pdf_file)
        print(f"PDF generado: {pdf_file}")
    except Exception as e:
        print("Error al generar PDF:", e)

    return html_file, pdf_file

def subir_a_drive(archivo, carpeta_id, drive):
    archivo_drive = drive.CreateFile({
        'title': os.path.basename(archivo),
        'parents': [{'id': carpeta_id}]
    })
    archivo_drive.SetContentFile(archivo)
    archivo_drive.Upload()
    print(f"Archivo subido a Drive: {archivo}")

def autenticar_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("teservimos-ocr-1c78273f15f3.json")
    drive = GoogleDrive(gauth)
    return drive

def guardar_log(html, cedula):
    with open(f"rnmc_log_{cedula}.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print("Log guardado como archivo de texto.")

if __name__ == "__main__":
    try:
        cedula = sys.argv[1]
        fecha_exp = sys.argv[2]
        carpeta_destino_id = sys.argv[3]

        print(f"== Consultando RNMC para {cedula} con fecha {fecha_exp}")
        html = consultar_rnmc(cedula, fecha_exp)

        guardar_log(html, cedula)

        html_file, pdf_file = guardar_html_y_pdf(html, cedula)

        drive = autenticar_drive()
        subir_a_drive(pdf_file, carpeta_destino_id, drive)
        subir_a_drive(html_file, carpeta_destino_id, drive)

        print("== Proceso completado exitosamente ==")

    except Exception as e:
        print("ERROR en el proceso:")
        traceback.print_exc()
