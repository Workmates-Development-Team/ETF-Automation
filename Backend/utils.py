import requests
import pandas as pd
from io import StringIO
from config import logger, CLIENT_ID, ACCESS_TOKEN
from models import Session, ExecutionHistory
from datetime import datetime
from config import IST
from dhanhq import dhanhq

# Initialize Dhan client
dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# def get_security_details(symbol, exchange="NSE"):
#     try:
#         logger.info(f"🔍 Fetching SECURITY_ID for '{symbol}' on exchange '{exchange}'...")
#         url = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
#         response = requests.get(url, verify=False)
#         df = pd.read_csv(StringIO(response.text))
#         df.columns = df.columns.str.strip()
#         required_columns = ["UNDERLYING_SYMBOL", "SECURITY_ID", "EXCH_ID"]
#         for col in required_columns:
#             if col not in df.columns:
#                 raise KeyError(f"Required column '{col}' not found.")
#         df["UNDERLYING_SYMBOL"] = df["UNDERLYING_SYMBOL"].astype(str).str.strip()
#         df["EXCH_ID"] = df["EXCH_ID"].astype(str).str.strip()
#         match = df[(df["UNDERLYING_SYMBOL"] == symbol) & (df["EXCH_ID"] == exchange)]
#         if not match.empty:
#             security_id = match.iloc[0]["SECURITY_ID"]
#             logger.info(f"✅ Found SECURITY_ID for {symbol} on {exchange}: {security_id}")
#             return int(security_id)
#         else:
#             raise ValueError(f"❌ Symbol '{symbol}' not found in Dhan CSV for exchange {exchange}.")
#     except Exception as e:
#         logger.error(f"❌ Error in get_security_details: {e}", exc_info=True)
#         return None
def get_security_details(symbol, exchange="NSE"):
    try:
        logger.info(f"🔍 Fetching SECURITY_ID and SYMBOL_NAME for '{symbol}' on exchange '{exchange}'...")
        url = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
        response = requests.get(url, verify=False)
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        required_columns = ["UNDERLYING_SYMBOL", "SECURITY_ID", "EXCH_ID", "SYMBOL_NAME"]
        for col in required_columns:
            if col not in df.columns:
                raise KeyError(f"Required column '{col}' not found.")
        df["UNDERLYING_SYMBOL"] = df["UNDERLYING_SYMBOL"].astype(str).str.strip()
        df["EXCH_ID"] = df["EXCH_ID"].astype(str).str.strip()
        match = df[(df["UNDERLYING_SYMBOL"] == symbol) & (df["EXCH_ID"] == exchange)]
        if not match.empty:
            security_id = match.iloc[0]["SECURITY_ID"]
            symbol_name = match.iloc[0]["SYMBOL_NAME"]
            logger.info(f"✅ Found SECURITY_ID: {security_id} and SYMBOL_NAME: {symbol_name} for {symbol} on {exchange}")
            return int(security_id), symbol_name
        else:
            raise ValueError(f"❌ Symbol '{symbol}' not found in Dhan CSV for exchange {exchange}.")
    except Exception as e:
        logger.error(f"❌ Error in get_security_details: {e}", exc_info=True)
        return None, None
def get_ltp(security_id):
    try:
        # Handle case where security_id is a tuple (e.g., from get_security_details)
        if isinstance(security_id, tuple):
            security_id = security_id[0]  # Take the first element (security_id)
        security_id = int(security_id)
        url = "https://api.dhan.co/v2/marketfeed/ltp"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": ACCESS_TOKEN,
            "client-id": CLIENT_ID
        }
        payload = {
            "NSE_EQ": [security_id],
            "NSE_FNO": []
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            ltp_info = data.get("data", {}).get("NSE_EQ", {}).get(str(security_id))
            if ltp_info and "last_price" in ltp_info:
                ltp = float(ltp_info["last_price"])
                logger.info(f"📈 LTP for SECURITY_ID {security_id}: ₹{ltp}")
                return ltp
            else:
                logger.warning(f"⚠️ 'last_price' not found in response: {data}")
        else:
            logger.error(f"❌ Failed to fetch LTP. Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Exception while fetching LTP: {e}", exc_info=True)
        return None

def get_balance():
    try:
        response = dhan.get_fund_limits()
        if response and response.get("status") == "success" and "data" in response:
            data = response["data"]
            available_balance = float(data.get("availableBalance", 0.0))
            withdrawable_balance = float(data.get("withdrawableBalance", 0.0))
            logger.info(f"💰 Available Balance: ₹{available_balance}")
            logger.info(f"🏦 Withdrawable Balance: ₹{withdrawable_balance}")
            return available_balance, withdrawable_balance
        else:
            logger.error(f"❌ Failed to fetch balance. Response: {response}")
            return None, None
    except Exception as e:
        logger.error(f"❌ Exception while fetching balance: {e}", exc_info=True)
        return None, None

def save_execution_to_db(schedule_id, amount, ltp, quantity, execution_timestamp, status, error_message=None):
    session = Session()
    try:
        execution = ExecutionHistory(
            schedule_id=schedule_id,
            execution_timestamp=execution_timestamp,
            amount=amount,
            status=status,
            error_message=error_message
        )
        session.add(execution)
        session.commit()
        logger.info(f"✅ Execution saved to database: Schedule ID {schedule_id}, Status {status}")
    except Exception as e:
        logger.error(f"❌ Error saving execution to database: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()