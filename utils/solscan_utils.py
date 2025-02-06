import os
import time
import pandas as pd
from selenium import webdriver
from io import StringIO

def get_transfers(driver: webdriver.Chrome, tmpdirname, wallet_address, address_type, activity_type=None, time_range=None):
    url = f"https://api-v2.solscan.io/v2/{address_type}/transfer/export?address={wallet_address}"

    if(activity_type):
        url += f"&activity_type[]={activity_type}"
    
    if(time_range):
        url += f"&block_time[]={time_range[0]}&block_time[]={time_range[1]}"

    # Get files that are already in the directory
    files = os.listdir(tmpdirname)

    # clear the window to avoid getting last transfer data
    driver.get("about:blank")
    driver.get(url)
    # Sometimes solscan doesn't respond with a download, but instead a CSV in the body, so we need to check for that
    
    raw_csv = driver.find_element("tag name", "body").get_attribute("innerHTML")
    if(raw_csv == ""):
        # Get the latest downloaded file comparing with the files before the download and wait for it to be downloaded
        new_files = os.listdir(tmpdirname)
        downloaded_file = list(set(new_files) - set(files))[0]
        
        # Wait for the file to be downloaded and check if it's a CSV file (sometimes it could be a .crdownload file)
        while downloaded_file is None or downloaded_file.split(".")[-1] != "csv":
            new_files = os.listdir(tmpdirname)
            downloaded_file = list(set(new_files) - set(files))[0]
            # time.sleep(0.1)

        # Check if file is still being downloaded or corrupted
        while True:
            try:
                # Read the downloaded file
                df = pd.read_csv(f"{tmpdirname}/{downloaded_file}")
                break
            except Exception as e:
                print(e)
                time.sleep(0.1)
                continue
    else:
        df = pd.read_csv(StringIO(raw_csv))

    return df