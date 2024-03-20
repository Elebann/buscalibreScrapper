#To interact with the web
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import math

# For date and tracking
from datetime import date

#todo graphics
import matplotlib.pyplot as plt


# Get date
today = date.today()
print("Today's date:", today)

#todo json file
# try:
#   file = open("tracking.json", "r")
#   print("File found.")
#   file.write(f"{today}:")
# except:
#   print("No file found. Creating a new one...")
#   file = open("tracking.json", "w")
#   file.write(f"\"{today}\":")
#   file.close()
#   print("File created.")

# Heres your Buscalibre Wishlist URL
url = "https://www.buscalibre.cl/v2/cosmere_1647219_l.html"

# Chrome UI settings for headless (Silent) mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

try:
  # Go to the URL
  driver.get(url)

  # Wait for the page to load
  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

  # Get the amount of books
  booksQuantity = driver.find_elements(By.CLASS_NAME, 'contenedorProducto').__len__()

  for i in range(booksQuantity):
    # Get the book's title, price and discount
    title = driver.find_elements(By.CSS_SELECTOR, '.infoProducto .titulo')[i].text
    priceNow = int(driver.find_elements(By.CSS_SELECTOR, '.infoProducto .precioAhora')[i].text.replace("$ ", "").replace(".", ""))
    
    # Check if the book has a discount
    try:
      normalPrice = int(driver.find_elements(By.CSS_SELECTOR, '.infoProducto .precioTachado')[i].text.replace("$ ", "").replace(".", ""))
    except:
      normalPrice = priceNow

    # Calculate the discount percentage
    discount = math.ceil(100-(100/(normalPrice/priceNow)))

    # Print the book's info
    books = {
      "title": title,
      "priceNow": priceNow,
      "normalPrice": normalPrice,
      "discount": discount
    }

    print(books)

    # Save on tracking file
    # try:
    #   file = open("tracking.json", "a")
    #   file.write(f"[{books}],")
    #   file.close()
    # except:
    #   print("Error saving the tracking file.")

except Exception as e:
  print("Oops. There was an error: " + e)
  exit()
