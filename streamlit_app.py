import streamlit as st
import pandas as pd

# Title of the app
st.title("Stock Data Dashboard")

# Load stock data from database or API
data = {
    'Date': ["2024-10-10", "2024-10-11", "2024-10-12"],
    'Price': [150, 155, 160]
}
df = pd.DataFrame(data)

# Display data as a table
st.table(df)

# Line chart of stock prices
st.line_chart(df.set_index('Date')['Price'])
