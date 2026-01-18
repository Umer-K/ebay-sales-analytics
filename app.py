import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

st.set_page_config(page_title="eBay Sales Analytics Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .product-highlight {
        background-color: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #262730;
    }
    </style>
    """, unsafe_allow_html=True)

def parse_sales_data(file_content):
    import io
    
    try:
        df = pd.read_csv(io.StringIO(file_content), header=None, on_bad_lines='skip', engine='python')
        
        if df.iloc[0, 0] and isinstance(df.iloc[0, 0], str) and 'keyword' in df.iloc[0, 0].lower():
            df = df.iloc[1:]
        
        df = df.reset_index(drop=True)
        num_cols = len(df.columns)
        
        has_price = False
        if num_cols >= 7 and len(df) > 0:
            sample = df.iloc[:min(10, len(df)), 2].astype(str)
            dollar_count = 0
            for val in sample:
                if '$' in str(val):
                    dollar_count += 1
            if dollar_count >= 3:
                has_price = True
        
        if has_price and num_cols >= 7:
            df.columns = ['Product', 'URL', 'Price', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked', 'Status'] + [f'Extra_{i}' for i in range(num_cols - 7)]
        elif num_cols >= 6:
            df.columns = ['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked', 'Status'] + [f'Extra_{i}' for i in range(num_cols - 6)]
            df['Price'] = 0.0
        else:
            df.columns = ['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Date Checked'] + [f'Extra_{i}' for i in range(num_cols - 5)]
            df['Price'] = 0.0
            df['Status'] = 'N/A'
        
        df['Dec 2025 Sales'] = pd.to_numeric(df['Dec 2025 Sales'], errors='coerce').fillna(0).astype(int)
        df['Jan 2026 Sales'] = pd.to_numeric(df['Jan 2026 Sales'], errors='coerce').fillna(0).astype(int)
        
        if 'Price' in df.columns:
            df['Price'] = df['Price'].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).astype(float)
        
        df['Total Sales'] = df['Dec 2025 Sales'] + df['Jan 2026 Sales']
        df['Growth'] = df['Jan 2026 Sales'] - df['Dec 2025 Sales']
        df['Growth %'] = df.apply(
            lambda row: ((row['Jan 2026 Sales'] - row['Dec 2025 Sales']) / row['Dec 2025 Sales'] * 100) 
            if row['Dec 2025 Sales'] > 0 
            else (100 if row['Jan 2026 Sales'] > 0 else 0),
            axis=1
        )
        
        df['Dec Revenue'] = df['Dec 2025 Sales'] * df['Price']
        df['Jan Revenue'] = df['Jan 2026 Sales'] * df['Price']
        df['Total Revenue'] = df['Total Sales'] * df['Price']
        df['Revenue Growth'] = df['Jan Revenue'] - df['Dec Revenue']
        
        df['Item ID'] = df['URL'].apply(
            lambda x: re.search(r'/itm/(\d+)', str(x)).group(1) if re.search(r'/itm/(\d+)', str(x)) else 'N/A'
        )
        
        df['Product'] = df['Product'].astype(str).str.strip()
        df['URL'] = df['URL'].astype(str).str.strip()
        df['Date Checked'] = df['Date Checked'].astype(str)
        df['Status'] = df['Status'].astype(str)
        
        df = df[df['URL'].str.contains('ebay.com', na=False)]
        
        return df[['Product', 'URL', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Price', 'Total Sales', 'Growth', 'Growth %', 
                   'Dec Revenue', 'Jan Revenue', 'Total Revenue', 'Revenue Growth', 'Date Checked', 'Status', 'Item ID']]
        
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return pd.DataFrame()

st.title("📊 eBay Sales Analytics Dashboard")
st.markdown("*Track and analyze product performance across December 2025 & January 2026*")
st.markdown("---")

uploaded_file = st.file_uploader("📁 Upload your sales data (CSV/TXT)", type=['csv', 'txt'])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode('utf-8')
    df = parse_sales_data(content)
    
    if df.empty:
        st.error("No valid data found in the uploaded file.")
    else:
        st.sidebar.header("🔍 Filters")
        
        products = ['All Products'] + sorted(df['Product'].unique().tolist())
        selected_product = st.sidebar.selectbox("Filter by Product", products)
        
        performance_filter = st.sidebar.selectbox(
            "Performance Type",
            ["All", "Growing (Jan > Dec)", "Declining (Jan < Dec)", "No Sales", "New Sales (Dec=0, Jan>0)"]
        )
        
        st.sidebar.markdown("### Sales Range")
        min_total_sales = st.sidebar.number_input("Min Total Sales", 0, int(df['Total Sales'].max()), 0)
        min_jan_sales = st.sidebar.number_input("Min Jan Sales", 0, int(df['Jan 2026 Sales'].max()), 0)
        
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
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_price = filtered_df['Price'].mean()
            st.metric("Avg Price", f"${avg_price:.2f}")
        
        with col2:
            total_dec_rev = filtered_df['Dec Revenue'].sum()
            st.metric("Dec Revenue", f"${total_dec_rev:,.2f}")
        
        with col3:
            total_jan_rev = filtered_df['Jan Revenue'].sum()
            rev_growth = ((total_jan_rev - total_dec_rev) / total_dec_rev * 100) if total_dec_rev > 0 else 0
            st.metric("Jan Revenue", f"${total_jan_rev:,.2f}", f"{rev_growth:+.1f}%")
        
        with col4:
            total_revenue = filtered_df['Total Revenue'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        with col5:
            revenue_growth = filtered_df['Revenue Growth'].sum()
            st.metric("Revenue Growth", f"${revenue_growth:+,.2f}")
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏆 Top Performers", 
            "📊 Category Analysis", 
            "📈 Growth Analysis",
            "💰 Revenue Analysis",
            "📋 Detailed Table",
            "🎯 Product Deep Dive"
        ])
        
        with tab1:
            st.markdown("### 🏆 Top Performers")
            top_n = st.selectbox("Show Top:", [10, 20, 30, 40, 50, 100], index=0, key="top_n_selector")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### 🥇 Top {top_n} by Total Sales")
                top_sales = filtered_df.nlargest(top_n, 'Total Sales')[['Product', 'Item ID', 'Total Sales', 'Price', 'Total Revenue', 'Dec 2025 Sales', 'Jan 2026 Sales']]
                
                for idx, row in top_sales.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="product-highlight">
                            <strong>{row['Product'].title()}</strong><br>
                            <small>ID: {row['Item ID']} | Price: ${row['Price']:.2f}</small><br>
                            Total: <strong>{row['Total Sales']}</strong> sales | Revenue: <strong>${row['Total Revenue']:,.2f}</strong><br>
                            Dec: {row['Dec 2025 Sales']} | Jan: {row['Jan 2026 Sales']}
                        </div>
                        """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"### 📈 Top {top_n} Growth (Absolute)")
                top_growth = filtered_df.nlargest(top_n, 'Growth')[['Product', 'Item ID', 'Growth', 'Growth %', 'Dec 2025 Sales', 'Jan 2026 Sales']]
                
                for idx, row in top_growth.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="product-highlight">
                            <strong>{row['Product'].title()}</strong><br>
                            <small>ID: {row['Item ID']}</small><br>
                            Growth: <strong>+{row['Growth']}</strong> ({row['Growth %']:+.0f}%) | {row['Dec 2025 Sales']} → {row['Jan 2026 Sales']}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("### 📊 Visual Comparison")
            
            chart_limit = min(top_n, 20)
            if top_n > 20:
                st.info(f"📊 Chart showing top {chart_limit} for readability. Full list of {top_n} shown above.")
            
            top_n_sales = filtered_df.nlargest(chart_limit, 'Total Sales')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Dec 2025',
                x=top_n_sales['Product'],
                y=top_n_sales['Dec 2025 Sales'],
                marker_color='#667eea'
            ))
            fig.add_trace(go.Bar(
                name='Jan 2026',
                x=top_n_sales['Product'],
                y=top_n_sales['Jan 2026 Sales'],
                marker_color='#764ba2'
            ))
            
            fig.update_layout(
                barmode='group',
                height=400,
                xaxis_tickangle=-45,
                title=f"Top {chart_limit} Products - Monthly Comparison"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown("### 📦 Product Category Performance")
            
            category_stats = filtered_df.groupby('Product').agg({
                'Total Sales': 'sum',
                'Dec 2025 Sales': 'sum',
                'Jan 2026 Sales': 'sum',
                'Total Revenue': 'sum',
                'Dec Revenue': 'sum',
                'Jan Revenue': 'sum',
                'Price': 'mean',
                'URL': 'count'
            }).reset_index()
            category_stats.columns = ['Product', 'Total Sales', 'Dec Sales', 'Jan Sales', 'Total Revenue', 'Dec Revenue', 'Jan Revenue', 'Avg Price', 'Listings Count']
            category_stats['Avg Sales per Listing'] = (category_stats['Total Sales'] / category_stats['Listings Count']).round(1)
            category_stats['Avg Revenue per Listing'] = (category_stats['Total Revenue'] / category_stats['Listings Count']).round(2)
            category_stats = category_stats.sort_values('Total Sales', ascending=False)
            
            st.dataframe(
                category_stats,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Product": st.column_config.TextColumn("Product Category", width="medium"),
                    "Total Sales": st.column_config.NumberColumn("Total Sales", format="%d"),
                    "Dec Sales": st.column_config.NumberColumn("Dec Sales", format="%d"),
                    "Jan Sales": st.column_config.NumberColumn("Jan Sales", format="%d"),
                    "Total Revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
                    "Dec Revenue": st.column_config.NumberColumn("Dec Revenue", format="$%.2f"),
                    "Jan Revenue": st.column_config.NumberColumn("Jan Revenue", format="$%.2f"),
                    "Avg Price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
                    "Listings Count": st.column_config.NumberColumn("# Listings", format="%d"),
                    "Avg Sales per Listing": st.column_config.NumberColumn("Avg Sales/Listing", format="%.1f"),
                    "Avg Revenue per Listing": st.column_config.NumberColumn("Avg Revenue/Listing", format="$%.2f"),
                }
            )
            
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
        
        with tab3:
            st.markdown("### 📈 Growth & Trends Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🌟 Biggest Winners")
                winners = filtered_df.nlargest(5, 'Growth')[['Product', 'Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Growth', 'Growth %']]
                st.dataframe(winners, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown("#### ⚠️ Biggest Declines")
                losers = filtered_df.nsmallest(5, 'Growth')[['Product', 'Item ID', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Growth', 'Growth %']]
                st.dataframe(losers, hide_index=True, use_container_width=True)
        
        with tab4:
            st.markdown("### 💰 Revenue & Pricing Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💎 Top 10 Revenue Generators")
                top_revenue = filtered_df.nlargest(10, 'Total Revenue')[['Product', 'Item ID', 'Price', 'Total Sales', 'Total Revenue']]
                st.dataframe(
                    top_revenue,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "Total Revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
                    }
                )
                
                st.markdown("#### 💵 Revenue by Price Range")
                price_bins = pd.cut(
                    filtered_df['Price'],
                    bins=[0, 10, 25, 50, 100, float('inf')],
                    labels=['$0-10', '$10-25', '$25-50', '$50-100', '$100+']
                )
                revenue_by_price = filtered_df.groupby(price_bins)['Total Revenue'].sum().reset_index()
                revenue_by_price.columns = ['Price Range', 'Revenue']
                
                fig_price_revenue = px.bar(
                    revenue_by_price,
                    x='Price Range',
                    y='Revenue',
                    title='Total Revenue by Price Range',
                    color='Revenue',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig_price_revenue, use_container_width=True)
            
            with col2:
                st.markdown("#### 📊 Price vs Sales Relationship")
                fig_price_scatter = px.scatter(
                    filtered_df,
                    x='Price',
                    y='Total Sales',
                    color='Product',
                    size='Total Revenue',
                    hover_data=['Item ID', 'Total Revenue'],
                    title='Price Impact on Sales Volume'
                )
                st.plotly_chart(fig_price_scatter, use_container_width=True)
                
                st.markdown("#### 📈 Top 10 Revenue Growth")
                top_rev_growth = filtered_df.nlargest(10, 'Revenue Growth')[['Product', 'Item ID', 'Price', 'Dec Revenue', 'Jan Revenue', 'Revenue Growth']]
                st.dataframe(
                    top_rev_growth,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "Dec Revenue": st.column_config.NumberColumn("Dec Revenue", format="$%.2f"),
                        "Jan Revenue": st.column_config.NumberColumn("Jan Revenue", format="$%.2f"),
                        "Revenue Growth": st.column_config.NumberColumn("Revenue Growth", format="$%.2f"),
                    }
                )
            
            st.markdown("---")
            st.markdown("#### 💡 Revenue Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                high_price_sales = filtered_df[filtered_df['Price'] > 50]['Total Sales'].sum()
                high_price_revenue = filtered_df[filtered_df['Price'] > 50]['Total Revenue'].sum()
                st.metric("Premium Products ($50+)", f"{high_price_sales:,} sales", f"${high_price_revenue:,.2f} revenue")
            
            with col2:
                mid_price_sales = filtered_df[(filtered_df['Price'] >= 25) & (filtered_df['Price'] <= 50)]['Total Sales'].sum()
                mid_price_revenue = filtered_df[(filtered_df['Price'] >= 25) & (filtered_df['Price'] <= 50)]['Total Revenue'].sum()
                st.metric("Mid-Range ($25-50)", f"{mid_price_sales:,} sales", f"${mid_price_revenue:,.2f} revenue")
            
            with col3:
                low_price_sales = filtered_df[filtered_df['Price'] < 25]['Total Sales'].sum()
                low_price_revenue = filtered_df[filtered_df['Price'] < 25]['Total Revenue'].sum()
                st.metric("Budget (<$25)", f"{low_price_sales:,} sales", f"${low_price_revenue:,.2f} revenue")
        
        with tab5:
            st.markdown("### 📋 Complete Product Listing")
            
            search_term = st.text_input("🔍 Search products or Item ID", "")
            
            display_df = filtered_df.copy()
            if search_term:
                display_df = display_df[
                    display_df['Product'].str.contains(search_term, case=False) |
                    display_df['Item ID'].str.contains(search_term, case=False)
                ]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                sort_by = st.selectbox("Sort by", ['Total Sales', 'Total Revenue', 'Jan 2026 Sales', 'Growth', 'Growth %', 'Price', 'Product'])
            with col2:
                sort_order = st.radio("Order", ['Descending', 'Ascending'], horizontal=True)
            with col3:
                show_url = st.checkbox("Show URLs", value=False)
            
            ascending = (sort_order == 'Ascending')
            display_df = display_df.sort_values(sort_by, ascending=ascending)
            
            columns = ['Product', 'Item ID', 'Price', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth', 'Growth %', 'Total Revenue']
            if show_url:
                columns.append('URL')
            
            st.dataframe(
                display_df[columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("eBay Link"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                    "Total Sales": st.column_config.NumberColumn("Total Sales", format="%d"),
                    "Total Revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
                }
            )
            
            st.info(f"Showing {len(display_df)} of {len(filtered_df)} products")
        
        with tab6:
            st.markdown("### 🎯 Individual Product Analysis")
            
            selected_product_deep = st.selectbox(
                "Select a product to analyze",
                sorted(df['Product'].unique())
            )
            
            product_data = df[df['Product'] == selected_product_deep]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Listings", len(product_data))
            with col2:
                st.metric("Total Dec Sales", f"{product_data['Dec 2025 Sales'].sum():,}")
            with col3:
                st.metric("Total Jan Sales", f"{product_data['Jan 2026 Sales'].sum():,}")
            with col4:
                avg_growth = product_data['Growth %'].mean()
                st.metric("Avg Growth", f"{avg_growth:+.1f}%")
            with col5:
                total_revenue = product_data['Total Revenue'].sum()
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_price = product_data['Price'].mean()
                st.metric("Avg Price", f"${avg_price:.2f}")
            with col2:
                min_price = product_data['Price'].min()
                st.metric("Min Price", f"${min_price:.2f}")
            with col3:
                max_price = product_data['Price'].max()
                st.metric("Max Price", f"${max_price:.2f}")
            with col4:
                revenue_growth = product_data['Revenue Growth'].sum()
                st.metric("Revenue Growth", f"${revenue_growth:+,.2f}")
            
            st.markdown("---")
            
            st.markdown("#### All Listings for this Product")
            st.dataframe(
                product_data[['Item ID', 'Price', 'Dec 2025 Sales', 'Jan 2026 Sales', 'Total Sales', 'Growth', 'Growth %', 'Total Revenue', 'URL']].sort_values('Total Revenue', ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("eBay Link"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                    "Total Revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
                }
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_sales_dist = go.Figure()
                fig_sales_dist.add_trace(go.Histogram(
                    x=product_data['Total Sales'],
                    name='Sales Distribution',
                    nbinsx=20,
                    marker_color='#667eea'
                ))
                fig_sales_dist.update_layout(
                    title=f'Sales Distribution for {selected_product_deep.title()}',
                    xaxis_title='Total Sales',
                    yaxis_title='Number of Listings',
                    height=300
                )
                st.plotly_chart(fig_sales_dist, use_container_width=True)
            
            with col2:
                fig_price_dist = go.Figure()
                fig_price_dist.add_trace(go.Histogram(
                    x=product_data['Price'],
                    name='Price Distribution',
                    nbinsx=20,
                    marker_color='#764ba2'
                ))
                fig_price_dist.update_layout(
                    title=f'Price Distribution for {selected_product_deep.title()}',
                    xaxis_title='Price ($)',
                    yaxis_title='Number of Listings',
                    height=300
                )
                st.plotly_chart(fig_price_dist, use_container_width=True)
        
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
    st.info("👆 Upload your sales data CSV to get started!")
    
    st.markdown("""
    ### 📊 What this dashboard does:
    
    - Track Performance across December 2025 and January 2026
    - Revenue Analytics with pricing and profitability metrics
    - Identify top-performing products by sales and revenue
    - Analyze growth patterns and declining products
    - Compare performance across product categories
    - Export reports for further analysis
    
    ### 📁 CSV Format:
    Your CSV can have price or no price - both work!
    """)
