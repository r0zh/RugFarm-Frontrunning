import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from pathlib import Path

def get_html_link():
    # Get the path of the html file
    current_dir = Path(__file__).resolve().parent
    resources_dir = current_dir / "resources"
    html_file_path = os.path.join(resources_dir, "cf_bypass.html")

    # Convert it to a URL-friendly file path
    return f"file://{html_file_path}"

def get_driver(tmpdirname=None):
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    if(tmpdirname):
        options.add_experimental_option("prefs", {
            "download.default_directory": tmpdirname,
            "download.prompt_for_download": False,
        })

    service = Service('/usr/bin/chromedriver')  # Adjust path to your chromedriver
    driver = webdriver.Chrome(service=service, options=options)

    # !!! Cloudflare bypass !!!
    # You will see two links, one for solscan and one for gmgn. Open the ones which you need and solve the captcha if asked to.
    # After that, the script will run without any issues. (you can close the other tabs if you want)
    
    file_url = get_html_link()
    driver.get(file_url)
    
    click_tracker = driver.find_element(By.ID, "clickTracker")
    
    value = click_tracker.get_attribute("value")
    while value != "clicked":
        value = click_tracker.get_attribute("value")
        time.sleep(0.5)  # Poll every 500ms

    return driver