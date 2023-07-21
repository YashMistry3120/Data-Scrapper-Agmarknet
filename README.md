# Data-Scrapper-Agmarknet
Indian Government Agriculture Dataset Scraping

Goverment Agriculture Website from where we scrape the data is: http://agmarknet.gov.in/

Part 1: Scraping the data from the website and storing it in a csv file.

- The data is scraped from the website using the BeautifulSoup library in python. The data is stored in a csv file.

Using following command in terminal to run the code:

```
python scrape_agmarket.py --commodity=onion --start_date=2020-01-01 --end_date=2021-04-12 --time_agg=monthly --states=Maharashtra,West\ Bengal
```

- The above command will scrape the data for onion commodity from 2020-01-01 to 2021-04-12 for Maharashtra and West Bengal states and store it in a csv file.

Once the data is scraped, we can use the following command to run the code for insert the data into the postgres database:

```
python postgres_insert.py
```

Note: I used Docker image of postgres to run the database. The docker image can be found here: https://hub.docker.com/_/postgres

Part 2: Write a single SQL query to return the top 5 states for 4 commodities (Potato,
Onion, Wheat, tomato) – Output should contain 20 records only

SQL Query:

```
SELECT 
    commodity,
    state_name,
    SUM(arrivals) AS Total_Arrivals_Tonnes,
    AVG(model_price) AS Avg_Modal_Price_Rs_Quintal
FROM agmarket_monthly
WHERE commodity IN ('Potato', 'Onion', 'Wheat', 'Tomato')
GROUP BY commodity, state_name
ORDER BY commodity, Total_Arrivals_Tonnes DESC
LIMIT 20;
```