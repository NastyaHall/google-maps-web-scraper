from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd 
import argparse
from datetime import datetime

@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    amount_of_reviews: int = None
    rating: float = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize((asdict(business) for business in self.business_list), sep="_")
    def save_to_csv(self, filename):
        self.dataframe().to_csv(f'{filename}.csv', index=False)

def scroll(page):
    sidebar_selector = 'div[role="feed"]'
    page.hover('//a[@class="hfpxzc"][1]')

    while True:
        page.mouse.wheel(0, 1000) 
        page.wait_for_timeout(3000) 
        
        if page.query_selector('div.PbZDve'):
            break

def get_business(page, listing):
    business = Business()
    
    xpath_mapping = {
        'name': '//h1[contains(@class, "DUwDvf") and contains(@class, "lfPIob")]',
        'address': '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]',
        'website': '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]',
        'phone_number': '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]',
        'rating': '//div[@class="F7nice "]/span/span[@aria-hidden="true"]',
        'amount_of_reviews': '//div[@class="F7nice "]/span/span/span[@aria-label]'
    }
    
    for key, xpath in xpath_mapping.items():
        if page.locator(xpath).count() > 0:
            text = page.locator(xpath).inner_text()
            if key == 'rating':
                business.rating = float(text.replace(',', '.'))
            elif key == 'amount_of_reviews':
                business.amount_of_reviews = int(text.replace('(', '').replace(')', '').replace('\xa0', ''))
            else:
                setattr(business, key, text)
    
    return business

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto('https://www.google.com/maps', timeout=60000)

        page.locator('//input[@id="searchboxinput"]').fill(search_for)

        page.keyboard.press('Enter')
        page.wait_for_timeout(3000)

        # scroll(page)
        listings = page.locator('//a[@class="hfpxzc"]').all()
        print(len(listings))

        business_list = BusinessList()

        for listing in listings:
            listing.click()
            page.wait_for_timeout(500)
            business_list.business_list.append(get_business(page, listing))

        business_list.save_to_csv('google_maps_data')

        browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-l", "--location", type=str)

    args = parser.parse_args()

    if args.location and args.search:
        search_for = f'{args.search} {args.location}'
    else:
        search_for = 'dentist new york'
    start = datetime.now()
    main()
    end = datetime.now()
    print(end - start)
