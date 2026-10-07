import asyncio
import json
import aiohttp
import platform
import argparse
from datetime import date, timedelta

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="
CURRENCIES = ["EUR", "USD"]

def get_list_of_days(num: int):
    """
    Returns a list of dates in the format "dd.mm.yyyy" for the last 'num' days including today.
    """
    if num > 10 or num < 1:
        raise ValueError("Number of days must be 1-10.")
    days_list = []
    for i in range(num):
        day = date.today() - timedelta(days=i)
        days_list.append(day.strftime("%d.%m.%Y"))
    return days_list

class APIClient:

    @staticmethod
    async def fetch_raw_data(session: aiohttp.ClientSession, day: str):
        url = API_URL + day
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                else:
                    try:
                        return await response.json()
                    except json.JSONDecodeError:
                        print(f"[ERROR] APIClient: Could not decode JSON for {day}.")
                        return None
        except aiohttp.ClientConnectorError as e:
            print(f"[ERROR] APIClient: Network connection failed for {day}: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] APIClient: An unexpected error occurred for {day}: {e}")
            return None

class RateParser:

    @staticmethod
    async def parse_data(raw_data: dict, day: str):
        try:
            filtered_data = [item for item in raw_data.get("exchangeRate", []) if item.get("currency") in CURRENCIES]
            rates={}
            for item in filtered_data:
                rates[item.get("currency")] = {'sale': item.get("saleRate"), 'purchase': item.get("purchaseRate")}
            if not rates:
                return None
            return {day: rates}
        except json.JSONDecodeError as e:
            return {day: f"Data processing failed: {e}"}

        
class RateFetcher:

    @staticmethod
    async def fetch(session: aiohttp.ClientSession, day: str):
        response = await APIClient.fetch_raw_data(session, day)
        if response is None:
            return {day: "Failed to connect or received an invalid HTTP status."}
        processed_data = await RateParser.parse_data(response, day)
        if processed_data is None:
            return {day: f"no data available for {day}"}
        else:
            return processed_data
       
            
async def main(days: int = 1):
    """Main function to fetch exchange rates for the last 'days' days."""
    try:
        days_list = get_list_of_days(days)
    except ValueError as ve:
        print(f"[ERROR] {ve}")
        return
    async with aiohttp.ClientSession() as session:
            tasks = [RateFetcher.fetch(session, day) for day in days_list]
            results = await asyncio.gather(*tasks)
            print (results)
    

if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(
                    prog='PrivatBank Exchange Rate Fetcher',
                    description='Fetches exchange rates for USD and EUR from PrivatBank API for the last N days (1-10).',
                    epilog='GoIT Python course project.')
    parser.add_argument('days', type=int, nargs='?', default=1, help='Number of days to fetch exchange rates for (1-10).')
    args = parser.parse_args()
    asyncio.run(main(args.days))