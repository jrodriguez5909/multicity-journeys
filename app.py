import base64
import streamlit as st

from main_prod import *
from time import sleep
from stqdm import stqdm

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
    st.balloons()
    st.info('App is running, please wait...')

    cities_ = cities_.split(",")
    days_ = days_.split(",")

    df_perms = generate_permutations(cities=cities_, days=days_, start_city=start_city_, end_city=end_city_, start_date=start_date_, takeoff_constraint=takeoff_constraint_, landing_constraint=landing_constraint_)
    # df_scrape = scrape_permutations(executable_path, urls=df_perms['kayak_search_url'].tolist())
    df_scrape = scrape_permutations(urls=df_perms['kayak_search_url'].tolist())
    df_download = merge_dfs(df_perms, df_scrape)

    csv = df_download.to_csv()
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    linko = f'<a href="data:file/csv;base64,{b64}" download="flight_permutations.csv">Download full csv file</a>'
    st.markdown(linko, unsafe_allow_html=True)
    st.warning("⚠ Be sure to grab the URL under the **kayak_search_url** column if the quickest and/or cheapest URLs don't work!")
    st.write("""
    • All flight permutations below and available in csv format when clicking "Download full csv file" URL above:
    """)
    st.dataframe(df_download)