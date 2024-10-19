import streamlit as st
import pandas as pd
import streamlit as st

# Initialize connection.
conn = st.connection("postgresql", type="sql")

# Perform query.
df = conn.query('select * from history where stock = "ACB" order by date desc', ttl="10m")

# Title of the app
st.title("Stock Data Dashboard")
# Print results.
for row in df.itertuples():
    st.write(f"{row}")
    print(row)


# Load stock data from database or API
data = {
    'Date': ["2024-10-10", "2024-10-11", "2024-10-12"],
    'Price': [150, 155, 160]
}
df = pd.DataFrame(data)

# Display data as a table
#st.table(df)

# Line chart of stock prices
#st.line_chart(df.set_index('Date')['Price'])
# Create a sidebar with a title and text input
#st.sidebar.title("Stock Input Panel")
#stock_name = st.sidebar.text_input("Enter stock name:")


# Display the input from the sidebar on the main page
#st.write(f"You have entered: {stock_name}")

# You can add more elements to the sidebar as needed