import argparse
import csv
import re
import time
from typing import Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Website Dict
WEBSITES = {"marshalls": {"main": "https://marshalls.com/",
                          "target": 'https://www.marshalls.com/us/store/shop/clearance/_/N-3951437597+0?Nr=AND%28OR%28product.catalogId%3Atjmaxx%29%2Cproduct.siteId%3Amarshalls%29&ln=11:1#/us/store/products/clearance/_/N-3951437597+0?No=0&Nr=AND%28isEarlyAccess%3Afalse%2COR%28product.catalogId%3Atjmaxx%29%2Cproduct.siteId%3Amarshalls%29&Ns=product.minListPrice%7C0%7C%7Cproduct.inventory%7C1&originalFilterState=3951437597+0&tag=va&va=true',
                          }
            }


def get_product_data(html: str, website: str) -> List[Dict]:
    """
    Extract product and price data from HTML.
    :param html: HTML to parse.
    :param website: Website name.
    :return: List of product info dictionaries.
    """
    soup = BeautifulSoup(html, 'html.parser')
    product_list = []

    # Adjust this based on actual HTML structure observed
    for product in soup.find_all('div', class_='product-details equal-height-cell'):
        name = product.find('span', class_='product-title')
        price = product.find('span', class_='product-price')
        price_comparison = product.find('span', class_='price-comparison')
        if name and price and price_comparison:
            name_text = name.text
            link = WEBSITES[website]["main"] + product.find('a', class_='product-link').get('href')
            price_text = price.text
            price_text = price_text[price_text.find("ada.newPriceLabel"):]
            price_text = price_text[price_text.find("$") + 1:].strip()
            price_comparison_text = price_comparison.text
            price_comparison_text = price_comparison_text[price_comparison_text.find("$") + 1:]
            price_comparison_text = price_comparison_text[:list(re.finditer(r'\d',
                                                          price_comparison_text))[-1].end()]

            product_list.append({
                'name': name_text,
                'current_price': price_text,
                'original_price': price_comparison_text,
                'link': link
            })

    return product_list


def get_product_links_selenium(website: str,
                               driver: webdriver.chrome.webdriver.WebDriver,
                               initial_sleep: int = 10,
                               scroll_sleep: int = 5) -> List[Dict]:
    """
    Function to get product details.
    :param website: Webpage URL to scrape.
    :param driver: Chromedriver.
    :param initial_sleep: Initial sleep time to avoid ads.
    :param scroll_sleep: Scroll sleep time to load page.
    :return: List of product dictionaries.
    """
    driver.get(WEBSITES[website]["target"])

    # If a pop-up appears, waiting appears to help get the underlying webpage
    time.sleep(initial_sleep)

    # Let's scroll all the way to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 0
    while True:
        # Scroll down to the bottom
        print(f"Scrolling {count}...")
        count += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page content
        time.sleep(scroll_sleep)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If the heights are the same, break the loop (we are at the bottom)
            break
        last_height = new_height

    print("Done scrolling!")

    page_source = driver.page_source
    product_list = get_product_data(page_source, website)
    product_list = sorted(product_list, key=lambda item: item["current_price"], reverse=True)

    # Close the WebDriver
    driver.quit()

    return product_list


def export_to_csv(products: List[Dict], filename: str = "products.csv") -> None:
    """
    Export products to CSV.
    :param products: List of product price dictionaries.
    :param filename: Output filename.
    """
    # Write products to CSV
    with open(filename, 'w', newline='') as csvfile:
        # Get the fieldnames from the first dictionary
        fieldnames = products[0].keys()

        # Create a writer object and write the header and rows
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(products)  # Write data rows


def main(args: argparse.Namespace):
    # Set up Chrome options for headless browsing
    options = Options()
    options.headless = True  # Run in headless mode (no GUI)
    service = Service(args.chromedriver_path)  # Make sure to specify the correct path

    # Start the WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    # Extract products
    products = get_product_links_selenium(args.website, driver, args.initial_sleep, args.scroll_sleep)

    # Write to CSV
    export_to_csv(products, args.filename)


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument(
        "--website", choices=["marshalls"], help="Choose a website from the list.", required=True
    )
    parser.add_argument(
        "--chromedriver_path", default="/opt/homebrew/bin/chromedriver",
        help="Local path to chromedriver.", required=False
    )
    parser.add_argument(
        "--filename", default="products.csv",
        help="Output filename.", required=False
    )
    parser.add_argument(
        "--initial_sleep", default=10,
        help="Output filename.", required=False
    )
    parser.add_argument(
        "--scroll_sleep", default=5,
        help="Output filename.", required=False
    )

    main(parser.parse_args())
