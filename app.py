import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

st.set_page_config(page_title="eBay Sales Analytics Dashboard", layout="wide")

def parse_sales_data(file_content):
    """Parse the sales CSV data - handles mixed formats with/without price"""
    import io
    
    try:
        # Read CSV
        df = pd.read_csv(io.StringIO(file_content), header=None, on_bad_lines='skip', engine='python')
        
        # Check if first row is a header
        if df.iloc[0, 0] and isinstance(df.iloc[0, 0], str) and 'keyword' in df.iloc[0, 0].lower():
            df = df.iloc[1:]
        
        df = df.reset_index(drop=True)
        num_cols = len(df.columns)
        
        # Detect format: check if column 3 (index 2) has prices
        has_price = False
        if num_cols >= 7:
            # Sample first 10 rows to detect
            sample = df.iloc[:min(10, len(df)), 2].astype(str)
            if sample.str.contains('\

st.title("📊 eBay Sales Analytics Dashboard")
st.markdown("---")

uploaded_file = st.file_uploader("📁 Upload your sales CSV", type=['csv', 'txt'])

if uploaded_file:
    df = parse_sales_data(uploaded_file.getvalue().decode('utf-8'))
    
    if not df.empty:
        # Filters
        st.sidebar.header("🔍 Filters")
        products = ['All Products'] + sorted(df['Product'].unique().tolist())
        selected_product = st.sidebar.selectbox("Product", products)
        
        filtered_df = df if selected_product == 'All Products' else df[df['Product'] == selected_product]
        
        # Key Metrics
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Products", f"{len(filtered_df):,}")
        col2.metric("Dec Sales", f"{filtered_df['Dec 2025 Sales'].sum():,}")
        col3.metric("Jan Sales", f"{filtered_df['Jan 2026 Sales'].sum():,}")
        col4.metric("Total Sales", f"{filtered_df['Total Sales'].sum():,}")
        col5.metric("Total Revenue", f"${filtered_df['Total Revenue'].sum():,.2f}")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🏆 Top Products", "📋 All Data", "📊 Stats"])
        
        with tab1:
            st.markdown("### Top 30 Products by Total Sales")
            top = filtered_df.nlargest(30, 'Total Sales')
            
            for _, row in top.iterrows():
                price_display = f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else "No price"
                revenue_display = f"${row['Total Revenue']:,.2f}" if row['Price'] != 'No price' else "N/A"
                
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:1rem; margin:0.5rem 0; border-left:4px solid #667eea; border-radius:4px;">
                    <strong>{row['Product'].title()}</strong> (ID: {row['Item ID']})<br>
                    Price: <strong>{price_display}</strong> | Sales: <strong>{row['Total Sales']}</strong> | Revenue: <strong>{revenue_display}</strong><br>
                    Dec: {row['Dec 2025 Sales']} → Jan: {row['Jan 2026 Sales']} ({row['Growth %']:+.0f}%)
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("### Complete Product List")
            
            # Format price column for display
            display_df = filtered_df.copy()
            display_df['Price Display'] = display_df.apply(
                lambda row: f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else 'No price', axis=1
            )
            
            st.dataframe(
                display_df[['Product', 'Item ID', 'Price Display', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth %', 'Total Revenue', 'URL']].sort_values('Total Sales', ascending=False),
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Price Display": "Price",
                    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f")
                }
            )
        
        with tab3:
            st.markdown("### Product Categories")
            
            category_stats = filtered_df.groupby('Product').agg({
                'Total Sales': 'sum',
                'Total Revenue': 'sum',
                'URL': 'count',
                'Price Numeric': 'mean'
            }).reset_index()
            category_stats.columns = ['Product', 'Total Sales', 'Total Revenue', 'Listings', 'Avg Price']
            category_stats = category_stats.sort_values('Total Sales', ascending=False)
            
            st.dataframe(
                category_stats,
                use_container_width=True,
                column_config={
                    "Total Sales": st.column_config.NumberColumn("Sales", format="%d"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
                    "Listings": st.column_config.NumberColumn("# Listings", format="%d"),
                    "Avg Price": st.column_config.NumberColumn("Avg Price", format="$%.2f")
                }
            )
else:
    st.info("👆 Upload your CSV to get started!")
    st.markdown("""
    ### Supported Format:
    Your CSV can have mixed formats:
    - **With price**: `Product, URL, Price, Dec Sales, Jan Sales, Date, Status`
    - **Without price**: `Product, URL, Dec Sales, Jan Sales, Date, Status`
    
    Products without price will show "No price" in the dashboard.
    """), regex=False).sum() >= 3:
                has_price = True
        
        if has_price and num_cols >= 7:
            # New format with price
            df.columns = ['Product', 'URL', 'Price', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked', 'Status'] + [f'Extra_{i}' for i in range(num_cols - 7)]
        elif num_cols >= 6:
            # Old format without price
            df.columns = ['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked', 'Status'] + [f'Extra_{i}' for i in range(num_cols - 6)]
            df['Price'] = 0.0
        else:
            df.columns = ['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked'] + [f'Extra_{i}' for i in range(num_cols - 5)]
            df['Price'] = 0.0
            df['Status'] = 'N/A'
        
        # Convert sales columns to numeric
        df['Dec 2025 Sales'] = pd.to_numeric(df['Dec 2025 Sales'], errors='coerce').fillna(0).astype(int)
        df['Jan 2026 Sales'] = pd.to_numeric(df['Jan 2026 Sales'], errors='coerce').fillna(0).astype(int)
        
        # Convert price to numeric
        if 'Price' in df.columns:
            df['Price'] = df['Price'].astype(str).str.replace('

st.title("📊 eBay Sales Analytics Dashboard")
st.markdown("---")

uploaded_file = st.file_uploader("📁 Upload your sales CSV", type=['csv', 'txt'])

if uploaded_file:
    df = parse_sales_data(uploaded_file.getvalue().decode('utf-8'))
    
    if not df.empty:
        # Filters
        st.sidebar.header("🔍 Filters")
        products = ['All Products'] + sorted(df['Product'].unique().tolist())
        selected_product = st.sidebar.selectbox("Product", products)
        
        filtered_df = df if selected_product == 'All Products' else df[df['Product'] == selected_product]
        
        # Key Metrics
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Products", f"{len(filtered_df):,}")
        col2.metric("Dec Sales", f"{filtered_df['Dec 2025 Sales'].sum():,}")
        col3.metric("Jan Sales", f"{filtered_df['Jan 2026 Sales'].sum():,}")
        col4.metric("Total Sales", f"{filtered_df['Total Sales'].sum():,}")
        col5.metric("Total Revenue", f"${filtered_df['Total Revenue'].sum():,.2f}")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🏆 Top Products", "📋 All Data", "📊 Stats"])
        
        with tab1:
            st.markdown("### Top 30 Products by Total Sales")
            top = filtered_df.nlargest(30, 'Total Sales')
            
            for _, row in top.iterrows():
                price_display = f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else "No price"
                revenue_display = f"${row['Total Revenue']:,.2f}" if row['Price'] != 'No price' else "N/A"
                
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:1rem; margin:0.5rem 0; border-left:4px solid #667eea; border-radius:4px;">
                    <strong>{row['Product'].title()}</strong> (ID: {row['Item ID']})<br>
                    Price: <strong>{price_display}</strong> | Sales: <strong>{row['Total Sales']}</strong> | Revenue: <strong>{revenue_display}</strong><br>
                    Dec: {row['Dec 2025 Sales']} → Jan: {row['Jan 2026 Sales']} ({row['Growth %']:+.0f}%)
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("### Complete Product List")
            
            # Format price column for display
            display_df = filtered_df.copy()
            display_df['Price Display'] = display_df.apply(
                lambda row: f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else 'No price', axis=1
            )
            
            st.dataframe(
                display_df[['Product', 'Item ID', 'Price Display', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth %', 'Total Revenue', 'URL']].sort_values('Total Sales', ascending=False),
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Price Display": "Price",
                    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f")
                }
            )
        
        with tab3:
            st.markdown("### Product Categories")
            
            category_stats = filtered_df.groupby('Product').agg({
                'Total Sales': 'sum',
                'Total Revenue': 'sum',
                'URL': 'count',
                'Price Numeric': 'mean'
            }).reset_index()
            category_stats.columns = ['Product', 'Total Sales', 'Total Revenue', 'Listings', 'Avg Price']
            category_stats = category_stats.sort_values('Total Sales', ascending=False)
            
            st.dataframe(
                category_stats,
                use_container_width=True,
                column_config={
                    "Total Sales": st.column_config.NumberColumn("Sales", format="%d"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
                    "Listings": st.column_config.NumberColumn("# Listings", format="%d"),
                    "Avg Price": st.column_config.NumberColumn("Avg Price", format="$%.2f")
                }
            )
else:
    st.info("👆 Upload your CSV to get started!")
    st.markdown("""
    ### Supported Format:
    Your CSV can have mixed formats:
    - **With price**: `Product, URL, Price, Dec Sales, Jan Sales, Date, Status`
    - **Without price**: `Product, URL, Dec Sales, Jan Sales, Date, Status`
    
    Products without price will show "No price" in the dashboard.
    """), '').str.replace(',', '').str.strip()
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).astype(float)
        
        # Calculate metrics
        df['Total Sales'] = df['Dec 2025 Sales'] + df['Jan 2026 Sales']
        df['Growth'] = df['Jan 2026 Sales'] - df['Dec 2025 Sales']
        df['Growth %'] = df.apply(
            lambda row: ((row['Jan 2026 Sales'] - row['Dec 2025 Sales']) / row['Dec 2025 Sales'] * 100) 
            if row['Dec 2025 Sales'] > 0 
            else (100 if row['Jan 2026 Sales'] > 0 else 0),
            axis=1
        )
        
        # Calculate revenue metrics
        df['Dec Revenue'] = df['Dec 2025 Sales'] * df['Price']
        df['Jan Revenue'] = df['Jan 2026 Sales'] * df['Price']
        df['Total Revenue'] = df['Total Sales'] * df['Price']
        df['Revenue Growth'] = df['Jan Revenue'] - df['Dec Revenue']
        
        # Extract Item ID from URL
        df['Item ID'] = df['URL'].apply(
            lambda x: re.search(r'/itm/(\d+)', str(x)).group(1) if re.search(r'/itm/(\d+)', str(x)) else 'N/A'
        )
        
        # Clean up data types
        df['Product'] = df['Product'].astype(str).str.strip()
        df['URL'] = df['URL'].astype(str).str.strip()
        df['Date Checked'] = df['Date Checked'].astype(str)
        df['Status'] = df['Status'].astype(str)
        
        # Filter out invalid rows
        df = df[df['URL'].str.contains('ebay.com', na=False)]
        
        return df[['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Price', 'Total Sales', 'Growth', 'Growth %', 
                   'Dec Revenue', 'Jan Revenue', 'Total Revenue', 'Revenue Growth', 'Date Checked', 'Status', 'Item ID']]
        
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return pd.DataFrame()

st.title("📊 eBay Sales Analytics Dashboard")
st.markdown("---")

uploaded_file = st.file_uploader("📁 Upload your sales CSV", type=['csv', 'txt'])

if uploaded_file:
    df = parse_sales_data(uploaded_file.getvalue().decode('utf-8'))
    
    if not df.empty:
        # Filters
        st.sidebar.header("🔍 Filters")
        products = ['All Products'] + sorted(df['Product'].unique().tolist())
        selected_product = st.sidebar.selectbox("Product", products)
        
        filtered_df = df if selected_product == 'All Products' else df[df['Product'] == selected_product]
        
        # Key Metrics
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Products", f"{len(filtered_df):,}")
        col2.metric("Dec Sales", f"{filtered_df['Dec 2025 Sales'].sum():,}")
        col3.metric("Jan Sales", f"{filtered_df['Jan 2026 Sales'].sum():,}")
        col4.metric("Total Sales", f"{filtered_df['Total Sales'].sum():,}")
        col5.metric("Total Revenue", f"${filtered_df['Total Revenue'].sum():,.2f}")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🏆 Top Products", "📋 All Data", "📊 Stats"])
        
        with tab1:
            st.markdown("### Top 30 Products by Total Sales")
            top = filtered_df.nlargest(30, 'Total Sales')
            
            for _, row in top.iterrows():
                price_display = f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else "No price"
                revenue_display = f"${row['Total Revenue']:,.2f}" if row['Price'] != 'No price' else "N/A"
                
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:1rem; margin:0.5rem 0; border-left:4px solid #667eea; border-radius:4px;">
                    <strong>{row['Product'].title()}</strong> (ID: {row['Item ID']})<br>
                    Price: <strong>{price_display}</strong> | Sales: <strong>{row['Total Sales']}</strong> | Revenue: <strong>{revenue_display}</strong><br>
                    Dec: {row['Dec 2025 Sales']} → Jan: {row['Jan 2026 Sales']} ({row['Growth %']:+.0f}%)
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("### Complete Product List")
            
            # Format price column for display
            display_df = filtered_df.copy()
            display_df['Price Display'] = display_df.apply(
                lambda row: f"${row['Price Numeric']:.2f}" if row['Price'] != 'No price' else 'No price', axis=1
            )
            
            st.dataframe(
                display_df[['Product', 'Item ID', 'Price Display', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth %', 'Total Revenue', 'URL']].sort_values('Total Sales', ascending=False),
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Price Display": "Price",
                    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f")
                }
            )
        
        with tab3:
            st.markdown("### Product Categories")
            
            category_stats = filtered_df.groupby('Product').agg({
                'Total Sales': 'sum',
                'Total Revenue': 'sum',
                'URL': 'count',
                'Price Numeric': 'mean'
            }).reset_index()
            category_stats.columns = ['Product', 'Total Sales', 'Total Revenue', 'Listings', 'Avg Price']
            category_stats = category_stats.sort_values('Total Sales', ascending=False)
            
            st.dataframe(
                category_stats,
                use_container_width=True,
                column_config={
                    "Total Sales": st.column_config.NumberColumn("Sales", format="%d"),
                    "Total Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
                    "Listings": st.column_config.NumberColumn("# Listings", format="%d"),
                    "Avg Price": st.column_config.NumberColumn("Avg Price", format="$%.2f")
                }
            )
else:
    st.info("👆 Upload your CSV to get started!")
    st.markdown("""
    ### Supported Format:
    Your CSV can have mixed formats:
    - **With price**: `Product, URL, Price, Dec Sales, Jan Sales, Date, Status`
    - **Without price**: `Product, URL, Dec Sales, Jan Sales, Date, Status`
    
    Products without price will show "No price" in the dashboard.
    """)
