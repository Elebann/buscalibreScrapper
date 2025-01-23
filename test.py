import json
import math
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BuscalibreScraper:
    def __init__(self, url, tracking_file="tracking.json"):
		# setup
        self.url = url
        self.tracking_file = tracking_file
        # date
        self.now = datetime.today()
        self.today = self.now.strftime("%d-%m-%Y")
        # drive
        self.driver = self._init_driver()
        # tracking
        self.register = self._load_tracking_file()

    # start selenium
    def _init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless') # no GUI
        return webdriver.Chrome(options=chrome_options)

    def _load_tracking_file(self):
        try:
            with open(self.tracking_file, "r") as file:
                print(f"File \"{self.tracking_file}\" found.")
                return json.load(file)
            
        except FileNotFoundError:
            print("No file found. Creating a new one...")
            with open(self.tracking_file, "w") as file:
                file.write("{}") # writing an empty dict which is required
            print(f"File \"{self.tracking_file}\" created.")
            return {}

    """ Scrape the data from the website. this is the HTML params, if the website changes, this will need to be updated:
        - title: .infoProducto .titulo
        - priceNow: .infoProducto .precioAhora
        - normalPrice: .infoProducto .precioTachado
    """
    def scrape(self):
        try:
            self.driver.get(self.url)
			# wait until the page is loaded
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            # get the quantity of books
            books_quantity = len(self.driver.find_elements(By.CLASS_NAME, 'contenedorProducto'))
            # call methods to proceeed
            self._process_books(books_quantity)
            self._save_tracking_file()
            
        except Exception as e:
            print("Scrape method: Oops. There was an error...", e)
            
        finally:
            self.driver.quit()

    def _process_books(self, books_quantity):
        for i in range(books_quantity):
            
			# the title
            title = self.driver.find_elements(By.CSS_SELECTOR, '.infoProducto .titulo')[i].text
            
			# the price
            price_now = int(self.driver.find_elements
                        	(By.CSS_SELECTOR, '.infoProducto .precioAhora')
                        	[i].text.replace("$ ", "").replace(".", ""))
            
			# if there is a normal (no discount price), get it
            try:
                normal_price = int(self.driver.find_elements
                                   (By.CSS_SELECTOR, '.infoProducto .precioTachado')
                                   [i].text.replace("$ ", "").replace(".", ""))
            except:
                normal_price = price_now
            discount = math.ceil(100 - (100 / (normal_price / price_now))) # Calculate the discount (this might not be as accurate as expected compared to the website, but it’s a good approximation—almost 99% close to the website). Also, ceil is not used because that function could produce unexpected results.
            
			# create a dictionary with the book data
            book = {
                "title": title,
                "priceNow": price_now,
                "normalPrice": normal_price,
                "discount": discount
            }
            # update the register
            self._update_register(book)

    def _update_register(self, book):
        if self.today in self.register:
            if book not in self.register[self.today]:
                self.register[self.today].append(book)
                print(f"New book {book.get('title')} added to the tracker")
        else:
            self.register[self.today] = [book]

    def _save_tracking_file(self):
        with open(self.tracking_file, "w") as file:
            json.dump(self.register, file, ensure_ascii=False, indent=2)
            print("Data has been registered in the tracking.")

if __name__ == "__main__":
    url = "https://www.buscalibre.cl/v2/cosmere_1647219_l.html"
    scraper = BuscalibreScraper(url)
    scraper.scrape()