import streamlit as st
import psycopg2
from psycopg2 import pool
import yaml
import pandas as pd
import altair as alt

# Function to get a connection from the pool
def get_connection():
    return st.session_state.db_pool.getconn()

# Function to return a connection to the pool
def return_connection(conn):
    st.session_state.db_pool.putconn(conn)

# Function to load YAML configuration
def load_tree_config():
    with open('tree_config.yaml', 'r') as file:
        return yaml.safe_load(file)

# Function to load stock data
def get_stock_data(stock_name):
    
    connection = get_connection()
    cursor = connection.cursor()
    # Execute the query securely using parameterized queries
    cursor.execute(get_stock_data_query, (stock_name,))
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

    # Ensure the 'Date' column is in datetime format (adjust if your schema has a different name for the date column)
    #if 'Date' in df.columns:
    #    df['Date'] = pd.to_datetime(df['Date'])

    return df

# Loading the YAML file
tree_config = load_tree_config()

# Accessing SQL queries from secrets, convert to dict an get exact query with key
get_stock_data_query = st.secrets["queries"]["get_stock_data"]

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
    stock_name_input = st.sidebar.text_input("INPUT YOUR STOCK:")
    #stock_name = st.text_input("## nhập mã cổ phiếu")

    if stock_name_input:
        st.session_state.selected_stock = stock_name_input  # Store the selected stock name
        #st.query_params.selected_stock=stock_name_input)  # Keep the selection state

# Main Content: Display the query result on the right
# st.title("Stock Data Dashboard")
if st.session_state.selected_stock:
    st.write(f"{st.session_state.selected_stock} daily analysis:  ")
    stock_data = get_stock_data(st.session_state.selected_stock)

    if not stock_data.empty:        

        # Display line chart
        recommend_order = ['STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL']

        # Create the point chart
        chart = alt.Chart(stock_data).mark_point(size=100).encode(
            x=alt.X('Date:O', axis=None),  # Ordinal x-axis to only display provided dates
            y=alt.Y('recommendation:N', axis=alt.Axis(title=''), sort=recommend_order),  # Nominal y-axis for recommendations
            tooltip=[alt.Tooltip('stock:N'), alt.Tooltip('recommendation:N'), alt.Tooltip('Date:O')]  # Tooltips for interactivity
        ).properties(
            width=600,
            height=200
        )
        st.altair_chart(chart, use_container_width=True)

        # Display stack chart
        # Reshape the DataFrame using pd.melt() to convert the bp, np, sp columns to a single 'Rating' column
        df_melted = pd.melt(stock_data[stock_data['stock']==st.session_state.selected_stock], id_vars=['stock', 'date'], 
                            value_vars=['bp', 'np', 'sp'], 
                            var_name='Rating', 
                            value_name='Percentage')
        # Map 'Rating' to human-readable labels
        rating_map = {'bp': 'Buy', 'np': 'Neutral', 'sp': 'Sell'}
        df_melted['Rating'] = df_melted['Rating'].map(rating_map)
        # Convert 'Date' column to datetime
        #df_melted['Date'] = pd.to_datetime(df_melted['date'])
        df_melted['Date'] = df_melted['date'].astype(str)
        
        # Define custom colors for the ratings
        area_color = alt.Scale(
            domain=['Buy', 'Neutral', 'Sell'],
            range=['#00ff00', '#ffff00', '#ff0000']
        )

        area_chart = alt.Chart(df_melted).mark_area().encode(
            x=alt.X('Date:O', title="", axis=alt.Axis(title='')),
            y=alt.Y('sum(Percentage):Q', title="", axis=None),
            color=alt.Color('Rating:N', scale=area_color).legend(orient="left"),  # Custom colors for ratings
            opacity={"value": 0.7},
            tooltip=[alt.Tooltip('stock:N', title="Stock"), alt.Tooltip('date:T', title="Date"), alt.Tooltip('Rating:N', title="Recommendation"), alt.Tooltip('Percentage:Q', format='.0%', title="Ratio")]  # Tooltips for interactivity
        ).properties(
            width=800,
            height=300
        ) #.interactive()

        # Display the chart in Streamlit
        st.altair_chart(area_chart, use_container_width=True)

    else:
        st.write('No data for this stock')

