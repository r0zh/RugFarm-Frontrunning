import time
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import random
from datetime import datetime
import json
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configuration
INTERVAL = 45 * 60  # 45 minutes in seconds
PRICE_DROP_THRESHOLD = 0.6  # 60%


# GET TOKEN CREATION DATE

def smart_retry(api_call, max_retries=5, backoff_factor=0.5):
    retries = 0
    while retries < max_retries:
        try:
            return api_call()
        except Exception as e:
            retries += 1
            sleep_time = backoff_factor * (2 ** retries) + random.uniform(0, 0.1)
            print(f"Retrying call in {sleep_time:.2f}s due to: {e}")
            time.sleep(sleep_time)
    raise RuntimeError("Max retries exceeded")

def get_token_creation_date(token_mint_address: str) -> int:
    print(f"\033[94mGetting token creation date for \033[0m\033[1m{token_mint_address}... \033[0m")
    solana_client = Client("https://docs-demo.solana-mainnet.quiknode.pro/")

    signatures = []
    before_signature = None

    while True:
        response = smart_retry(lambda: solana_client.get_signatures_for_address(
            Pubkey.from_string(token_mint_address),
            before=before_signature
        ))

        if not response.value:
            break

        signatures.extend(response.value)
        before_signature = response.value[-1].signature

    if not signatures:
        raise ValueError("No transactions found for this token address.")

    return signatures[-1].block_time

def process_json_data(json_data):
    data_list = json_data['data']['list']
    df = pd.DataFrame(data_list)
    df.rename(columns={"time": "Time"}, inplace=True)
    df["Time"] = pd.to_numeric(df["Time"]).div(1000)
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    if 'volume' in df.columns:
        df.drop(columns=['volume'], inplace=True)
    return df

def check_price_drop(df, initial_price):
    for index, row in df.iterrows():
        if float(row['close']) <= initial_price * PRICE_DROP_THRESHOLD:
            return True, row['Time']
    return False, None


# Check if price has stopped moving with a margin of 1%
def check_price_stopped(initial_price, last_price, margin=0.1):
    return abs(last_price - initial_price) <= initial_price * margin
    

def translate_time(human_time):
    return int(time.mktime(datetime.strptime(human_time, "%m/%d/%Y %H:%M").timetuple()))

def generate_link(token_address, start, end):
    return f"https://gmgn.ai/api/v1/token_kline/sol/{token_address}?resolution=1s&from={start}&to={end}"


def get_driver():
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service('/usr/bin/chromedriver')  # Adjust path to your chromedriver
    driver = webdriver.Chrome(service=service, options=options)

    # Cloudflare bypass
    # IMPORTANT. Solve the Cloudflare challenge manually, then open a new tab with the same URL and solve the challenge again.
    # After that, the script will run without any issues. (you can close the second tab if you want)
    driver.get("https://gmgn.ai/api/v1/token_kline/sol/7xXJiyap6a389EWw7YkgBEd3VPVT9f3Hv5xEuUM7pump?resolution=1m&from=1736427240&to=1736444798")
    time.sleep(15)

    return driver

# Main script
def main(output_folder="output"):
    # get selenium driver with cloudflare bypass
    driver = get_driver()
    os.makedirs(output_folder, exist_ok=True)

    tokens_file = os.path.join(output_folder, "tokens.txt")
    processed_file = os.path.join(output_folder, "processed_tokens.txt")
    print(f"Tokens file: {tokens_file}")
    print(f"Processed file: {processed_file}")

    if not os.path.exists(tokens_file):
        open(tokens_file, "w").close()

    if not os.path.exists(processed_file):
        open(processed_file, "w").close()

    with open(processed_file, "r") as pf:
        processed_tokens = set(line.strip() for line in pf if line.strip())

    with open(tokens_file, "r") as file:
        token_addresses = [line.strip() for line in file if line.strip() and line.strip() not in processed_tokens]

    failed_tokens = []

    for token_address in token_addresses:
        token_folder = os.path.join(output_folder, "price_data")
        os.makedirs(token_folder, exist_ok=True)
        csv_file = os.path.join(token_folder, f'{token_address}.csv')

        try:
            start_time_unix = get_token_creation_date(token_address)
        except ValueError:
            start_time_human = input(f"No transactions found for {token_address}. Enter a start time (MM/DD/YYYY HH:MM): ")
            start_time_unix = translate_time(start_time_human)

        initial_price = None
        iteration = 1

        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"Existing file {csv_file} deleted for token {token_address}.")

        end_time_unix = start_time_unix + INTERVAL
        price_dropped = False
        price_stopped_moving = False
        error = False

        while not price_dropped and not price_stopped_moving:
            link = generate_link(token_address, start_time_unix, end_time_unix)

            # SELENIUM LOGIC
            driver.get("about:blank")
            driver.get(link)
            raw_json = driver.find_element("tag name", "pre").text

            try:
                json_data = json.loads(raw_json)
            except json.JSONDecodeError:
                print("Invalid JSON data. Skipping this iteration.")
                continue
            
            try:
                df = process_json_data(json_data)
            except KeyError:
                print("Invalid JSON data. Skipping this token.")
                error = True
                failed_tokens.append(token_address)
                break

            if initial_price is None:
                initial_price = float(df['close'].iloc[0])

            header = iteration == 1

            price_dropped, drop_time = check_price_drop(df, initial_price)
            price_stopped_moving = check_price_stopped(initial_price, float(df['close'].iloc[-1]))

            # Cut the data after the price drop is detected + 10 min
            if price_dropped:
                print(f"Price drop detected for {token_address}. Stopping data collection.")
                df = df[df['Time'] <= (drop_time + 60 * 10)]

            # Check if price has stopped moving
            if price_stopped_moving:
                print(f"Price has stopped moving for {token_address}. Stopping data collection.")
                break

            df.to_csv(csv_file, mode='w' if iteration == 1 else 'a', index=False, header=header)

            start_time_unix = end_time_unix
            end_time_unix = start_time_unix + INTERVAL

            print(f"Iteration {iteration} completed. Data saved to {csv_file}.")
            iteration += 1

        if error:
            print(f"\033[91mError occurred for token \033[0m\033[1m{token_address}.\033[0m\n")
        else:    
            print(f"\033[92mProcessing completed for token \033[0m\033[1m{token_address}.\033[0m\n")

        with open(processed_file, "a") as pf:
            pf.write(token_address + "\n")

        # Remove processed token from tokens.txt
        with open(tokens_file, "r") as tf:
            remaining_tokens = [line for line in tf if line.strip() != token_address]
        with open(tokens_file, "w") as tf:
            tf.writelines(remaining_tokens)

    if(len(failed_tokens) == 0):
        print("\033[92mAll tokens processed successfully.\033[0m")
    else:
        print("\033[91mFailed tokens:\033[0m")
        for token in failed_tokens:
            print(token + "\n")
    
    driver.quit()

if __name__ == "__main__":
    print("IMPORTANT. Read the comments in get_driver method before running the script.")
    folder = input("Enter rug farm name (i.e. folder name. default is 'output'): ")
    main(folder if folder else "output")
