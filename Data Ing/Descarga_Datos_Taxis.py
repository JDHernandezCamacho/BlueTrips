from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import os
import time

driver = webdriver.Chrome()

    # URL de la página
url = 'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'
driver.get(url)

# Pausa para permitir la carga completa de la página
time.sleep(5)

# Crear la carpeta de destino si no existe
dest_folder = 'Data'
if not os.path.exists(dest_folder):
    os.makedirs(dest_folder)

try:
    year_elements = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.faq-questions'))
    )

    # Extraer los años disponibles directamente de la página
    available_years = set()
    for year_element in year_elements:
        year_text = year_element.find_element(By.TAG_NAME, 'p').text
        available_years.add(year_text)
    
    print("Años disponibles en la página:", available_years)

    for year_text in sorted(available_years, reverse=True):  # Ordenar por año de manera descendente
        print(f"Procesando el año: {year_text}")

        # Expandir el año si no está expandido
        if year_element.get_attribute('aria-expanded') == 'false':
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(year_element)).click()
            time.sleep(2)

        year_content = driver.page_source
        soup = BeautifulSoup(year_content, 'html.parser')

        year_section = soup.find('div', id=f'faq{year_text}')
        if year_section:
            links = year_section.select('a[href$=".parquet"]')

            print(f"Enlaces encontrados para el año {year_text}:")
            for link in links:
                href = link.get('href')
                text = link.get_text()
                print(f"  Enlace encontrado: {href} - Texto: {text}")

                if href and "Green Taxi Trip Records" in text:
                    file_name = os.path.join(dest_folder, os.path.basename(href))

                    # Verificar si el archivo ya existe
                    if not os.path.exists(file_name):
                        file_url = href if href.startswith('http') else f'{url}{href}'
                        response = requests.get(file_url)
                        if response.status_code == 200:
                            with open(file_name, 'wb') as file:
                                file.write(response.content)
                            print(f'Descargado: {file_name}')
                        else:
                            print(f'Error al descargar el archivo: {file_url}')
                    else:
                        print(f'El archivo {file_name} ya existe. Saltando descarga.')
except Exception as e:
    print(f"Error: {e}")

# Cerrar el navegador
driver.quit()
