from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math

#todo graphics
import matplotlib.pyplot as plt

# print(selenium.__version__)

url = "https://www.buscalibre.cl/v2/cosmere_1647219_l.html"

# Para que no se abra el navegador
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

try:
  # Ir a la lista de Buscalibre pasado por variable
  driver.get(url)

  # Esperar a que cargue la pagina
  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

  # Obtener la cantidad de libros
  cantidad = driver.find_elements(By.CLASS_NAME, 'contenedorProducto').__len__()
  # time.sleep(1)

  for i in range(cantidad):
    # Conseguimos los datos
    titulo = driver.find_elements(By.CSS_SELECTOR, '.infoProducto .titulo')[i].text
    precioAhora = int(driver.find_elements(By.CSS_SELECTOR, '.infoProducto .precioAhora')[i].text.replace("$ ", "").replace(".", ""))
    #Comprobamos si el libro está en descuento
    try:
      precioOriginal = int(driver.find_elements(By.CSS_SELECTOR, '.infoProducto .precioTachado')[i].text.replace("$ ", "").replace(".", ""))
    except:
      precioOriginal = precioAhora

    descuento = math.ceil(100-(100/(precioOriginal/precioAhora)))

    libros = {
      "titulo": titulo,
      "precioAhora": precioAhora,
      "precioOriginal": precioOriginal,
      "descuento": descuento
    }

    print(f"{libros["titulo"]}: ${libros['precioAhora']} ({libros["descuento"]}% OFF)")

except Exception as e:
  print("Ups. Hubo un problema: " + e)
  exit()
