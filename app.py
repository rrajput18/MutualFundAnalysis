import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Mutual Fund Analytics Platform", layout="wide")

db_path = Path("data/db/bluestock_mf.db")

@st.cache_data
def load_all_dashboard_data():
    conn = sqlite3.connect(db_path)
    
    # 1. Page 1 (Industry Overview) Queries
    aum = pd.read_sql_query("SELECT * FROM fact_aum", conn)
    sip = pd.read_sql_query("SELECT * FROM fact_sip_industry", conn)
    
    latest_aum_val = pd.read_sql_query(
        "SELECT SUM(aum_lakh_crore) as total_aum FROM fact_aum WHERE date = (SELECT MAX(date) FROM fact_aum)", 
        conn
    )['total_aum'].iloc[0]
    
    latest_sip_row = pd.read_sql_query(
        "SELECT sip_inflow_crore, month FROM fact_sip_industry WHERE month = (SELECT MAX(month) FROM fact_sip_industry)", 
        conn
    ).iloc[0]
    
    latest_folio_val = pd.read_sql_query(
        "SELECT total_folios_crore FROM fact_folio_count WHERE month = (SELECT MAX(month) FROM fact_folio_count)", 
        conn
    )['total_folios_crore'].iloc[0]
    
    latest_schemes_val = pd.read_sql_query(
        "SELECT SUM(num_schemes) as total_schemes FROM fact_aum WHERE date = (SELECT MAX(date) FROM fact_aum)", 
        conn
    )['total_schemes'].iloc[0]
    
    # 2. Page 2 (Fund Performance) Queries
    funds = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    performance = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    
    # 3. Page 3 (Investor Analytics) Queries
    transactions = pd.read_sql_query(
        "SELECT amount_inr, gender, age_group, transaction_type, state, city_tier FROM fact_transactions", 
        conn
    )
    
    # 4. Page 4 (SIP & Market Trends) Queries
    combo_query = """
        WITH monthly_nifty AS (
            SELECT SUBSTR(date, 1, 7) AS month, AVG(close_value) AS avg_nifty_close
            FROM fact_benchmarks
            WHERE index_name = 'NIFTY50'
            GROUP BY month
        )
        SELECT s.month, s.sip_inflow_crore, ROUND(n.avg_nifty_close, 2) AS avg_nifty_close
        FROM fact_sip_industry s
        JOIN monthly_nifty n ON s.month = n.month
        ORDER BY s.month
    """
    combo_df = pd.read_sql_query(combo_query, conn)
    # Parse month column to datetime for proper time-series rendering on charts
    combo_df['month_dt'] = pd.to_datetime(combo_df['month'] + '-01')
    
    category_inflows = pd.read_sql_query("SELECT month, category, net_inflow_crore FROM fact_category_inflows", conn)
    
    conn.close()
    
    return {
        "aum": aum,
        "sip": sip,
        "latest_aum_val": latest_aum_val,
        "latest_sip_row": latest_sip_row,
        "latest_folio_val": latest_folio_val,
        "latest_schemes_val": latest_schemes_val,
        "funds": funds,
        "performance": performance,
        "transactions": transactions,
        "combo_df": combo_df,
        "category_inflows": category_inflows
    }

if not db_path.exists():
    st.error("SQLite Database not found! Please run the Day 2 Cleaning & DB Load notebook (`02_data_cleaning.ipynb`) first to populate the SQLite database.")
else:
    try:
        # Load all data
        data = load_all_dashboard_data()
        
        # Navigation
        st.sidebar.title("📊 MF Analytics Platform")
        page = st.sidebar.radio(
            "Navigate Pages", 
            ["Industry Overview", "Fund Performance", "Investor Analytics", "SIP & Market Trends"]
        )
        st.sidebar.markdown("---")
        
        # ==============================================================
        # PAGE 1: INDUSTRY OVERVIEW
        # ==============================================================
        if page == "Industry Overview":
            st.title("📈 Mutual Fund Industry Overview")
            st.markdown("---")
            
            # KPI Cards
            col1, col2, col3, col4 = st.columns(4)
            
            try:
                month_dt = pd.to_datetime(data['latest_sip_row']['month'] + "-01")
                month_label = month_dt.strftime("%b %Y")
            except Exception:
                month_label = data['latest_sip_row']['month']
                
            col1.metric("Industry Folios", f"{data['latest_folio_val']:.2f} Cr")
            col2.metric("Total Industry AUM", f"₹{data['latest_aum_val']:.2f} Lakh Cr")
            col3.metric("Total Schemes", f"{int(data['latest_schemes_val']):,}")
            col4.metric(f"SIP Inflow ({month_label})", f"₹{data['latest_sip_row']['sip_inflow_crore']:,.0f} Cr")
            st.markdown("---")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("AUM Growth Trend by Fund House")
                fig_aum = px.line(
                    data['aum'], 
                    x='date', 
                    y='aum_crore', 
                    color='fund_house',
                    labels={
                        'aum_crore': 'AUM (₹ Crores)', 
                        'date': 'Reporting Date', 
                        'fund_house': 'Fund House'
                    }
                )
                st.plotly_chart(fig_aum, use_container_width=True)
                
            with col_right:
                st.subheader("Total AUM by Fund House (Latest)")
                latest_aum = data['aum'][data['aum']['date'] == data['aum']['date'].max()].sort_values('aum_crore', ascending=False)
                fig_bar = px.bar(
                    latest_aum, 
                    x='aum_crore', 
                    y='fund_house', 
                    orientation='h',
                    labels={
                        'aum_crore': 'AUM (₹ Crores)', 
                        'fund_house': 'Fund House'
                    },
                    color='aum_crore',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        # ==============================================================
        # PAGE 2: FUND PERFORMANCE
        # ==============================================================
        elif page == "Fund Performance":
            st.title("🏆 Mutual Fund Scheme Performance")
            st.markdown("---")
            
            # Interactive Filters on Sidebar
            st.sidebar.subheader("Performance Filters")
            
            fh_list = sorted(data['performance']['fund_house'].unique())
            selected_fh = st.sidebar.multiselect("Select Fund House", fh_list, default=fh_list[:3])
            
            cat_list = sorted(data['performance']['category'].unique())
            selected_cat = st.sidebar.multiselect("Select Category", cat_list, default=cat_list)
            
            plan_list = sorted(data['performance']['plan'].unique())
            selected_plan = st.sidebar.multiselect("Select Plan Option", plan_list, default=plan_list)
            
            # Apply Filters
            filtered_perf = data['performance'][
                (data['performance']['fund_house'].isin(selected_fh)) &
                (data['performance']['category'].isin(selected_cat)) &
                (data['performance']['plan'].isin(selected_plan))
            ]
            
            col_left, col_right = st.columns([3, 2])
            
            with col_left:
                st.subheader("Risk vs Return Scatter Analysis")
                if not filtered_perf.empty:
                    fig_scatter = px.scatter(
                        filtered_perf,
                        x='std_dev_ann_pct',
                        y='return_3yr_pct',
                        size='aum_crore',
                        color='scheme_name',
                        hover_name='scheme_name',
                        labels={
                            'std_dev_ann_pct': 'Annualized Volatility / Risk (%)',
                            'return_3yr_pct': '3-Year CAGR Return (%)',
                            'aum_crore': 'Scheme AUM (₹ Crores)'
                        }
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("No performance records match the selected filters.")
                    
            with col_right:
                st.subheader("Daily NAV Trend Comparison")
                if not filtered_perf.empty:
                    schemes_list = sorted(filtered_perf['scheme_name'].unique())
                    default_schemes = schemes_list[:2] if len(schemes_list) >= 2 else schemes_list
                    selected_schemes = st.multiselect(
                        "Choose Schemes to compare", 
                        schemes_list, 
                        default=default_schemes
                    )
                    
                    if selected_schemes:
                        conn = sqlite3.connect(db_path)
                        nav_query = f"""
                            SELECT n.date, f.scheme_name, n.nav
                            FROM fact_nav n
                            JOIN dim_fund f ON n.amfi_code = f.amfi_code
                            WHERE f.scheme_name IN ({','.join(['?']*len(selected_schemes))})
                            ORDER BY n.date
                        """
                        nav_df = pd.read_sql_query(nav_query, conn, params=selected_schemes)
                        conn.close()
                        
                        fig_nav = px.line(
                            nav_df,
                            x='date',
                            y='nav',
                            color='scheme_name',
                            labels={
                                'nav': 'Net Asset Value (INR)',
                                'date': 'Date',
                                'scheme_name': 'Scheme Name'
                            }
                        )
                        st.plotly_chart(fig_nav, use_container_width=True)
                    else:
                        st.info("Select at least one scheme to compare daily NAVs.")
                else:
                    st.warning("No schemes available for NAV plotting.")
            
            st.subheader("Scheme Scorecard Grid")
            if not filtered_perf.empty:
                grid_df = filtered_perf[[
                    'scheme_name', 'return_3yr_pct', 'sharpe_ratio', 
                    'sortino_ratio', 'expense_ratio_pct', 'morningstar_rating'
                ]].copy().rename(columns={
                    'scheme_name': 'Scheme Name',
                    'return_3yr_pct': '3-Yr Return (%)',
                    'sharpe_ratio': 'Sharpe Ratio',
                    'sortino_ratio': 'Sortino Ratio',
                    'expense_ratio_pct': 'Expense Ratio (%)',
                    'morningstar_rating': 'Morningstar Rating'
                })
                st.dataframe(grid_df, use_container_width=True)
            else:
                st.warning("No scheme details to show.")

        # ==============================================================
        # PAGE 3: INVESTOR ANALYTICS
        # ==============================================================
        elif page == "Investor Analytics":
            st.title("👥 Investor Demographics & Transaction Analytics")
            st.markdown("---")
            
            # Interactive Filters on Sidebar
            st.sidebar.subheader("Investor Filters")
            
            tier_list = sorted(data['transactions']['city_tier'].unique())
            selected_tier = st.sidebar.multiselect("Select City Tier", tier_list, default=tier_list)
            
            state_list = sorted(data['transactions']['state'].unique())
            selected_state = st.sidebar.multiselect("Select State", state_list, default=state_list)
            
            age_list = sorted(data['transactions']['age_group'].unique())
            selected_age = st.sidebar.multiselect("Select Age Group", age_list, default=age_list)
            
            # Apply Filters
            filtered_tx = data['transactions'][
                (data['transactions']['city_tier'].isin(selected_tier)) &
                (data['transactions']['state'].isin(selected_state)) &
                (data['transactions']['age_group'].isin(selected_age))
            ]
            
            if not filtered_tx.empty:
                col_c1, col_c2, col_c3 = st.columns(3)
                
                with col_c1:
                    st.subheader("Investment by Gender")
                    gender_df = filtered_tx.groupby('gender', as_index=False)['amount_inr'].sum()
                    fig_gen = px.pie(gender_df, values='amount_inr', names='gender', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_gen, use_container_width=True)
                    
                with col_c2:
                    st.subheader("Investment by Age Group")
                    age_df = filtered_tx.groupby('age_group', as_index=False)['amount_inr'].sum()
                    fig_age = px.pie(age_df, values='amount_inr', names='age_group', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                    st.plotly_chart(fig_age, use_container_width=True)
                    
                with col_c3:
                    st.subheader("Investment by Transaction Type")
                    type_df = filtered_tx.groupby('transaction_type', as_index=False)['amount_inr'].sum()
                    fig_type = px.pie(type_df, values='amount_inr', names='transaction_type', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                    st.plotly_chart(fig_type, use_container_width=True)
                
                st.markdown("---")
                st.subheader("Invested Value by State (Top 12)")
                state_df = filtered_tx.groupby('state', as_index=False)['amount_inr'].sum().sort_values('amount_inr', ascending=False).head(12)
                fig_state = px.bar(
                    state_df,
                    x='amount_inr',
                    y='state',
                    orientation='h',
                    labels={
                        'amount_inr': 'Total Invested Amount (₹ INR)',
                        'state': 'State'
                    },
                    color='amount_inr',
                    color_continuous_scale='Viridis'
                )
                fig_state.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_state, use_container_width=True)
            else:
                st.warning("No transactions match the selected filter combinations.")

        # ==============================================================
        # PAGE 4: SIP & MARKET TRENDS
        # ==============================================================
        elif page == "SIP & Market Trends":
            st.title("📊 SIP Inflows & Benchmark Market Trends")
            st.markdown("---")
            
            # Prepare data
            inflows = data['category_inflows'].copy()
            inflows['Year'] = inflows['month'].str.split('-').str[0]
            
            col_l, col_r = st.columns([3, 2])
            
            with col_l:
                st.subheader("SIP Inflow Volumes vs Nifty 50 Close Value")
                fig_combo = go.Figure()
                
                # Add Bar chart for SIP inflows
                fig_combo.add_trace(
                    go.Bar(
                        x=data['combo_df']['month_dt'],
                        y=data['combo_df']['sip_inflow_crore'],
                        name='SIP Inflow (₹ Crores)',
                        marker_color='#3b82f6',
                        yaxis='y'
                    )
                )
                
                # Add Line chart for Nifty 50 close
                fig_combo.add_trace(
                    go.Scatter(
                        x=data['combo_df']['month_dt'],
                        y=data['combo_df']['avg_nifty_close'],
                        name='Avg Nifty 50 Close',
                        line=dict(color='#f59e0b', width=3),
                        yaxis='y2'
                    )
                )
                
                fig_combo.update_layout(
                    xaxis=dict(
                        title=dict(text="Month"),
                        tickformat="%b\n%Y",
                        dtick="M6"  # Show ticks every 6 months to prevent label overlap
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Monthly SIP Inflow (₹ Crores)",
                            font=dict(color="#3b82f6")
                        ),
                        tickfont=dict(color="#3b82f6")
                    ),
                    yaxis2=dict(
                        title=dict(
                            text="Avg Nifty 50 Close Value",
                            font=dict(color="#f59e0b")
                        ),
                        tickfont=dict(color="#f59e0b"),
                        anchor="x",
                        overlaying="y",
                        side="right"
                    ),
                    legend=dict(x=0.01, y=0.99)
                )
                st.plotly_chart(fig_combo, use_container_width=True)
                
            with col_r:
                st.subheader("Net Category Inflows Pivot Table (₹ Crores)")
                
                pivot = inflows.pivot_table(
                    index='category',
                    columns='Year',
                    values='net_inflow_crore',
                    aggfunc='sum',
                    margins=True,
                    margins_name='Total'
                ).fillna(0)
                
                # Format numeric columns as integer crores with commas
                st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)
                
                st.markdown("---")
                st.subheader("Cumulative Net Inflow by Category")
                cat_totals = inflows.groupby('category', as_index=False)['net_inflow_crore'].sum().sort_values('net_inflow_crore', ascending=False)
                fig_cat = px.bar(
                    cat_totals,
                    x='category',
                    y='net_inflow_crore',
                    labels={
                        'net_inflow_crore': 'Net Inflows (₹ Crores)',
                        'category': 'Category'
                    },
                    color='net_inflow_crore',
                    color_continuous_scale='Tealgrn'
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("Ensure the database exists and that it has been populated by the Day 2 notebook.")
