'''
Name: Jacob Carvalho
CS602: SN1.SUI21 Mondays 6:00:9:30
Data: California Fires
URL:

Description:
This program uses Streamlit to create a web-like page that navigates between 4 different pages related to
California Wildfire data. The pages include a map of the California wildfires based on a year that the user
selects, a top charts page that shows the top 10 fires by acreage burned, and a most dangerous page to show the
data of the most dangerous fires based on county.
'''

import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk
import matplotlib as mpl
import matplotlib.pyplot as plt
import emoji
from PIL import Image


def year_list():  # Getting a list of the years in the data set
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['ArchiveYear', 'Latitude', 'Longitude', 'MajorIncident'])
    yes_year = []
    for year in df['ArchiveYear']:
        if year not in yes_year:
            yes_year.append(year)
    return yes_year


def county_list():  # Getting a list of the years in the data set
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['Counties'])
    df.drop_duplicates(inplace=True)  # Remove any duplicate county names to create single list
    df.sort_values(by='Counties', ascending=True, inplace=True)
    return df


def o(numb):  # Creating ordinal numbers function
    if numb < 20:  # determining suffix for < 20
        if numb == 1:
            suffix = 'st'
        elif numb == 2:
            suffix = 'nd'
        elif numb == 3:
            suffix = 'rd'
        else:
            suffix = 'th'
    else:   # determining suffix for > 20
        tens = str(numb)
        tens = tens[-2]
        unit = str(numb)
        unit = unit[-1]
        if tens == "1":
           suffix = "th"
        else:
            if unit == "1":
                suffix = 'st'
            elif unit == "2":
                suffix = 'nd'
            elif unit == "3":
                suffix = 'rd'
            else:
                suffix = 'th'
    return str(numb) + suffix


# Getting the data for the map given 2 inputs, including a defaulted selection
def map_fires(yearly, majory="All Fires"):
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['ArchiveYear', 'Latitude', 'Longitude', 'MajorIncident', 'Name', 'Counties', 'UniqueId'])
    df = df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})

    # Cleaning up the data to only include those latitudes and longitudes in CA
    df2 = df[(df.lat != 0)]
    df2.drop(df2.loc[df['lat'] < 32].index, inplace=True)
    df2.drop(df2.loc[df['lat'] > 44].index, inplace=True)
    df2.drop(df2.loc[df['lon'] > -114].index, inplace=True)
    df2.drop(df2.loc[df['lon'] < -124].index, inplace=True)

    # Renaming the Major Incident column from True or False to Major or Minor for better usability
    df2.replace({'MajorIncident': True}, {'MajorIncident': 'Major'}, regex=True, inplace=True)
    df2.replace({'MajorIncident': False}, {'MajorIncident': 'Minor'}, regex=True, inplace=True)

    if majory == "All Fires":
        df5 = df2[(df2['ArchiveYear'] == yearly)]
    else:
        df3 = df2[(df2['ArchiveYear'] == yearly)]
        df5 = df3[(df3['MajorIncident'] == majory)]

    return df5  # Returning a dataframe that is filtered on what user selected


def final_map():  # Creating the final Map tab
    st.title("California Fires Map by Year")

    year_select = st.selectbox("Select Year", year_list(), index=3)  # Starting on 2016 for no apparent reason but to be different
    major = st.radio('Filter by Major or Minor Fire?', ["All Fires", "Major", "Minor"])
    df = map_fires(year_select, major)

    view_state = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=5,
        pitch=0)

    # Custom tool tip that updates the color and the label based on selection by user
    if major == "Major":
        layer1 = pdk.Layer('ScatterplotLayer', data=df, get_position='[lon, lat]', get_radius=10000, get_color=[255, 0, 0], pickable=True)
        tool_tip = {"html": "Name: '{Name}'", "style": {"backgroundColor": "red", "color": "black"}}

    elif major == "Minor":
        layer1 = pdk.Layer('ScatterplotLayer', data=df, get_position='[lon, lat]', get_radius=10000, get_color=[204, 204, 0], pickable=True)
        tool_tip = {"html": "Name: '{Name}'", "style": {"backgroundColor": "yellow", "color": "black"}}

    else:
        layer1 = pdk.Layer('ScatterplotLayer', data=df, get_position='[lon, lat]', get_radius=10000, get_color=[255, 165, 0], pickable=True)
        tool_tip = {"html": "Name: '{Name}' - ({MajorIncident})", "style": {"backgroundColor": "orange", "color": "black"}}

    mapz = pdk.Deck(map_style='mapbox://styles/mapbox/outdoors-v11', initial_view_state=view_state, layers=[layer1], tooltip=tool_tip)
    st.pydeck_chart(mapz)

    # Creating pivot table to show the counties and the number of fires that are Major or Minor
    st.subheader("Fires by County in Year Selected:")
    table = df.pivot_table(values='UniqueId', index='Counties', columns='MajorIncident', aggfunc=pd.Series.nunique, fill_value=0)
    st.table(table)


def bar_fire(counties):  # Creating bar chart for the Top Charts
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['Name', 'Counties', 'ArchiveYear', 'AcresBurned', 'UniqueId'])
    df.sort_values(by='AcresBurned', ascending=False, inplace=True)
    df.drop_duplicates(subset='UniqueId', inplace=True)
    if len(counties):  # Checking if the user has selected anything, if so, then filters to that country
        df = df[df['Counties'].isin(counties)]
    df = df.reset_index(drop=True)
    df = df.drop(columns='UniqueId')  # Getting rid of duplicates
    df['AcresBurned'].fillna(0, inplace=True)  # Replacing and blanks with 0
    df10 = df[:10]  # Making a top 10 list of the values
    labels = year_list()
    total_years = []
    stack_list = []
    stacklist2 = []

    # Getting total for the entire data set for chart
    for year in labels:
        total_acres = 0
        for index, row in df.iterrows():
            fire_year = row['ArchiveYear']
            if fire_year == year:
                total_acres = total_acres + row['AcresBurned']/1000
        total_years.append(total_acres)

    # Creating a list of lists to be able to generate a stacked bar chart
    for y in counties:
        stack_list = []
        for year in labels:
            county_acres = 0
            for index, row in df.iterrows():
                if row['ArchiveYear'] == year:
                    if row['Counties'] == y:
                        county_acres = county_acres + row['AcresBurned']/1000
            stack_list.append(county_acres)
        stacklist2.append(stack_list)

    # Using def o to create ordinal numbers for a top 10 i.e. 1 becomes 1st, 2 becomes 2nd
    rank = []
    for i in range(1, 11):
        place = o(i)
        rank.append(place)
    print(rank)
    for i in range(0, 10):
        df10 = df10.rename(index={i: rank[i]})

    df10['AcresBurned'] = df10['AcresBurned'].map('{:,.0f}'.format)
    df['AcresBurned'] = df['AcresBurned'].map('{:,.0f}'.format)

    # Creating the graph
    x = np.arange(len(labels))
    county_count = 0
    # This if below is for the stacked bar chart, stacks if the user has selected any counties, else normal bar chart
    if len(counties):
        fig, ax = plt.subplots()
        ax.bar(x, stacklist2[0], .5, label=counties[county_count], edgecolor='black')
        county_count += 1
        if len(counties) > 1:
            ax.bar(x, stacklist2[1], .5, label=counties[county_count], edgecolor='black', bottom=stacklist2[0])
            county_count += 1
            if len(counties) > 2:
                ax.bar(x, stacklist2[2], .5, label=counties[county_count], edgecolor='black', bottom=np.array(stacklist2[0])+np.array(stacklist2[1]))
                county_count += 1
                if len(counties) > 3:
                    ax.bar(x, stacklist2[3], .5, label=counties[county_count], edgecolor='black', bottom=np.array(stacklist2[0])+np.array(stacklist2[1])+np.array(stacklist2[2]))
    else:
        fig, ax = plt.subplots()
        ax.bar(x, total_years, .5, label='All Counties', color='#EC5819', edgecolor='red')
    # Formatting bar chart
    plt.grid(color='gray', axis='y', linewidth=0.2)
    ax.set_ylabel('Acres Burned (Thousands)')
    ax.set_xlabel('Year')
    ax.set_title('Total Acres Burned by Year', weight='bold', fontname='Times New Roman', fontsize=18)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))  # Updating format of axis
    ax.legend(loc='upper left')

    st.subheader("Top 10 Fires by Size")
    st.table(df10)
    st.pyplot(fig)


def most_fatal(county):  # Returning the deadliest fires given a county
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['Name', 'Counties', 'ArchiveYear', 'UniqueId', 'Fatalities', 'SearchDescription'])
    df.drop_duplicates(subset='UniqueId', inplace=True)
    df.sort_values(by='Fatalities', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['Fatalities'].fillna("None", inplace=True)
    df['SearchDescription'].fillna("No Description", inplace=True)

    if county.title() == 'All':
        fatal_name = df.loc[0, 'Name']
        fatal_year = df.loc[0, 'ArchiveYear']
        fatals = df.loc[0, 'Fatalities']
        fatal_desc = df.loc[0, 'SearchDescription']
    else:
        df2 = df[df['Counties'] == county.title()]
        fatal_name = df2['Name'].iloc[0]
        fatal_year = df2['ArchiveYear'].iloc[0]
        fatals = df2['Fatalities'].iloc[0]
        fatal_desc = df2['SearchDescription'].iloc[0]
    return fatal_name, fatal_year, fatals, fatal_desc


def most_injury(county):  # Returning the fires that injured the most people given a county
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['Name', 'Counties', 'ArchiveYear', 'UniqueId', 'Injuries', 'SearchDescription'])
    df.drop_duplicates(subset='UniqueId', inplace=True)
    df.sort_values(by='Injuries', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['Injuries'].fillna("None", inplace=True)
    df['SearchDescription'].fillna("No Description", inplace=True)

    if county.title() == 'All':
        injury_name = df.loc[0, 'Name']
        injury_year = df.loc[0, 'ArchiveYear']
        injury = df.loc[0, 'Injuries']
        injury_desc = df.loc[0, 'SearchDescription']
    else:
        df2 = df[df['Counties'] == county.title()]
        injury_name = df2['Name'].iloc[0]
        injury_year = df2['ArchiveYear'].iloc[0]
        injury = df2['Injuries'].iloc[0]
        injury_desc = df2['SearchDescription'].iloc[0]
    return injury_name, injury_year, injury, injury_desc


def destroyed(county_selected):  # Creates a horizontal bar chart on top 5 structures destroyed given user input
    datafile = "california_fire_incidents.csv"
    data = pd.read_csv(datafile)
    df = pd.DataFrame(data, columns=['Name', 'Counties', 'ArchiveYear', 'StructuresDestroyed', 'UniqueId'])
    df.sort_values(by='StructuresDestroyed', ascending=False, inplace=True)
    df.drop_duplicates(subset='UniqueId', inplace=True)
    # I removed this crazy long name as it made the chart visually unappealling
    indexnames = df[df['Name'] == 'Nuns / Adobe / Norrbom/ Pressley / Partrick Fires / Oakmont (Central LNU Complex)'].index
    df.drop(indexnames, inplace=True)

    df['StructuresDestroyed'].fillna(0, inplace=True)
    # If the user types All, then pull all data, else filter based on what user types
    if county_selected.title() == "All":
        df10 = df[:5]
    else:
        df2 = df[df['Counties'] == county_selected.title()]
        df10 = df2[:5]
    df10 = df10.reset_index(drop=True)
    df10max = df10.at[0, 'StructuresDestroyed'] * 1.25  # Creating max value of x-axis for visual purposes
    labels = []
    structured = []

    # Creates labeling for the chart to identify the fire name and year as some fire names are the same
    for index, row in df10.iterrows():
        fire_name = row['Name'] + " (" + str(row['ArchiveYear']) + ")"
        labels.append(fire_name)
        structures = row['StructuresDestroyed']
        structured.append(structures)

    # Create horizontal bar graph
    fig, ax = plt.subplots()
    plt.grid(color='gray', axis='x', linewidth=0.2)
    reacts = ax.barh(labels, structured, color='black', edgecolor='red')
    ax.set_title('Top 5 Fires by Structures Destroyed', weight='bold', fontname='Georgia', fontsize=18)
    ax.set_yticklabels(labels)
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.bar_label(reacts, padding=3)
    plt.xlim(left=0, right=df10max)
    ax.legend(loc='lower right')

    st.pyplot(fig)

# Creating the page along with sidebar to navigate different pages


st.sidebar.title("California Fires")
menu = ["Home", "Map", "Top Charts", "Most Dangerous"]

choice = st.sidebar.selectbox("Menu", menu)

if choice == "Map":
    final_map()

elif choice == "Home":
    st.title("Welcome to California Fires Insight")
    image = Image.open("wildfire.jpg")
    st.image(image)
    st.subheader(emoji.emojize("Created by Jacob Carvalho :star2:"))
    st.empty()
    st.subheader('California Wildires Resources')
    st.write(emoji.emojize(":fire:") + "[Current CA Fires](https://www.fire.ca.gov/incidents/)")
    st.write(emoji.emojize(":newspaper:") + "[SF Chronicle Fire Tracker](https://www.sfchronicle.com/projects/california-fire-map/)")
    st.write(emoji.emojize(":bear:") + "[Smokey Bear](https://www.smokeybear.com/en)")

elif choice == "Top Charts":
    st.title("Top Biggest Fires 2013-2019")
    selected = st.multiselect('Select County (Max of 4 for Chart)', county_list())
    bar_fire(selected)

elif choice == "Most Dangerous":
    st.title(emoji.emojize("Most Dangerous Fires :sos:"))
    user_input = st.text_input("Search by County or type: All", "All")
    df = county_list()

    if user_input.title() not in df.values:
        if user_input.title() != "All":
            st.error("County does not exist. Reset to All")
            user_input = "All"

    col1, col2 = st.beta_columns(2)

    # Call most_fatal and most_injury to return the details of those fires
    fatal_name = most_fatal(user_input)[0]
    fatal_year = str(most_fatal(user_input)[1])
    fatals = (most_fatal(user_input)[2])
    fatal_desc = (most_fatal(user_input)[3])
    injury_name = most_injury(user_input)[0]
    injury_year = str(most_injury(user_input)[1])
    injury = (most_injury(user_input)[2])
    injury_desc = (most_injury(user_input)[3])

    with col1:  # Fatal data
        st.header(emoji.emojize("Most Fatalities :skull:"))
        st.subheader("Name: " + fatal_name)
        st.write("Year: " + fatal_year)
        if type(fatals) == str:
            st.write(f"Fatalities: ", fatals)
        else:
            st.write(f"Fatalities: {fatals:,.0f}")
        with st.beta_expander('Description'):
            st.write(fatal_desc)
    with col2:  # Injury data
        st.header(emoji.emojize("Most Injuries :hospital:"))
        st.subheader("Name: " + injury_name)
        st.write("Year: " + injury_year)
        if type(injury) == str:
            st.write(f"Injuries: ", injury)
        else:
            st.write(f"Injuries: {injury:,.0f}")
        with st.beta_expander('Description'):
            st.write(injury_desc)
    # Chart that holds the structures destroyed
    st.title(emoji.emojize("Most Structures Destroyed :fire_engine: :fire:"))
    destroyed(user_input)
