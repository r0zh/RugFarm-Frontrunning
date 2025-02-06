import os
import time
import pandas as pd
import tempfile

from utils.solscan_utils import get_transfers
from utils.cf_bypass import get_driver
from utils.token_utils import get_creation_date

ADDRESS_TYPE = "token"

# Main script
def main(rugfarm="output"):

    # get selenium driver with cloudflare bypass
    with tempfile.TemporaryDirectory() as tmpdirname:
        driver = get_driver(tmpdirname)
        rugfarm_folder = os.path.join("rugfarms", rugfarm)
        os.makedirs(rugfarm_folder, exist_ok=True)

        tokens_file = os.path.join(rugfarm_folder, "tokens.txt")
        processed_file = os.path.join(rugfarm_folder, "processed_tokens.txt")
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

        transfer_data_folder = os.path.join(rugfarm_folder, "transfer_data")
        os.makedirs(transfer_data_folder, exist_ok=True)

        for token_address in token_addresses:

            creation_date = get_creation_date(driver, token_address)

            # from now to the creation date
            time_range = (creation_date, int(time.time()))
            csv_file = os.path.join(transfer_data_folder, f'{token_address}.csv')

            df = get_transfers(driver, tmpdirname, token_address, ADDRESS_TYPE)
            transfers = pd.DataFrame()
            min_time = None

            while not df.empty and df["Time"].min() != creation_date:
                # Append the new data to the existing data
                transfers = pd.concat([transfers, df], ignore_index=True)
                if min_time == df["Time"].min():
                    min_time = df["Time"].min() -1
                    # text in color red
                    print(f"\033[91mMore than 1000 transfers in the same second. Check out if important {df["Time"].min()}\033[0m")
                else:
                    min_time = df["Time"].min()
                time_range = (time_range[0], min_time)
                df = get_transfers(driver, tmpdirname, token_address, ADDRESS_TYPE, time_range=time_range)
                print(f"Min time: {min_time} - Creation date: {creation_date}")

            print(f"Saving {transfers.shape[0]} transfers for token {token_address} to {csv_file}")
            # save the data to a csv file replacing the old one if it exists
            transfers.to_csv(csv_file, index=False)

        driver.quit()


if __name__ == "__main__":
    print("IMPORTANT. Read the comments in get_driver method before running the script.")
    rugfarm = input("Enter rug farm name (i.e. folder name. default is 'output'): ")
    main(rugfarm if rugfarm else "output")