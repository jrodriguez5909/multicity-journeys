import base64
import streamlit as st

from main_prod import *
from time import sleep
from stqdm import stqdm

st.write("""# Optimize your Multi-city Journey""")
st.image("https://www.visualcapitalist.com/wp-content/uploads/2022/09/CP-Adam-Symington-Mapping-Airways-Main.png", caption="Finding the Optimal Multi-city Flight Route")
st.write("[See this app's GitHub ReadMe file for more info](%s)" % "https://github.com/jrodriguez5909/RecipeScraper#top-daily-stock-losers--trading-opportunities")
st.write("""
## **App Instructions:**
1. Populate the text box below with URLs for recipes you'd like to gather ingredient from - separate the URLs with commas e.g., https://www.hellofresh.nl/recipes/chicken-parmigiana-623c51bd7ed5c074f51bbb10, https://www.hellofresh.nl/recipes/quiche-met-broccoli-en-oude-kaas-628665b01dea7b8f5009b248
2. Click **Grab ingredient list** to kick off the web scraping and creation of the ingredient shopping list dataset.
3. Click **Download full csv file** link below if you'd like to download the ingredient shopping list dataset as a csv file.
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

st.write("""
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
    df_scrape = scrape_permutations(urls=df_perms['kayak_search_url'].tolist())
    df_download = merge_dfs(df_perms, df_scrape)

    csv = df_download.to_csv()
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    linko = f'<a href="data:file/csv;base64,{b64}" download="Ingredients_list.csv">Download full csv file</a>'
    st.markdown(linko, unsafe_allow_html=True)
    st.warning('⚠ Ingredient quantities follow serving size shown in the URL you provide so be mindful of this!')
    st.write("""
    • Ingredient shopping list below and available in csv format when clicking "Download full csv file" URL above:
    """)
    st.dataframe(df_download)

    # TODO: give user frontend status bar when scraping is happening; this could be doable using stqdm package