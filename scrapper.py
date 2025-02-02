import json
import math
import sqlite3
from datetime import datetime
# pip install selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BuscalibreScraper:
    def __init__(self, url, tracking_file="tracking.json", sqlite_db="books.db"):
        # setup
        self.url = url
        self.tracking_file = tracking_file
        # date
        self.now = datetime.today()
        self.today = self.now.strftime("%d-%m-%Y")
        # drive
        self.driver = self._init_driver()
        # json tracking
        self.register = self._load_tracking_file()
        # sqlite tracking
        self.sqlite_db = sqlite_db
        self._init_sqlite()

    # start selenium
    def _init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless') # no GUI
        return webdriver.Chrome(options=chrome_options)
    
    def _init_sqlite(self):
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            print("SQLite database connected.")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dates (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(120) NOT NULL,
                url VARCHAR(255) NOT NULL UNIQUE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                price_now INT,
                normal_price INT NOT NULL,
                discount INT,
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (date_id) REFERENCES dates (id)
                );
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error connecting to the database:", e)

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
            name_list = self.driver.find_element(By.CSS_SELECTOR, '.nombreLista').text
            print(f"Wishlist \"{name_list}\" found...")
            # get the quantity of books
            books_quantity = len(self.driver.find_elements(By.CLASS_NAME, 'contenedorProducto'))
            print(f"Found {books_quantity} books.")
            # call methods to proceeed
            self._process_books(books_quantity)
            self._save_tracking_file()
            
        except Exception as e:
            print("Oops. There was an error... Did you use a wishlist url?")
        finally:
            self.driver.quit()

    def _process_books(self, books_quantity):
        for i in range(books_quantity):
            
			# get the link to the book
            book_url = self.driver.find_elements(By.CSS_SELECTOR, '.infoProducto .titulo a')[i].get_attribute('href')
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
                
            discount = math.ceil(100 - (100 / (normal_price / price_now))) # Calculate the discount (this might not be as accurate as expected compared to the website, but it’s a good approximation—almost 99% close to the website).
            
			# create a dictionary with the book data
            book = {
                "title": title,
				"priceNow": price_now,
				"normalPrice": normal_price,
				"discount": discount,
				"url": book_url
			}
            # update the register
            self._update_register(book)
            self._insert_into_sqlite(book)

    def _insert_into_sqlite(self, book):
        try:
            conn = sqlite3.connect(self.sqlite_db)
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign keys
            cursor = conn.cursor()

            # Check if today's date is already in the database
            cursor.execute("INSERT OR IGNORE INTO dates (date) VALUES (?)", (self.today,))
            cursor.execute("SELECT id FROM dates WHERE date = ?", (self.today,))
            date_id = cursor.fetchone()[0]  # get today's ID

            # Check if the book is already in the database
            cursor.execute("SELECT id FROM books WHERE url = ?", (book["url"],))
            book_result = cursor.fetchone()
            
            if book_result:
                book_id = book_result[0]  # Get the book's ID
            else:
                # Insert new book
                cursor.execute("INSERT INTO books (title, url) VALUES (?, ?)", (book["title"], book["url"]))
                book_id = cursor.lastrowid
                print(f"New book inserted: {book['title']}")

            # Check if the price of the book is already in the database
            cursor.execute("""
                SELECT id FROM prices
                WHERE date_id = ? AND book_id = ?
            """, (date_id, book_id))
            price_result = cursor.fetchone()

            if price_result:
                pass # The price is already in the database
            else:
                # Insert price of the book
                cursor.execute("""
                    INSERT INTO prices (date_id, book_id, price_now, normal_price, discount)
                    VALUES (?, ?, ?, ?, ?)
                """, (date_id, book_id, book["priceNow"], book["normalPrice"], book["discount"]))


            # Confirmar los cambios
            conn.commit()
        except Exception as e:
            print("SQLITE: Error uploading the books to the database", e)
        finally:
            conn.close()

    def _update_register(self, book):
        # if the date is already in the register..    
        if self.today in self.register:
            # check if the book is not already in the register
            if book not in self.register[self.today]:
                # so we add it
                self.register[self.today].append(book)
        # if not, we create a new key with the book
        else:
            self.register[self.today] = [book]

    def _save_tracking_file(self):
        with open(self.tracking_file, "w") as file:
            json.dump(self.register, file, ensure_ascii=False, indent=2)
            print(f"{self.tracking_file}: Data has been registered in the tracking.")

if __name__ == "__main__":
    url = "https://www.buscalibre.cl/v2/cosmere_1647219_l.html"
    scraper = BuscalibreScraper(url)
    scraper.scrape()