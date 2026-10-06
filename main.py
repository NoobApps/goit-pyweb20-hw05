import asyncio
import aiohttp
import platform
import sys
from datetime import date, timedelta

API = "https://api.privatbank.ua/p24api/exchange_rates?date="

def get_list_of_days(num: int):
    """
    Returns a list of dates in the format "dd.mm.yyyy" for the last 'num' days including today.
    """
    if num > 10 or num < 1:
        raise ValueError("Number of days must be at interval 1-10.")
    days_list = []
    for i in range(num):
        day = date.today() - timedelta(days=i)
        days_list.append(day.strftime("%d.%m.%Y"))
    return days_list

async def main(days: int = 1):
    async with aiohttp.ClientSession() as session:
        try:
            days = get_list_of_days(days)
            tasks = [fetch_exchange_rate(session, day) for day in days]
            results = await asyncio.gather(*tasks)
            print (results)
        except Exception as e:
            print(f"{e}")

async def fetch_exchange_rate(session, day):
    url = API + day
    async with session.get(url) as response:
        data = await response.json()
        try:
            d = data.get("exchangeRate", [])
            filtered_data = list(filter(lambda x: x.get("currency") in ["EUR", "USD"], d))
            rates={}
            for item in filtered_data:
                rates[item.get("currency")] = {'sale': item.get("saleRate"), 'purchase': item.get("purchaseRate")}
            return {day: rates}
        except aiohttp.ClientConnectorError:
            return {day: "No data available for this date."}

if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1))