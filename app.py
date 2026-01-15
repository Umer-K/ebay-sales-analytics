import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

st.set_page_config(page_title="eBay Sales Analytics Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .product-highlight {
        background-color: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #262730;
    }
    
    .stMarkdown {
        color: #262730 !important;
    }
    
    div[data-testid="stMarkdownContainer"] p {
        color: #262730 !important;
    }
    
    div[data-testid="stMarkdownContainer"] strong {
        color: #1f1f1f !important;
    }
    
    div[data-testid="stMarkdownContainer"] small {
        color: #555555 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def parse_sales_data(file_content):
    """Parse the sales CSV data"""
    import io
    
    # Try using pandas read_csv for more robust parsing
    try:
        df = pd.read_csv(io.StringIO(file_content), header=None)
        
        # Check if first row is a header
        if df.iloc[0, 0] and isinstance(df.iloc[0, 0], str) and 'keyword' in df.iloc[0, 0].lower():
            df = df.iloc[1:]  # Skip header
        
        # Assign column names
        if len(df.columns) >= 6:
            df.columns = ['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked', 'Status'] + [f'Extra_{i}' for i in range(len(df.columns) - 6)]
        
        # Convert sales columns to numeric
        df['Dec 2025 Sales'] = pd.to_numeric(df['Dec 2025 Sales'], errors='coerce').fillna(0).astype(int)
        df['Jan 2026 Sales'] = pd.to_numeric(df['Jan 2026 Sales'], errors='coerce').fillna(0).astype(int)
        
        # Calculate metrics
        df['Total Sales'] = df['Dec 2025 Sales'] + df['Jan 2026 Sales']
        df['Growth'] = df['Jan 2026 Sales'] - df['Dec 2025 Sales']
        df['Growth %'] = df.apply(
            lambda row: ((row['Jan 2026 Sales'] - row['Dec 2025 Sales']) / row['Dec 2025 Sales'] * 100) 
            if row['Dec 2025 Sales'] > 0 
            else (100 if row['Jan 2026 Sales'] > 0 else 0),
            axis=1
        )
        
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
        
        return df[['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth', 'Growth %', 'Date Checked', 'Status', 'Item ID']]
        
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return pd.DataFrame()

# Title
st.title("📊 eBay Sales Analytics Dashboard")
st.markdown("*Track and analyze product performance across December 2025 & January 2026*")
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("📁 Upload your sales data (CSV/TXT)", type=['csv', 'txt'])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode('utf-8')
    df = parse_sales_data(content)
    
    # ============ SIDEBAR FILTERS ============
    st.sidebar.header("🔍 Filters")
    
    # Product filter
    products = ['All Products'] + sorted(df['Product'].unique().tolist())
    selected_product = st.sidebar.selectbox("Filter by Product", products)
    
    # Sales performance filter
    performance_filter = st.sidebar.selectbox(
        "Performance Type",
        ["All", "Growing (Jan > Dec)", "Declining (Jan < Dec)", "No Sales", "New Sales (Dec=0, Jan>0)"]
    )
    
    # Sales range filters
    st.sidebar.markdown("### Sales Range")
    min_total_sales = st.sidebar.number_input("Min Total Sales", 0, int(df['Total Sales'].max()), 0)
    min_jan_sales = st.sidebar.number_input("Min Jan Sales", 0, int(df['Jan 2026 Sales'].max()), 0)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_product != 'All Products':
        filtered_df = filtered_df[filtered_df['Product'] == selected_product]
    
    if performance_filter == "Growing (Jan > Dec)":
        filtered_df = filtered_df[filtered_df['Growth'] > 0]
    elif performance_filter == "Declining (Jan < Dec)":
        filtered_df = filtered_df[filtered_df['Growth'] < 0]
    elif performance_filter == "No Sales":
        filtered_df = filtered_df[filtered_df['Total Sales'] == 0]
    elif performance_filter == "New Sales (Dec=0, Jan>0)":
        filtered_df = filtered_df[(filtered_df['Dec 2025 Sales'] == 0) & (filtered_df['Jan 2026 Sales'] > 0)]
    
    filtered_df = filtered_df[filtered_df['Total Sales'] >= min_total_sales]
    filtered_df = filtered_df[filtered_df['Jan 2026 Sales'] >= min_jan_sales]
    
    # ============ KEY METRICS ============
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Products",
            f"{len(filtered_df):,}",
            delta=f"{len(df)} total" if selected_product != 'All Products' else None
        )
    
    with col2:
        total_dec = filtered_df['Dec 2025 Sales'].sum()
        st.metric("Dec 2025 Sales", f"{total_dec:,}")
    
    with col3:
        total_jan = filtered_df['Jan 2026 Sales'].sum()
        growth_pct = ((total_jan - total_dec) / total_dec * 100) if total_dec > 0 else 0
        st.metric("Jan 2026 Sales", f"{total_jan:,}", f"{growth_pct:+.1f}%")
    
    with col4:
        st.metric("Total Sales", f"{filtered_df['Total Sales'].sum():,}")
    
    with col5:
        avg_growth = filtered_df['Growth %'].mean()
        st.metric("Avg Growth", f"{avg_growth:+.1f}%")
    
    st.markdown("---")
    
    # ============ TABS FOR DIFFERENT VIEWS ============
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 Top Performers", 
        "📊 Category Analysis", 
        "📈 Growth Analysis",
        "📋 Detailed Table",
        "🎯 Product Deep Dive"
    ])
    
    # ============ TAB 1: TOP PERFORMERS ============
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🥇 Top 10 by Total Sales")
            top_sales = filtered_df.nlargest(10, 'Total Sales')[['Product', 'Item ID', 'Total Sales', 'Dec 2025 Sales', 'Jan 2026 Sales']]
            
            for idx, row in top_sales.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="product-highlight">
                        <strong>{row['Product'].title()}</strong><br>
                        <small>ID: {row['Item ID']}</small><br>
                        Total: <strong>{row['Total Sales']}</strong> | Dec: {row['Dec 2025 Sales']} | Jan: {row['Jan 2026 Sales']}
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📈 Top 10 Growth (Absolute)")
            top_growth = filtered_df.nlargest(10, 'Growth')[['Product', 'Item ID', 'Growth', 'Growth %', 'Dec 2025 Sales', 'Jan 2026 Sales']]
            
            for idx, row in top_growth.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="product-highlight">
                        <strong>{row['Product'].title()}</strong><br>
                        <small>ID: {row['Item ID']}</small><br>
                        Growth: <strong>+{row['Growth']}</strong> ({row['Growth %']:+.0f}%) | {row['Dec 2025 Sales']} → {row['Jan 2026 Sales']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Top performers chart
        st.markdown("### 📊 Visual Comparison")
        top_10_sales = filtered_df.nlargest(10, 'Total Sales')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Dec 2025',
            x=top_10_sales['Product'],
            y=top_10_sales['Dec 2025 Sales'],
            marker_color='#667eea'
        ))
        fig.add_trace(go.Bar(
            name='Jan 2026',
            x=top_10_sales['Product'],
            y=top_10_sales['Jan 2026 Sales'],
            marker_color='#764ba2'
        ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_tickangle=-45,
            title="Top 10 Products - Monthly Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ============ TAB 2: CATEGORY ANALYSIS ============
    with tab2:
        st.markdown("### 📦 Product Category Performance")
        
        category_stats = filtered_df.groupby('Product').agg({
            'Total Sales': 'sum',
            'Dec 2025 Sales': 'sum',
            'Jan 2026 Sales': 'sum',
            'URL': 'count'
        }).reset_index()
        category_stats.columns = ['Product', 'Total Sales', 'Dec Sales', 'Jan Sales', 'Listings Count']
        category_stats['Avg Sales per Listing'] = (category_stats['Total Sales'] / category_stats['Listings Count']).round(1)
        category_stats = category_stats.sort_values('Total Sales', ascending=False)
        
        # Display table
        st.dataframe(
            category_stats,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Product": st.column_config.TextColumn("Product Category", width="medium"),
                "Total Sales": st.column_config.NumberColumn("Total Sales", format="%d"),
                "Dec Sales": st.column_config.NumberColumn("Dec Sales", format="%d"),
                "Jan Sales": st.column_config.NumberColumn("Jan Sales", format="%d"),
                "Listings Count": st.column_config.NumberColumn("# Listings", format="%d"),
                "Avg Sales per Listing": st.column_config.NumberColumn("Avg/Listing", format="%.1f"),
            }
        )
        
        # Pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                category_stats.head(10),
                values='Total Sales',
                names='Product',
                title='Sales Distribution (Top 10 Categories)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                category_stats.head(15),
                x='Product',
                y='Listings Count',
                title='Number of Listings per Category (Top 15)',
                color='Total Sales',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # ============ TAB 3: GROWTH ANALYSIS ============
    with tab3:
        st.markdown("### 📈 Growth & Trends Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Growth distribution
            growth_bins = pd.cut(
                filtered_df['Growth %'],
                bins=[-float('inf'), -50, -10, 0, 10, 50, float('inf')],
                labels=['Decline >50%', 'Decline 10-50%', 'Decline <10%', 'Growth <10%', 'Growth 10-50%', 'Growth >50%']
            )
            growth_dist = growth_bins.value_counts().sort_index()
            
            fig_growth = px.bar(
                x=growth_dist.index,
                y=growth_dist.values,
                title='Growth Distribution',
                labels={'x': 'Growth Category', 'y': 'Number of Products'},
                color=growth_dist.values,
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        
        with col2:
            # Scatter plot
            fig_scatter = px.scatter(
                filtered_df,
                x='Dec 2025 Sales',
                y='Jan 2026 Sales',
                color='Product',
                size='Total Sales',
                hover_data=['Item ID'],
                title='Dec vs Jan Sales Correlation'
            )
            fig_scatter.add_trace(
                go.Scatter(
                    x=[0, filtered_df['Dec 2025 Sales'].max()],
                    y=[0, filtered_df['Dec 2025 Sales'].max()],
                    mode='lines',
                    name='Equal Performance',
                    line=dict(dash='dash', color='gray')
                )
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Winners and losers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌟 Biggest Winners")
            winners = filtered_df.nlargest(5, 'Growth')[['Product', 'Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Growth', 'Growth %']]
            st.dataframe(winners, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### ⚠️ Biggest Declines")
            losers = filtered_df.nsmallest(5, 'Growth')[['Product', 'Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Growth', 'Growth %']]
            st.dataframe(losers, hide_index=True, use_container_width=True)
    
    # ============ TAB 4: DETAILED TABLE ============
    with tab4:
        st.markdown("### 📋 Complete Product Listing")
        
        # Search box
        search_term = st.text_input("🔍 Search products or Item ID", "")
        
        display_df = filtered_df.copy()
        if search_term:
            display_df = display_df[
                display_df['Product'].str.contains(search_term, case=False) |
                display_df['Item ID'].str.contains(search_term, case=False)
            ]
        
        # Display options
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox("Sort by", ['Total Sales', 'Jan 2026 Sales', 'Growth', 'Growth %', 'Product'])
        with col2:
            sort_order = st.radio("Order", ['Descending', 'Ascending'], horizontal=True)
        with col3:
            show_url = st.checkbox("Show URLs", value=False)
        
        # Sort data
        ascending = (sort_order == 'Ascending')
        display_df = display_df.sort_values(sort_by, ascending=ascending)
        
        # Select columns to display
        columns = ['Product', 'Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth', 'Growth %']
        if show_url:
            columns.append('URL')
        
        st.dataframe(
            display_df[columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("eBay Link"),
                "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                "Total Sales": st.column_config.NumberColumn("Total Sales", format="%d"),
            }
        )
        
        st.info(f"Showing {len(display_df)} of {len(filtered_df)} products")
    
    # ============ TAB 5: PRODUCT DEEP DIVE ============
    with tab5:
        st.markdown("### 🎯 Individual Product Analysis")
        
        selected_product_deep = st.selectbox(
            "Select a product to analyze",
            sorted(df['Product'].unique())
        )
        
        product_data = df[df['Product'] == selected_product_deep]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Listings", len(product_data))
        with col2:
            st.metric("Total Dec Sales", f"{product_data['Dec 2025 Sales'].sum():,}")
        with col3:
            st.metric("Total Jan Sales", f"{product_data['Jan 2026 Sales'].sum():,}")
        with col4:
            avg_growth = product_data['Growth %'].mean()
            st.metric("Avg Growth", f"{avg_growth:+.1f}%")
        
        st.markdown("---")
        
        # Individual listings
        st.markdown("#### All Listings for this Product")
        st.dataframe(
            product_data[['Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth', 'Growth %', 'URL']].sort_values('Total Sales', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("eBay Link"),
                "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
            }
        )
        
        # Distribution chart
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=product_data['Total Sales'],
            name='Sales Distribution',
            nbinsx=20,
            marker_color='#667eea'
        ))
        fig_dist.update_layout(
            title=f'Sales Distribution for {selected_product_deep.title()}',
            xaxis_title='Total Sales',
            yaxis_title='Number of Listings',
            height=300
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # ============ EXPORT OPTIONS ============
    st.markdown("---")
    st.subheader("💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Filtered Data (CSV)",
            data=csv,
            file_name=f"sales_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        summary_csv = category_stats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Category Summary (CSV)",
            data=summary_csv,
            file_name=f"category_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    # Landing page
    st.info("👆 Upload your sales data CSV to get started!")
    
    st.markdown("""
    ### 📊 What this dashboard does:
    
    - **Track Performance**: Monitor sales across December 2025 and January 2026
    - **Identify Winners**: Find your top-performing products
    - **Spot Trends**: Analyze growth patterns and declining products
    - **Category Insights**: Compare performance across product categories
    - **Export Reports**: Download filtered data for further analysis
    
    ### 📁 Expected CSV format:
    ```
    Keyword,Product URL,December 2025 Sales,January 2026 Sales,Date Checked,Status
    silicone pot holders,https://www.ebay.com/itm/174746731680,11,5,2026-01-14 22:52:31,Success
    ```
    """)
