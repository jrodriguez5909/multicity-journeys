## Import packages
import itertools
import pandas as pd
import numpy as np
import datetime
import json
import streamlit as st

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeType
from datetime import datetime
from time import sleep
from random import randint
from stqdm import stqdm
# from tqdm import tqdm


##########################
##########################
## User inputs
executable_path = '/Users/junerodriguez/Downloads/chromedriver_mac_arm64/chromedriver'

# List the cities you want to travel to and from, how long you'd like to stay in each, and the appropriate start/end dates
start_city = 'Amsterdam'
end_city = 'Amsterdam'
start_date = '2023-02-14'

cities = ['Warsaw', 'Sofia', 'Milan', 'Belgrade']
days = [3,3,2,3]

# depart_time_interval = ['1000','2000']
# arrive_time_interval = ['1000','2000']

# takeoff_constraint = '0900,2000__0900,2000__0900,2000__0900,2000__0900,2000'
# landing_constraint = '1000,2000__1000,2000__1000,2000__1000,2000__1000,1700'


##########################
##########################
## Functions

def generate_permutations(cities, days, start_city, end_city, start_date, takeoff_constraint, landing_constraint):
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
    with open("iata_codes.json") as f:
        iata = json.load(f)

    permutations = [
        (start_city,) + p + (end_city,) for p in itertools.permutations(cities)
    ]

    days = np.array([0]+days, dtype=np.float32)
    flight_dates = pd.to_datetime(start_date) + pd.to_timedelta(np.array([0] + days).cumsum(), unit="D")

    # Generate the URLs
    urls = []
    for p in permutations:
        # The pattern for each segment is
        #     START-END,nearby/yyyy-dd-dd
        mid_url = "/".join(
            [
                f"{iata[s]}-{iata[e]},nearby/{fd:%Y-%m-%d}"
                for s, e, fd in zip(p[:-1], p[1:], flight_dates)
            ]
        )

        if landing_constraint in globals() and takeoff_constraint in globals():
            urls.append(f"https://www.kayak.com/flights/{mid_url}/?sort=bestflight_a&fs=landing={landing_constraint};takeoff={takeoff_constraint}")
        else:
            urls.append(f"https://www.kayak.com/flights/{mid_url}/?sort=bestflight")

    # Generate the resulting dataframe
    return (
        pd.DataFrame(
            permutations,
            columns=["origin", *[f"city{i+1}" for i in range(len(cities))], "end"],
        )
        .merge(
            pd.DataFrame(
                flight_dates,
                index=[f"flight_dt_{i+1}" for i in range(len(flight_dates))],
            ).T,
            how="cross",
        )
        .assign(kayak_search_url=urls)
    )



# def get_driver():
#     return


def scrape_permutations(urls):
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
    now = datetime.now()
    
    print(f"Function was run at: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if minutes > 0:
        print(f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {minutes} minutes and {seconds} seconds.")
    else:
        print(f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {seconds} seconds.")
    
    dfs = []

    for url in stqdm(urls):
        try:
            requests = 0

            # options = webdriver.ChromeOptions()
            # options.add_argument('--disable-gpu')
            # options.add_argument('--headless')

            agents = ["Firefox/66.0.3","Chrome/73.0.3683.68","Edge/16.16299"]
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--user-agent=' + agents[(requests%len(agents))] + '"')
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=executable_path)

            # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
            # driver.implicitly_wait(10)
            # driver.get(url)
            # st.code(driver.page_source)

            # firefoxOptions = Options()
            # firefoxOptions.add_argument("--headless")
            # firefoxOptions.add_argument('--user-agent=' + agents[(requests % len(agents))] + '"')
            # # firefoxOptions.add_experimental_option('useAutomationExtension', False)
            # service = Service(GeckoDriverManager().install())
            # driver = webdriver.Firefox(firefox_options=firefoxOptions, executable_path=service)

            driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), chrome_options=chrome_options)

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
            try:
                quickest_price = prices_list[0] if prices_list[0] else 'Not Available'
            except (IndexError, KeyError, ValueError):
                quickest_price = 'Not Available'

            try:
                cheapest_price = prices_list[1] if prices_list[1] else 'Not Available'
            except (IndexError, KeyError, ValueError):
                cheapest_price = 'Not Available'

            try: 
                quickest_link = df_elem['Links'][0] if df_elem['Links'][0] else 'Not Available'
            except (IndexError, KeyError, ValueError):
                quickest_link = 'Not Available'

            try:
                cheapest_link = df_elem['Links'][1] if df_elem['Links'][1] else 'Not Available'
            except (IndexError, KeyError, ValueError):
                cheapest_link = 'Not Available'

            new_df = pd.DataFrame({'kayak_search_url': [url],
                                   'quickest_price': [quickest_price],
                                   'cheapest_price': [cheapest_price],
                                   'quickest_link': [quickest_link],
                                   'cheapest_link': [cheapest_link]})
            
            driver.close()

            dfs.append(new_df)

        except IndexError:
            pass

    total_df = pd.concat(dfs).reset_index(drop=True)

    return total_df


def merge_dfs(df_perm, df_scrape):
    """
    Description: Merge scraped df and permutations df
    
    Arguments:
    • df_perm: df with all permutations
    • df_scrape: df with all scraped details of permutations
    """
    merged_df = pd.merge(df_perm, df_scrape, on='kayak_search_url', how='left')

    return merged_df


##########################
##########################
## Test the functions

# get_ipython().run_cell_magic('time', '', "\ndf_perms = generate_permutations(cities, days, start_city, end_city, start_date)\ndf_scrape = scrape_permutations(executable_path=executable_path, urls=df_perms['kayak_search_url'].tolist())\ndf_merged = merge_dfs(df_perms, df_scrape)")
# df_merged.to_csv('flights_warsaw.csv', index=False)