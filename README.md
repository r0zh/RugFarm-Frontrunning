

# TokenAnalysis

This repository contains tools for analyzing Solana tokens that have been rugpulled. It collects and processes data related to market capitalization, top holders, and wallet-to-wallet transfers.


## How to Use

### 1. Setting Up Token Address and Bitquery Credentials

Create a `.env` file with the following variables:  

```
BITQUERY_ACCESS_TOKEN=xxxxxxxxxxxxxx
MINT_ADDRESS=xxxxxxxxxxxx
```

- `BITQUERY_ACCESS_TOKEN`: Your Bitquery API access token.  
- `MINT_ADDRESS`: The Solana token mint address to analyze.

**Note**: Holders and market cap data are fetched in real-time, which may consume a significant number of Bitquery credits. I'm currently exploring alternatives to improve efficiency.

### 2. Analyzing Holders Data (Work in Progress)

Fetch top holders' data with `get_top_holders.ipynb`

### 3. Fetching Market Cap Data

Fetch market capitalization data with `get_market_cap.ipynb`

### 4. Processing Transfer Data

Transfer data can be exported for free from **Solscan**, but some filtering is required since we only need wallet-to-wallet transfers. Transfers to **Pump.fun** must be excluded.

**Steps to Export and Filter Data**:

1. Go to the **Transfers** section of the Solscan token page and export the data to CSV.  
   - Rename this file to `transfer_data.csv`.

2. Filter transfers **to Pump.fun's wallet** on Solscan and export these results to CSV.  
   - Rename this file to `transfer_data_to_delete.csv`.

3. Use the filtering script: `filter_transfers.ipynb`. This script will:
    - Compare `transfer_data.csv` and `transfer_data_to_delete.csv`.
    - Create a new file named `filtered_transfer_data.csv`, excluding all rows that appear in the second file.

# Example Analysis

The following example analysis is from the token **[DUCKEY](https://solscan.io/token/45jBd1sQWuSr2dbTBgjb168xaA6De78rLVUvQ2Zmpump)**.

![alt text](image.png)
