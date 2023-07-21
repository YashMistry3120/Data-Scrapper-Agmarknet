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
import pandas as pd

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

import openpyxl
from bs4 import BeautifulSoup

def extract_data_from_html_in_excel(file_path, sheet_name, cell_address, commodity):
    # Load the Excel file and read the content from the specified cell
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook[sheet_name]
    html_content = sheet[cell_address].value

    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr')[1:]  # Skip the first row, which contains header information

    data = {
        "State Name": [],
        "District Name": [],
        "Market Name": [],
        "Variety": [],
        "Group": [],
        "Arrivals (Tonnes)": [],
        "Min Price (Rs./Quintal)": [],
        "Max Price (Rs./Quintal)": [],
        "Modal Price (Rs./Quintal)": [],
        "Reported Date": [],
        "commodity": []
    }

    for row in rows:
        columns = row.find_all('td')
        if len(columns) == 10:
            data["State Name"].append(columns[0].text.strip())
            data["District Name"].append(columns[1].text.strip())
            data["Market Name"].append(columns[2].text.strip())
            data["Variety"].append(columns[3].text.strip())
            data["Group"].append(columns[4].text.strip())
            data["Arrivals (Tonnes)"].append(int(columns[5].text.strip()))
            data["Min Price (Rs./Quintal)"].append(int(columns[6].text.strip()))
            data["Max Price (Rs./Quintal)"].append(int(columns[7].text.strip()))
            data["Modal Price (Rs./Quintal)"].append(int(columns[8].text.strip()))
            data["Reported Date"].append(columns[9].text.strip())
            data["commodity"].append(commodity)

    return data

def save_data_as_csv(data, output_file):
    df = pd.DataFrame(data)
    df['Arrivals (Tonnes)'] = df['Arrival'].apply(remove_commas)
    df.to_csv(output_file, index=False)

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
            driver.find_element(By.XPATH,'//*[@id="cphBody_ButtonExcel"]').click()
            time.sleep(10)
            
            download_path = "/home/yash/Downloads/Agmarknet_Price_And_Arrival_Report.xls"
            sheet_name = 'Sheet1'
            cell_address = 'C2'
            
            output_data = extract_data_from_html_in_excel(download_path, sheet_name, cell_address, commodity)

            # Save data as CSV
            output_csv_file = 'agg_data.csv'
            save_data_as_csv(output_data, output_csv_file)


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
