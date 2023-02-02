import itertools
import re
import pandas as pd
import numpy as np
import datetime
import time
import json

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from time import sleep, strftime
from random import randint
from tqdm import tqdm
from math import factorial


####################################
####################################
### User inputs

executable_path = '/Users/junerodriguez/Downloads/chromedriver_mac_arm64/chromedriver'

# List the cities you want to travel to and from, how long you'd like to stay in each, and the appropriate start/end dates
start_city = 'Amsterdam'
end_city = 'Amsterdam'
start_date = '2023-02-14'

cities = ['Warsaw', 'Sofia', 'Milan', 'Belgrade']
days = [3,3,2,3]

# depart_time_interval = ['1000','2000']
# arrive_time_interval = ['1000','2000']

takeoff_constraint = 'takeoff=0900,2000__0900,2000__0900,2000__0900,2000__0900,2000'
landing_constraint = 'landing=1000,2000__1000,2000__1000,2000__1000,2000__1000,1700'


####################################
####################################
### Functions

def generate_permutations(cities, days, start_city, end_city, start_date):
    """
    Description:
    Returns a df showing all possible journeys using the user-input arguments 
    
    Arguments:
    • cities: list of desired cities to travel to e.g., cities = ['Warsaw', 'Sofia', 'Belgrade', 'Milan'] 
    • days: list of days in each of the cities e.g., days = [3,2,3,2], meaning 3 days in Warsaw, 2 days in Sofia etc.
    • start_city: string of the city you're starting your journey from e.g., 'Amsterdam'
    • end_city: string of the city you're ending your journey in, probably the same as start_city e.g., 'Amsterdam'
    • start_date: string of the date the journey is starting on in 'YYYY-MM-DD' format e.g., '2023-02-15'
    """
    city_to_days = dict(zip(cities, days))
    
    permutations = list(itertools.permutations(cities))
    df = pd.DataFrame(permutations, columns=['city' + str(i) for i in range(1, len(cities) + 1)])
    df['origin'] = start_city
    df['end'] = end_city
    first_column = df.pop('origin')
    df.insert(0, 'origin', first_column)
    
    st_dt = pd.to_datetime(start_date)
    df = df.assign(flight_dt_1=st_dt)
    
    for i in range(len(cities)):
        df['flight_dt_' + str(i + 2)] = df['flight_dt_' + str(i + 1)] + df['city' + str(i + 1)].map(city_to_days).map(lambda x: pd.Timedelta(days=x))
    
    # IATA city code dictionary from iata_code.csv file in repo and create Kayak 'url' column for each permutation
    iata = {'Amsterdam': 'AMS',
            'Warsaw': 'WMI',
            'Sofia': 'SOF',
            'Belgrade': 'BEG',
            'Milan': 'MIL'}

    df['kayak_search_url'] = df.apply(lambda x: 'https://www.kayak.com/flights/' \
                         + iata[x['origin']] + '-' + iata[x['city1']] + ',nearby/' + str(x['flight_dt_1'].strftime("%Y-%m-%d")) +'/' \
                         + iata[x['city1']] + '-' + iata[x['city2']] + ',nearby/' + str(x['flight_dt_2'].strftime("%Y-%m-%d")) +'/' \
                         + iata[x['city2']] + '-' + iata[x['city3']] + ',nearby/' + str(x['flight_dt_3'].strftime("%Y-%m-%d")) +'/' \
                         + iata[x['city3']] + '-' + iata[x['city4']] + ',nearby/' + str(x['flight_dt_4'].strftime("%Y-%m-%d")) +'/' \
                         + iata[x['city4']] + '-' + iata[x['end']] + ',nearby/' + str(x['flight_dt_5'].strftime("%Y-%m-%d")) +'/' \
                         + '?sort=bestflight_a&fs=' + landing_constraint + ';' + takeoff_constraint, axis=1)
    
    return df


def scrape_permutations(executable_path, urls):
    """
    Description: 
    Scrapes prices and URLs for the quickest i.e., "best" and cheapest journey options for all permutations and returns a df 
    
    Arguments:
    • urls: this is a list made from the 'kayak_search_url' column in the df returned from the generate_permutations function 
    """
    # Grabbing best & cheapeast flight info (price and link) for one iteration
    xp_prices = """//div[@class='above-button']//a[contains(@class,'booking-link')]/span[@class='price option-text']"""
    xp_prices_2 = """//div[contains(@class, 'price-text')]"""
    xp_urls = """//div[@class='col col-best']//a[@href]"""
    xp_urls_2 = """//div[contains(@class, 'main-btn-wrap')]//a[@href]"""
    
    total_time = len(urls)*45
    minutes, seconds = divmod(total_time, 60)
    now = datetime.datetime.now()
    
    print(f"Function was run at: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if minutes > 0:
        print(f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {minutes} minutes and {seconds} seconds.")
    else:
        print(f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {seconds} seconds.")
    
    dfs = []

    for url in urls:
        try:
            requests = 0

            agents = ["Firefox/66.0.3","Chrome/73.0.3683.68","Edge/16.16299"]
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--user-agent=' + agents[(requests%len(agents))] + '"')    
            chrome_options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=executable_path)
            driver.implicitly_wait(10)
            driver.get(url)
            sleep(randint(8,10))

            ##################
            ##################
            # Get prices:
            prices = driver.find_elements_by_xpath(xp_prices)
            prices_list = [price.text.replace('$','') for price in prices if price.text != '']
            prices_list = [price.replace(',','') for price in prices_list]
            prices_list = list(map(float, prices_list))

            if not prices_list:
                prices = driver.find_elements_by_xpath(xp_prices_2)
                prices_list = [price.text.replace('$','') for price in prices if price.text != '']
                prices_list = [price.replace(',','') for price in prices_list]
                prices_list = list(map(float, prices_list))
            else:
                prices_list

            ##################
            ##################
            # Get links:        
            data = []
            elems = driver.find_elements_by_xpath(xp_urls)

            for elem in elems:
                data.append(elem.get_attribute("href"))

            if not data:
                elems = driver.find_elements_by_xpath(xp_urls_2)

                for elem in elems:
                    data.append(elem.get_attribute("href"))
            else:
                data

            df_elem = pd.DataFrame(data, columns=['Links'])

            ##################
            ##################
            # Make df and append to list: 
            new_df = pd.DataFrame({'quickest_price': [prices_list[0]],
                                   'cheapest_price': [prices_list[1]],
                                   'quickest_link': [df_elem['Links'][0]],
                                   'cheapest_link': [df_elem['Links'][1]]})

            driver.close()

            dfs.append(new_df)

        except IndexError:
            pass

    total_df = pd.concat(dfs).reset_index(drop=True)

    # convert URL list to pandas series
    series = pd.Series(urls, name='kayak_search_url')

    # concatenate the series and dataframe
    df_scrape = pd.concat([series, total_df], axis=1)

    return df_scrape


def merge_dfs(df_perm, df_scrape):
    """
    Description: Merge scraped df and permutations df
    
    Arguments:
    • df_perm: df with all permutations
    • df_scrape: df with all scraped details of permutations
    """
    merged_df = pd.merge(df_perm, df_scrape, on='kayak_search_url', how='left')

    return merged_df


####################################
####################################
### Run findings and output to csv

df_perms = generate_permutations(cities, days, start_city, end_city, start_date)
df_scrape = scrape_permutations(executable_path=executable_path, urls=df_perms['kayak_search_url'].tolist())
df_merged = merge_dfs(df_perms, df_scrape)
df_merged.to_csv('flights.csv', index=False)