from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import lxml
import html5lib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
import time
from selenium.webdriver.common.by import By
import argparse
from datetime import datetime

def retry(max_attempts=3, wait_time=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, TimeoutError) as e:
                    attempts += 1
                    print(f"Attempt {attempts} failed: {e}. Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
            raise Exception("Exceeded maximum retry attempts. Check your internet connection.")
        return wrapper
    return decorator

def remove_commas(value):
    return value.replace(',', '')

from datetime import datetime, timedelta


def get_month_ranges(start_date, end_date):
    # Convert the input strings to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Initialize the result list to store the month ranges
    month_ranges = []

    # Loop through the months from start_date to end_date
    current_month = start_date
    while current_month <= end_date:
        # Calculate the last day of the current month
        last_day_of_month = current_month.replace(day=28) + timedelta(days=4)
        last_day_of_month = last_day_of_month - timedelta(days=last_day_of_month.day)

        # If the current month is February and it's a leap year, adjust the last day
        if current_month.month == 2 and current_month.year % 4 == 0 and (
                current_month.year % 100 != 0 or current_month.year % 400 == 0):
            last_day_of_month = last_day_of_month.replace(day=29)

        # If the last day of the current month is greater than the end_date, use the end_date
        if last_day_of_month > end_date:
            last_day_of_month = end_date

        # Append the current month range to the result list
        month_ranges.append((current_month.strftime("%d-%b-%Y"), last_day_of_month.strftime("%d-%b-%Y")))

        # Move to the next month
        current_month = last_day_of_month + timedelta(days=1)

    return month_ranges


@retry()
def scrape_agmarket(commodity, states, start_date, end_date, time_agg):
    # _start_date_object = datetime.strptime(start_date, "%Y-%m-%d")
    # _start_date = _start_date_object.strftime("%d-%b-%Y")

    # _end_date_object = datetime.strptime(end_date, "%Y-%m-%d")
    # _end_date = _end_date_object.strftime("%d-%b-%Y")
    month_ranges = get_month_ranges(start_date, end_date)

    _states = states.split(",")
    rows=[]
    for state in _states:
        for _start_date, _end_date in month_ranges:
            url = "https://agmarknet.gov.in/"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            s=soup.find_all('input')
            ser=Service("chromedriver.exe")
            driver=webdriver.Chrome(service=ser)
            driver.get("https://agmarknet.gov.in/")

            Select(driver.find_element("id","ddlArrivalPrice")).select_by_visible_text("Both")
            time.sleep(2)
            Select(driver.find_element("id","ddlCommodity")).select_by_visible_text(commodity)
            time.sleep(2)
            Select(driver.find_element("id","ddlState")).select_by_visible_text(state)
            time.sleep(2)
            date_from=driver.find_element(By.XPATH,'//*[@id="txtDate"]')
            date_from.clear()
            date_from.send_keys(_start_date)
            time.sleep(1)
            date_to=driver.find_element(By.XPATH,'//*[@id="txtDateTo"]')
            date_to.clear()
            date_to.send_keys(_end_date)
            driver.find_element("id","btnGo").click()
            time.sleep(10)

            
            ta=driver.find_element(By.XPATH,'//*[@id="cphBody_GridViewBoth"]')
            header=[]
            for i in ta.find_elements(By.TAG_NAME,"th"):
                header.append(i.text)

            header = header + ["commodity"]
            try:
                for j in ta.find_elements(By.TAG_NAME,"tr")[1:-5]:
                    data=[]
                    for p in (j.find_elements(By.TAG_NAME,"td")):
                        data.append(p.text)
                    data = data + [commodity]
                    if len(data) == len(header):
                        print(data)
                        rows.append(data)
                    elif len(data) == len(header)-1:
                        data = data[:5]+[rows[-1][5]]+data[5:]
                        print(data)
                        rows.append(data)
            except Exception as e:
                print(f"Data format error occurred: {e}")
                
    # rows list to csv conversion
    df = pd.DataFrame(rows, columns=header)
    df['Arrivals (Tonnes)'] = df['Arrivals (Tonnes)'].apply(remove_commas)
    df.to_csv("agg_data.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commodity", help="Commodity name", type=str, default="Onion")
    parser.add_argument("--states", help="State name", type=str, default="Uttar Pradesh")
    parser.add_argument("--start_date", help="Start date", type=str, default="2020-01-01")
    parser.add_argument("--end_date", help="End date", type=str, default="2021-04-12")
    parser.add_argument("--time_agg", help="Time aggregation", type=str, default="monthly")

    args = parser.parse_args()
    try:
        scrape_agmarket(args.commodity, args.states, args.start_date, args.end_date, args.time_agg)
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
