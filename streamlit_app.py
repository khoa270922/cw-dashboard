import time
import datetime as dt
import streamlit as st
import psycopg2
from psycopg2 import pool
import yaml
import pandas as pd
import altair as alt
import requests

# Load YAML configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Function to get a connection from the pool
def get_connection():
    return st.session_state.db_pool.getconn()

# Function to return a connection to the pool
def return_connection(conn):
    st.session_state.db_pool.putconn(conn)

# Function to load stock data
def get_ts(stock_name):
    
    connection = get_connection()
    cursor = connection.cursor()
    # Execute the query securely using parameterized queries
    cursor.execute(query_ts, (stock_name,))
    result = cursor.fetchall()

    # Get column names dynamically from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    cursor.close()        
    return_connection(connection)
    
    # Convert the stock data to a pandas DataFrame with dynamic column names
    df = pd.DataFrame(result, columns=column_names)
    df['bp'] = df['buy'] / (df['buy'] + df['sell'] + df['neutral'])
    df['np'] = df['neutral'] / (df['buy'] + df['sell'] + df['neutral'])
    df['sp'] = df['sell'] / (df['buy'] + df['sell'] + df['neutral'])
    df['Date'] = df['date'].astype(str)
    return df

def get_h(stock_name, from_date, to_date):
    header = config['headers']['vietstock']['header_0']
    url = config['urls']['vietstock']['history'] + stock_name + '&resolution=1d&from=' + str(from_date) + '&to=' + str(to_date)        
    
    response = requests.get(url, headers = header)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['o']=df['o']/1000
        df['h']=df['h']/1000
        df['l']=df['l']/1000
        df['c']=df['c']/1000
        df['Date']=pd.to_datetime(df['t'], unit ='s').apply(lambda x: x.date())
        df['Date'] = df['Date'].astype(str)        
        return df
    else:
        print("error request")

# Accessing SQL queries from secrets, convert to dict an get exact query with key
query_ts = st.secrets['queries']['gts']

# Initialize connection pool (do this once at the app start)
if 'db_pool' not in st.session_state:
    st.session_state.db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,  # Min 1 and max 20 connections in the pool
        host=st.secrets["database"]["host"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        dbname=st.secrets["database"]["dbname"],
        port="5432",
        sslmode='require'
    )

# Initialize session state for stock selection
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# Left Panel Layout
with st.sidebar:
    #st.sidebar.title("Stock Input Panel")
    stock_name_input = st.sidebar.text_input("INPUT STOCK:")
    #stock_name = st.text_input("## nhập mã cổ phiếu")
  

    if stock_name_input:
        st.session_state.selected_stock = stock_name_input  # Store the selected stock name
        #st.query_params.selected_stock=stock_name_input)  # Keep the selection state

# Main Content: Display the query result on the right
if st.session_state.selected_stock:
    
    st.markdown(f''':sunglasses: Happy analyz-ing :blue[{st.session_state.selected_stock}] :heart:''')
    
    ts_data = get_ts(st.session_state.selected_stock)
    
    today = dt.date.today()
    from_date = round(pd.Timestamp(ts_data['date'].min()).timestamp())
    to_date = round(time.mktime((today.year, today.month, today.day, 0, 0, 0, 0, 0, 0)))
    
    h_data = get_h(st.session_state.selected_stock, from_date, to_date)
    
    if not h_data.empty:
        line_chart = alt.Chart(h_data).mark_line(point=True).encode(
            x=alt.X('Date:O', title=''),
            y=alt.Y('c:Q', title='Closed Price').scale(zero=False), # Set custom order for Y-axis
            tooltip=[alt.Tooltip('Date:O'), alt.Tooltip('c:Q', title='ClosePrice'),]
        ).properties(
            width=600,  # Customize the width
            height=300  # Customize the height
        )
        st.altair_chart(line_chart, use_container_width=True)

    if not ts_data.empty:        

        # Display line chart
        recommend_order = ['STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL']

        # Create the point chart
        point_chart = alt.Chart(ts_data).mark_point(size=100).encode(
            x=alt.X('Date:O', axis=None),  # Ordinal x-axis to only display provided dates
            y=alt.Y('recommendation:N', axis=alt.Axis(title=''), sort=recommend_order),  # Nominal y-axis for recommendations
            tooltip=[alt.Tooltip('stock:N'), alt.Tooltip('recommendation:N'), alt.Tooltip('Date:O')]  # Tooltips for interactivity
        ).properties(
            width=600,
            height=200
        )

        st.altair_chart(point_chart, use_container_width=True)

        # Reshape the DataFrame using pd.melt() to convert the bp, np, sp columns to a single 'Rating' column
        df_melted = pd.melt(ts_data[ts_data['stock']==st.session_state.selected_stock], id_vars=['stock', 'date'], 
                            value_vars=['bp', 'np', 'sp'], 
                            var_name='Rating', 
                            value_name='Percentage')
        # Map 'Rating' to human-readable labels
        rating_map = {'bp': 'Buy', 'np': 'Neutral', 'sp': 'Sell'}
        df_melted['Rating'] = df_melted['Rating'].map(rating_map)
        df_melted['Date'] = df_melted['date'].astype(str)
        
        # Define custom colors for the ratings
        area_color = alt.Scale(
            domain=['Buy', 'Neutral', 'Sell'],
            range=['#00ff00', '#ffff00', '#ff0000']
        )

        area_chart = alt.Chart(df_melted).mark_area().encode(
            x=alt.X('Date:O', title="", axis=alt.Axis(title='')),
            y=alt.Y('sum(Percentage):Q', title="", axis=None),
            color=alt.Color('Rating:N', scale=area_color, title="").legend(orient="bottom"),  # Custom colors for ratings
            opacity={"value": 0.7},
            tooltip=[alt.Tooltip('stock:N', title="Stock"), alt.Tooltip('date:T', title="Date"), alt.Tooltip('Rating:N', title="Recommendation"), alt.Tooltip('Percentage:Q', format='.0%', title="Ratio")]  # Tooltips for interactivity
        ).properties(
            width=800,
            height=300
        )

        # Display the chart in Streamlit
        st.altair_chart(area_chart, use_container_width=True)

    else:
        st.write('No data for this stock')