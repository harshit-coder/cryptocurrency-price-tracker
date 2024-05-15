import json
from typing import List
import requests
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from decouple import config
from utils.constants import *
from utils.crypto_logger import logger

with open(CONFIG_FILE_NAME) as f:
    config_data = json.load(f)


class CoinGeckoAPI:

    def get_crypto_prices(self, cryptos: List[str]):
        try:
            coin_url = config_data.get(config(PRICE_URL_SECRET_NAME))
            target_currency = config_data.get(config(TARGET_CURRENCY_SECRET_NAME))
            params = {
                COIN_CONVERTER_PARAM_IDS: cryptos,
                COIN_CONVERTER_VS_CURRENCY_PARAM: target_currency
            }
            coin_api_headers = config_data.get(config(COIN_API_HEADERS))
            try:
                response = requests.get(coin_url, params=params, headers=coin_api_headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error fetching data from CoinGecko API: {response.status_code} with message: "
                                 f"{response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data from CoinGecko API: {e}")
            except HttpError as err:
                logger.error(f"Error fetching data from CoinGecko API: {err}")

        except Exception as e:
            logger.error(f"Error fetching data from CoinGecko API: {e}")
            return None


class GoogleSheetsLogger:
    def __init__(self, credentials):
        self.creds = credentials

    def log_crypto_prices(self, prices, service):
        try:
            if prices:
                for crypto, price_data in prices.items():
                    values = [[crypto, price_data[config_data.get(config(TARGET_CURRENCY_SECRET_NAME)).lower()], datetime.now().strftime(DATETIME_FORMAT)]]
                    body = {'values': values}
                    service.spreadsheets().values().append(
                        spreadsheetId=config_data.get(config(SPREADSHEET_ID_SECRET)), range=config_data.get(config(TARGET_CURRENCY_SECRET_NAME)),
                        valueInputOption=VALUEINPUTOPTION, body=body).execute()

        except Exception as e:
            logger.error(f"Error logging data to Google Sheets: {e}")


class CryptoPriceTracker:
    def __init__(self, api: CoinGeckoAPI, google_logger: GoogleSheetsLogger, cryptos: List[str], service: object):
        self.api = api
        self.google_logger = google_logger
        self.cryptos = cryptos
        self.service = service

    def track_prices(self):
        try:
            prices = self.api.get_crypto_prices(self.cryptos)
            if prices:
                self.google_logger.log_crypto_prices(prices, self.service)
        except Exception as e:
            logger.error(f"Error tracking prices: {e}")


def authenticate_google_sheets():
    try:
        creds = None
        scopes = config_data.get(config(GOOGLE_SCOPE_SECRET_NAME)).split(",")
        token_file = config_data.get(config(TOKEN_FILE_SECRET_NAME))
        creds_file = config_data.get(config(CRED_FILE_SECRET_NAME))
        if os.path.exists(os.path.join(GOOGLE_TOKENS_PATH, token_file)):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(GOOGLE_CREDENTIALS_PATH, creds_file), scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(os.path.join(GOOGLE_TOKENS_PATH, token_file), "w") as token:
                token.write(creds.to_json())
        return creds
    except Exception as e:
        logger.error(f"Error authenticating with Google Sheets: {e}")
        return None


def main():
    try:
        # Authenticate with Google Sheets
        credentials = authenticate_google_sheets()
        sheet_logger = GoogleSheetsLogger(credentials)
        service = build(SERVICE_NAME, GOOGLE_BUILD_VERSION, credentials=credentials)

        # Initialize CoinGeckoAPI and CryptoPriceTracker
        api = CoinGeckoAPI()
        cryptos = config_data.get(config(TRACKER_SECRET_NAME))
        tracker = CryptoPriceTracker(api, sheet_logger, cryptos, service)

        # Track cryptocurrency prices and log to Google Sheets
        tracker.track_prices()
    except HttpError as err:
        logger.error(f"Error authenticating with Google Sheets: {err}")
    except Exception as e:
        logger.error(f"Error tracking cryptocurrency prices: {e}")


if __name__ == "__main__":
    main()
