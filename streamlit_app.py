import base64
import itertools
import pandas as pd
import numpy as np
import datetime
import json
import os, sys
import streamlit as st

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeType
from datetime import datetime
from random import randint
from time import sleep
from stqdm import stqdm

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

def delete_selenium_log():
    if os.path.exists('selenium.log'):
        os.remove('selenium.log')


def show_selenium_log():
    if os.path.exists('selenium.log'):
        with open('selenium.log') as f:
            content = f.read()
            st.code(content)


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

    for i, day in enumerate(days):
        try:
            days[i] = float(day)
        except ValueError:
            days[i] = 0

    days = np.array([0] + days, dtype=np.float32)
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
            urls.append(
                f"https://www.kayak.com/flights/{mid_url}/?sort=bestflight_a&fs=landing={landing_constraint};takeoff={takeoff_constraint}")
        else:
            urls.append(f"https://www.kayak.com/flights/{mid_url}/?sort=bestflight")

    # Generate the resulting dataframe
    return (
        pd.DataFrame(
            permutations,
            columns=["origin", *[f"city{i + 1}" for i in range(len(cities))], "end"],
        )
        .merge(
            pd.DataFrame(
                flight_dates,
                index=[f"flight_dt_{i + 1}" for i in range(len(flight_dates))],
            ).T,
            how="cross",
        )
        .assign(kayak_search_url=urls)
    )


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

    total_time = len(urls) * 45
    minutes, seconds = divmod(total_time, 60)
    now = datetime.now()

    print(f"Function was run at: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    if minutes > 0:
        print(
            f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {minutes} minutes and {seconds} seconds.")
    else:
        print(
            f"This scraper was exectuted on {now.strftime('%Y-%m-%d %H:%M:%S')} and is estimated to finalize scraping all data in {seconds} seconds.")

    dfs = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=NetworkService")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-features=VizDisplayCompositor")

    with webdriver.Chrome(options=options, service_log_path='selenium.log') as driver:
        for url in stqdm(urls):
            try:
                requests = 0
                #
                # agents = ["Firefox/66.0.3", "Chrome/73.0.3683.68", "Edge/16.16299"]
                # chrome_options = webdriver.ChromeOptions()
                # chrome_options.add_argument('--headless')
                # chrome_options.add_argument('--user-agent=' + agents[(requests % len(agents))] + '"')
                # chrome_options.add_experimental_option('useAutomationExtension', False)
                #
                # driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(),
                #                           chrome_options=chrome_options)

                driver.implicitly_wait(10)
                driver.get(url)

                sleep(randint(8, 10))

                ##################
                ##################
                # Get prices:
                # prices = driver.find_elements_by_xpath(xp_prices)
                prices = driver.find_elements(by=By.XPATH, value=xp_prices)
                prices_list = [price.text.replace('$', '') for price in prices if price.text != '']
                prices_list = [price.replace(',', '') for price in prices_list]
                prices_list = list(map(float, prices_list))

                if not prices_list:
                    # prices = driver.find_elements_by_xpath(xp_prices_2)
                    prices = driver.find_elements(by=By.XPATH, value=xp_prices_2)
                    prices_list = [price.text.replace('$', '') for price in prices if price.text != '']
                    prices_list = [price.replace(',', '') for price in prices_list]
                    prices_list = list(map(float, prices_list))
                else:
                    prices_list

                ##################
                ##################
                # Get links:
                data = []
                # elems = driver.find_elements_by_xpath(xp_urls)
                elems = driver.find_elements(by=By.XPATH, value=xp_urls)

                for elem in elems:
                    data.append(elem.get_attribute("href"))

                if not data:
                    # elems = driver.find_elements_by_xpath(xp_urls_2)
                    elems = driver.find_elements(by=By.XPATH, value=xp_urls_2)

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




if __name__ == "__main__":
    st.write("""# Optimize your Multi-city Journey""")
    st.image("https://www.visualcapitalist.com/wp-content/uploads/2022/09/CP-Adam-Symington-Mapping-Airways-Main.png", caption="Finding the Optimal Multi-city Flight Route")
    st.write("Read this app's **[GitHub ReadMe file](https://github.com/jrodriguez5909/multicity-journeys)** and/or its **[Medium article](https://medium.com/@june.rodriguez/finding-an-optimal-flight-journey-using-selenium-b021df54f64b)** for more info")
    st.markdown("""
    ## **App Instructions:**
    1. Populate the **`Required User Inputs`** section below
    2. Populate the **`Optional User Inputs`** section below if you'd like to only see results within a certain timeframe  
    3. Click the **`Show me all possible flights!`** button to kick-off the data pull. Note each iteration takes about **50 seconds** to run so keep an eye on the status bar 
    -------
    """)

    st.write("""
    ## **Required User Inputs:**
    """)

    start_date_ = st.text_input(
                                label="""**Journey Start Date:** start date of your journey in YYYY-MM-DD format""",
                                placeholder="2023-06-01"
                                )

    start_city_ = st.text_input(
                                label="""**Starting City:** city you're starting from""",
                                placeholder="New York"
                                )

    end_city_ = st.text_input(
                              label="""**Ending City:** city you're ending in - note this is likely the same as Starting City""",
                              placeholder="New York"
                              )

    cities_ = st.text_input(
                            label="""**Destinations:** all of your desired destinations in this journey (separated by commas)""",
                            placeholder="Chicago,Atlanta,Hong Kong"
                            )

    days_ = st.text_input(
                          label="""**Days Visiting:** number of days you'll stay in each of the above destinations (separated by commas)""",
                          placeholder="3,2,7 (meaning 3 days in Chicago, 2 days in Atlanta, and 7 days in Hong Kong)"
                          )

    st.markdown("""
    -----------
    ## **Optional User Inputs:**
    """)

    takeoff_constraint_ = st.text_area(label="""**Departure Time Constraints:** desired departure times corresponding to cities above (00:00 24hr format and separated by double underscores __)""",
                                       placeholder="0900,2000__0900,2000__0900,2000\n(meaning departure time between 9:00 AM - 8:00 PM from all cities)",
                                       height=50)

    landing_constraint_ = st.text_area(label="""**Arrival Time Constraints:** desired arrival times corresponding to cities above (00:00 24hr format and separated by double underscores __)""",
                                       placeholder="1000,1900__1000,1900__1000,1900\n(meaning arrival time between 10:00 AM - 7:00 PM in all cities)",
                                       height=50)

    download = st.button('Show me all possible flights!',
                         type="primary",
                         on_click=print("Grabbing flight info for " + str(len(cities_.split(","))) + " cities based on your inputs"))

    if download:

        cities_ = cities_.split(",")
        days_ = days_.split(",")

        df_perms = generate_permutations(cities=cities_, days=days_, start_city=start_city_, end_city=end_city_, start_date=start_date_, takeoff_constraint=takeoff_constraint_, landing_constraint=landing_constraint_)
        # df_scrape = scrape_permutations(executable_path, urls=df_perms['kayak_search_url'].tolist())
        st.info('App is running, please wait...')
        df_scrape = scrape_permutations(urls=df_perms['kayak_search_url'].tolist())
        df_download = merge_dfs(df_perms, df_scrape)
        st.balloons()

        csv = df_download.to_csv()
        b64 = base64.b64encode(csv.encode()).decode()  # some strings
        linko = f'<a href="data:file/csv;base64,{b64}" download="flight_permutations.csv">Download full csv file</a>'
        st.markdown(linko, unsafe_allow_html=True)
        st.warning("⚠ Be sure to grab the URL under the **kayak_search_url** column if the quickest and/or cheapest URLs don't work!")
        st.write("""
        • All flight permutations below and available in csv format when clicking "Download full csv file" URL above:
        """)
        st.dataframe(df_download)