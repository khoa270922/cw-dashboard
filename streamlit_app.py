import streamlit as st
import psycopg2
import yaml
import pandas as pd
import altair as alt

# Function to load YAML configuration
def load_tree_config():
    with open('tree_config.yaml', 'r') as file:
        return yaml.safe_load(file)

# Loading the YAML file
tree_config = load_tree_config()

# Accessing SQL queries from secrets, convert to dict an get exact query with key
get_stock_data_query = st.secrets["queries"]["get_stock_data"]

# Initialize session state for stock selection
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

def get_stock_data(stock_name):
    
    # Initialize connection. # Perform query.
    # conn = st.connection("postgresql", type="sql")
    # query = f"SELECT * FROM history WHERE stock = '{stock_name}'  order by date desc limit 10"    
    # data = pd.read_sql(query, conn)
    
    connection = psycopg2.connect(
            host=st.secrets["database"]["host"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            dbname=st.secrets["database"]["dbname"],
            sslmode='require'
        )
    cursor = connection.cursor()
    # Execute the query securely using parameterized queries
    cursor.execute(get_stock_data_query, (stock_name,))
    result = cursor.fetchall()

    # Get column names dynamically from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    cursor.close()        
    connection.close()
    
    # Convert the stock data to a pandas DataFrame with dynamic column names
    df = pd.DataFrame(result, columns=column_names)

    # Ensure the 'Date' column is in datetime format (adjust if your schema has a different name for the date column)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])

    return df


# Left Panel Layout
with st.sidebar:
    st.sidebar.title("Stock Input Panel")
    stock_name_input = st.sidebar.text_input("Nhập mã chứng khoán:")
    #stock_name = st.text_input("## nhập mã cổ phiếu")

    if stock_name_input:
        st.session_state.selected_stock = stock_name_input  # Store the selected stock name
        #st.query_params.selected_stock=stock_name_input)  # Keep the selection state

# Main Content: Display the query result on the right
st.title("Stock Data Dashboard")
if st.session_state.selected_stock:
    st.write(f"Kết quả phân tích: {st.session_state.selected_stock}")
    stock_data = get_stock_data(st.session_state.selected_stock)

    if not stock_data.empty:        
        hover = alt.selection_single(
            fields=["date"],
            nearest=True,
            on="mouseover",
            empty="none",
        )

        recommend_order = ['STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL']
        lines = alt.Chart(stock_data).mark_line().encode(
            x=alt.X('date:T', axis=alt.Axis(title='Ngày', format='%d/%m/%Y')),
            y=alt.Y('recommendation:N', axis=alt.Axis(title='KHUYẾN NGHỊ'), sort=recommend_order),
            color='stock',
            #color=alt.Color('stock', sort=recommend_order),
            #order=alt.Order('y_site_sort_index:Q')
        ).properties(
            width=600,  # Customize the width
            height=400  # Customize the height
        )

        points = lines.transform_filter(hover).mark_circle(size=65)
        tooltips = (
            alt.Chart(stock_data)
            .mark_rule()
            .encode(
                x="yearmonthdate(date)",
                y=alt.Y('recommendation', sort=recommend_order),
                opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
                tooltip=[
                    alt.Tooltip("date", title="Ngày"),
                    alt.Tooltip("recommendation", title="Khuyến nghị"),
                    alt.Tooltip("stock", title="mã cp"),
                ],
            )
            .add_params(hover)
        )

        data_layer = lines + points + tooltips

        # Display the chart in Streamlit
        st.altair_chart(data_layer, use_container_width=True)
        st.write(stock_data[stock_data['stock']==st.session_state.selected_stock])
    else:
        st.write('No data for this stock')

