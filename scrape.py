from typing import Dict, List
import time
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Set up Chrome options for headless browsing
options = Options()
options.headless = True  # Run in headless mode (no GUI)
service = Service('/opt/homebrew/bin/chromedriver')  # Make sure to specify the correct path

# Start the WebDriver
driver = webdriver.Chrome(service=service, options=options)


def get_product_data(html) -> List[Dict]:
    soup = BeautifulSoup(html, 'html.parser')
    product_list = []

    # Adjust this based on actual HTML structure observed
    for product in soup.find_all('div', class_='product-details equal-height-cell'):
        name = product.find('span', class_='product-title')
        price = product.find('span', class_='product-price')
        if name and price:
            try:
                name = name.text
                link = "https://marshalls.com/" + product.find('a', class_='product-link').get('href')
                price = price.text
                price = price[price.find("ada.newPriceLabel"):]
                price = price[price.find("$") + 1:].strip()

                price_comparison = product.find('span', class_='price-comparison').text
                price_comparison = price_comparison[price_comparison.find("$") + 1:]
                price_comparison = price_comparison[:list(re.finditer(r'\d', price_comparison))[-1].end()]

                product_list.append({
                    'name': name,
                    'current_price': price,
                    'original_price': price_comparison,
                    'link': link
                })
            except Exception as e:
                print(e)
                continue

    return product_list


def get_product_links_selenium(url: str, min_price_ratio: float = 4.0) -> List[Dict]:
    """
    Function to get product details.
    :param url: Webpage URL to scrape.
    :param min_price_ratio: Minimum ratio of price comparison to current sales price.
    :return: List of product dictionaries.
    """
    driver.get(url)

    # If a pop-up appears, waiting appears to help get the underlying webpage
    time.sleep(10)

    # Let's scroll all the way to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 0
    while True:
        # Scroll down to the bottom
        print(f"Scrolling {count}...")
        count += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page content
        time.sleep(5)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If the heights are the same, break the loop (we are at the bottom)
            break
        last_height = new_height

    print("Done scrolling!")

    page_source = driver.page_source
    product_list = get_product_data(page_source)

    product_list = sorted(product_list, key=lambda item: item["current_price"], reverse=True)

    return product_list


url = 'https://www.marshalls.com/us/store/shop/clearance/_/N-3951437597+0?Nr=AND%28OR%28product.catalogId%3Atjmaxx%29%2Cproduct.siteId%3Amarshalls%29&ln=11:1#/us/store/products/clearance/_/N-3951437597+0?No=0&Nr=AND%28isEarlyAccess%3Afalse%2COR%28product.catalogId%3Atjmaxx%29%2Cproduct.siteId%3Amarshalls%29&Ns=product.minListPrice%7C0%7C%7Cproduct.inventory%7C1&originalFilterState=3951437597+0&tag=va&va=true'
products = get_product_links_selenium(url, min_price_ratio=0.0)

# Write products to CSV
with open("products.csv", 'w', newline='') as csvfile:
    # Get the fieldnames from the first dictionary
    fieldnames = products[0].keys()

    # Create a writer object and write the header and rows
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()  # Write header row
    writer.writerows(products)  # Write data rows

# Close the WebDriver
driver.quit()