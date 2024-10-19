import streamlit as st
import pandas as pd

# Initialize connection.
conn = st.connection("postgresql", type="sql")

# Perform query.
data = conn.query('select * from history order by date desc limit 10', ttl="10m")

df = pd.DataFrame(data)
# Title of the app
st.title("Stock Data Dashboard")
# Print results.
st.table(df)



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