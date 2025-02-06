import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import pytz

def get_creation_date(driver: webdriver.Chrome, token_address):
    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        try:
            # Navigate to your target URL
            driver.get(f"https://solscan.io/token/{token_address}")
            date_element = None
            retries = 0
            # wait dynamically for the page to load
            while retries < 100:
                try:
                    # Find the parent element containing the date
                    date_element = driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div[5]/div[2]/button/div/div/div")
                    break
                except:
                    time.sleep(0.1)
                    retries += 1
                    continue

            if date_element is None:
                print("Couldn't get date element")
                driver.quit()
                raise Exception("Date element not found")

            # Extract the text content of the date element
            date_text = date_element.text

            # Remove UTC from the date text
            date_text = date_text.replace(" +UTC", "")

            # Manually adjust for UTC since %Z is not recognized by strptime as UTC
            date_obj = datetime.strptime(date_text, "%B %d, %Y %H:%M:%S")

            # Assign UTC timezone
            date_obj = date_obj.replace(tzinfo=pytz.UTC)

            # Convert to Unix timestamp
            unix_timestamp = int(date_obj.timestamp())

            print(f"Creation date for token {token_address}: {date_obj}")

            return unix_timestamp

        except Exception as e:
            print(f"Attempt {attempts + 1} failed: {e}")
            attempts += 1

    print("All attempts failed, using auxiliary method")
    return get_creation_date_aux(driver, token_address)

def get_creation_date_aux(driver: webdriver.Chrome, token_address):
    # Navigate to your target URL
    driver.get(f"https://gmgn.ai/sol/token/{token_address}")
    date_element = None
    retries = 0
    # wait dinamically for the page to load
    while retries < 100:
        try:
            # Find the parent element containing the date
            date_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/main/div[3]/div[2]/div[2]/div[2]/div[6]/div[2]/div[4]/div[4]/div[2]")
            break
        except:
            time.sleep(0.1)
            retries += 1
            continue
    
    if date_element is None:
        print("Couldn't get date element")
        driver.quit()

    # Extract the text content of the date element
    date_text = date_element.text

    # Remove UTC from the date text
    date_text = date_text.replace(" +UTC", "")

    # Manually adjust for UTC since %Z is not recognized by strptime 01/11/2025 17:37
    date_obj = datetime.strptime(date_text, "%m/%d/%Y %H:%M")

    # Assign UTC timezone
    date_obj = date_obj.replace(tzinfo=pytz.UTC)

    # Convert to Unix timestamp
    unix_timestamp = int(date_obj.timestamp())

    print(f"Creation date for token {token_address}: {date_obj}")

    return unix_timestamp