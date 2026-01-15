# 📊 eBay Sales Analytics Dashboard

A powerful Streamlit dashboard for tracking and analyzing eBay product sales performance across multiple months.

## 🌟 Features

- **Multi-Month Comparison**: Track sales across December 2025 & January 2026
- **Top Performers**: Identify best-selling products instantly
- **Category Analysis**: Compare product categories with interactive charts
- **Growth Tracking**: Spot trending and declining products
- **Deep Dive Analytics**: Analyze individual product performance
- **Export Reports**: Download filtered data as CSV

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Umer-K/ebay-sales-analytics.git
cd ebay-sales-analytics
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## 📁 Data Format

Upload a CSV file with this format:
```csv
Keyword,Product URL,December 2025 Sales,January 2026 Sales,Date Checked,Status
silicone pot holders,https://www.ebay.com/itm/174746731680,11,5,2026-01-14 22:52:31,Success
oil mister,https://www.ebay.com/itm/186029362678,11,5,2026-01-15 08:03:19,Success
```

## 📊 Dashboard Tabs

1. **Top Performers** - View top 10 products by sales and growth
2. **Category Analysis** - Product category performance metrics
3. **Growth Analysis** - Identify winners, losers, and trends
4. **Detailed Table** - Searchable, sortable complete data
5. **Product Deep Dive** - Individual product analysis

## 🎯 Use Cases

- Track product performance month-over-month
- Identify trending products for inventory decisions
- Analyze category performance
- Export data for reporting
- Monitor competitor listings

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) - Web framework
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [Plotly](https://plotly.com/) - Interactive visualizations

## 📝 License

MIT License - feel free to use this project!

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📧 Contact

For questions or suggestions, open an issue on GitHub.
