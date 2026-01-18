import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

st.set_page_config(page_title="eBay Sales Analytics Dashboard", layout="wide")

def parse_sales_data(file_content):
    import io
    lines = file_content.strip().split('\n')
    
    # Skip header if exists
    start_idx = 1 if 'keyword' in lines[0].lower() else 0
    
    data = []
    for line in lines[start_idx:]:
        parts = [p.strip() for p in line.split(',')]
        
        # Check if this row has price (7+ columns and 3rd col has $ or looks like price)
        if len(parts) >= 7 and ('$' in parts[2] or (parts[2].replace('.', '').isdigit() and float(parts[2].replace('$', '')) > 2)):
            # New format: Product, URL, Price, Dec, Jan, Date, Status
            data.append({
                'Product': parts[0],
                'URL': parts[1],
                'Price': parts[2].replace('$', ''),
                'Dec 2025 Sales': parts[3],
                'Jan 2026 Sales': parts[4],
                'Date': parts[5] if len(parts) > 5 else '',
                'Status': parts[6] if len(parts) > 6 else ''
            })
        elif len(parts) >= 6:
            # Old format: Product, URL, Dec, Jan, Date, Status (no price)
            data.append({
                'Product': parts[0],
                'URL': parts[1],
                'Price': 'No price',
                'Dec 2025 Sales': parts[2],
                'Jan 2026 Sales': parts[3],
                'Date': parts[4] if len(parts) > 4 else '',
                'Status': parts[5] if len(parts) > 5 else ''
            })
    
    df = pd.DataFrame(data)
    
    # Convert to numeric
    df['Dec 2025 Sales'] = pd.to_numeric(df['Dec 2025 Sales'], errors='coerce').fillna(0).astype(int)
    df['Jan 2026 Sales'] = pd.to_numeric(df['Jan 2026 Sales'], errors='coerce').fillna(0).astype(int)
    
    # Handle price - keep as string for "No price", convert numbers
    df['Price Numeric'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
    
    # Calculate sales metrics
    df['Total Sales'] = df['Dec 2025 Sales'] + df['Jan 2026 Sales']
    df['Growth'] = df['Jan 2026 Sales'] - df['Dec 2025 Sales']
    df['Growth %'] = df.apply(
        lambda row: ((row['Jan 2026 Sales'] - row['Dec 2025 Sales']) / row['Dec 2025 Sales'] * 100) 
        if row['Dec 2025 Sales'] > 0 else (100 if row['Jan 2026 Sales'] > 0 else 0), axis=1
    )
    
    # Calculate revenue
    df['Total Revenue'] = df['Total Sales'] * df['Price Numeric']
    
    # Extract Item ID
    df['Item ID'] = df['URL'].apply(lambda x: re.search(r'/itm/(\d+)', str(x)).group(1) if re.search(r'/itm/(\d+)', str(x)) else 'N/A')
    
    # Filter valid rows
    df = df[df['URL'].str.contains('ebay.com', na=False)]
    
    st.sidebar.success(f"✅ Loaded {len(df)} products")
    price_count = (df['Price'] != 'No price').sum()
    st.sidebar.info(f"💰 {price_count} with price, {len(df)-price_count} without price")
    
    return df

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
