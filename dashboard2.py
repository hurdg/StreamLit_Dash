import requests
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as pls
import altair as alt
import datetime as dt
import yfinance as yf

from EDGAR_functions import EDGAR_query, EDGAR_gettag, EDGAR_q4df
from inventory_plot import create_inventory_chart
from pe_plot import trailing_pe_plot, forward_pe_plot

#################################################################################################################################
##################################### Page Configuration ########################################################################
#################################################################################################################################
#basic configuration
st.set_page_config(
    page_title="Ticker Trends",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

#Get data for dropdown/title
header = {'User-Agent':'gavinhurd11@gmail.com'}
tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
tickers_cik['cik_str']=tickers_cik['cik_str'].astype(str).str.zfill(10)

#Company Dropdown
selected_title = st.sidebar.selectbox('Ticker', options = tickers_cik['title'])
cik_str = tickers_cik['cik_str'][tickers_cik['title'] == selected_title].values[0]
selected_ticker = tickers_cik['ticker'][tickers_cik['title'] == selected_title].values[0]

#Page title
st.header(f"{selected_ticker}: _{selected_title}_", divider = True)

tab1, tab2, tab3 = st.tabs(["Key Metrics", "Income Statement", "Balance Sheet"])

#################################################################################################################################
######################################### Data Wrangling ########################################################################
#################################################################################################################################
#Load data of selected company
df = EDGAR_query(cik_str, header = header)


###########################################
#Wrangle dataframe and create income_statement db (Q and K), balance_sheet db, and historical price db
df[["start", 'end']] = df[["start", 'end']].apply(pd.to_datetime, errors='coerce', utc=False)
df.dropna(subset=['frame', 'val'], inplace = True) 
###########################################


###########################################
balance_sheet = df[df['start'].isnull()]
###########################################


###########################################
income_state = df.dropna(subset=['start'])
income_state.sort_values(['tag', 'end', 'start'], inplace = True) 
income_state.reset_index(inplace = True)
income_state.drop(columns = ['index'], inplace = True)
quarterly_income_statement = income_state.apply(EDGAR_q4df, full_df = df, axis=1)
annual_income_statement = income_state[income_state['frame'].str.contains('k', case = False)]
###########################################


###########################################
df_hist = yf.Ticker('UG')
historical_price = df_hist.history(period="max")
historical_price.reset_index(inplace = True)
historical_price["Date"] = historical_price["Date"].dt.tz_localize(tz = None)
historical_price = historical_price[historical_price["Date"] > (min(quarterly_income_statement['start']))]
###########################################

#################################################################################################################################
################################################### Tab 1: Key Metrics ##########################################################
#################################################################################################################################

###############################################
inc_tag = EDGAR_gettag('netincome', quarterly_income_statement['tag'])
sharesoutstanding_tag = EDGAR_gettag('sharesoutstanding', balance_sheet['tag'])

newest_q_dates = pd.Series.nlargest((quarterly_income_statement['end'][quarterly_income_statement['tag']==inc_tag]),4)
newest_sharesoutstanding = balance_sheet['val'][(balance_sheet['tag']==sharesoutstanding_tag) & (balance_sheet['end']== max(newest_q_dates))].mean()

newest_k_profit = quarterly_income_statement['val'][(quarterly_income_statement['tag']==inc_tag) & (quarterly_income_statement['end'].isin(newest_q_dates))].sum()
newest_q_profit = quarterly_income_statement['val'][(quarterly_income_statement['tag']==inc_tag) & (quarterly_income_statement['end']== max(newest_q_dates))].sum()
newest_price = historical_price['Close'][historical_price["Date"]==max(historical_price["Date"])].mean()

trailing_eps = newest_k_profit/newest_sharesoutstanding
forward_eps = newest_q_profit*4/newest_sharesoutstanding

trailing_pe = round((newest_price/trailing_eps),2)
forward_pe = round((newest_price/forward_eps),2)
###############################################

###############################################
inc_date_df = quarterly_income_statement[['end', 'val']][quarterly_income_statement['tag']==inc_tag]
pe_list = []
date_list = []
sharesoutstanding_tag = EDGAR_gettag('sharesoutstanding', balance_sheet['tag'])

for i in range(4,len(inc_date_df)):
    annualized_earning = inc_date_df.iloc[i-4:i]['val'].sum()
    shares_outstanding = balance_sheet['val'][(balance_sheet['tag']==sharesoutstanding_tag) &
                                              (balance_sheet['end']==inc_date_df.iloc[i]['end'])].mean()
    eps = annualized_earning/shares_outstanding
    price = historical_price['Close'][(historical_price['Date'] > inc_date_df.iloc[i]['end'] - dt.timedelta(15)) &
                          (historical_price['Date'] < inc_date_df.iloc[i]['end'] + dt.timedelta(15))].mean()
    pe = round((price/eps).mean(),2)
    pe_list.append(pe)
    date_list.append(inc_date_df.iloc[i]['end'])
pe_df = pd.DataFrame({'date' : date_list,'pe' : pe_list})
###############################################

#Split tab into two columns
with tab1:
    row = st.columns((1, 4), gap='medium')
    with row[1]:
        st.subheader('Inventory Analysis', divider = False)
        #Plot for column 1
        fig = create_inventory_chart(balance_sheet, quarterly_income_statement,  historical_price)
        st.plotly_chart(fig, use_container_width = True)

    with row[0]:
        fig = trailing_pe_plot(newest_price, trailing_eps, trailing_pe, pe_df)
        on = st.toggle('Forward PE')
        if on:
            fig = forward_pe_plot(newest_price, forward_eps, forward_pe, pe_df)
        st.plotly_chart(fig, use_container_width=True)
#######################