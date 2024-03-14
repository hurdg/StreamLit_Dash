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

st.set_page_config(
    page_title="Ticker Trends",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

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


#Split dashboard into two columns
row = st.columns((1, 4), gap='medium')
with row[1]:
    st.subheader('Inventory Analysis', divider = False)

#Load data of selected company
df = EDGAR_query(cik_str, header = header)

#Prep df and create quarterly
df[["start", 'end']] = df[["start", 'end']].apply(pd.to_datetime, errors='coerce', utc=False)

quarter_prep_df = df[(df['frame'].notna()) & 
                  (df['start'].notna()) &
                  (df['frame'].notnull())
                  ]
quarter_prep_df.sort_values(['tag', 'end', 'start'], inplace = True) 
quarter_prep_df.reset_index(inplace = True)
quarter_prep_df.drop(columns = ['index'], inplace = True)

#Create 4th quarter df
quarterly_df = quarter_prep_df.apply(EDGAR_q4df, full_df = quarter_prep_df, axis=1)

#Subset by desired data
#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
raw_tag = EDGAR_gettag('rawmaterials', df['tag'])
wip_tag = EDGAR_gettag('workinprocess', df['tag'])
fin_tag = EDGAR_gettag('FinishedGoods', df['tag'])
inc_tag = EDGAR_gettag('netincome', quarterly_df['tag'])

df_inventory = df[df['tag'].isin([raw_tag, wip_tag, fin_tag, inc_tag])][['start','end','val','tag', 'frame']]
df_inventory.reset_index(inplace = True)
##Changes
# get historical stock price data
df_hist = yf.Ticker('UG')
hist = df_hist.history(period="max")
hist.reset_index(inplace = True)
hist["Date"] = hist["Date"].dt.tz_localize(tz = None)
hist = hist[hist["Date"] > (min(quarterly_df['start']))]

#Split dashboard into two columns
row = st.columns((1, 4), gap='medium')

#Plot for column 1
with row[1]:
    #Create Figure
    #######################
    fig = create_inventory_chart(df_inventory, quarterly_df,  hist)
    st.plotly_chart(fig, use_container_width=True)

###############################################
newest_annual_dates = pd.Series.nlargest((quarterly_df['end'][quarterly_df['tag']==inc_tag]),4)
newest_profit = quarterly_df['val'][(quarterly_df['tag']==inc_tag) & (quarterly_df['end'].isin(newest_annual_dates))]
newest_sharesoutstanding = quarterly_df['val'][(quarterly_df['tag']=='CommonStockSharesOutstanding') & (quarterly_df['end']== max(newest_annual_dates))]
newest_profitpershare = newest_profit.sum()/newest_sharesoutstanding.mean()
newest_price = hist['Close'][hist["Date"]==max(hist["Date"])]
pe = round((newest_price/newest_profitpershare).mean(),2)

dates = df['end'].unique()

pe_list = []
date_list = []
for i in range(3,len(dates)):
    #Chunk data quarterly
    quarterly_prices = hist['Close'][(hist['Date'] > dates[i-1]) & (hist['Date'] < dates[i])]

    annualized_earning = df['val'][(df['tag']==inc_tag) & (df['end']< dates[i-1]) & (df['end']<dates[i-1]-dt.timedelta(360))].mean()*4
    quarterly_shares = df['val'][(df['tag']=='CommonStockSharesOutstanding') & (df['end']<dates[i-1]) & (df['end']<dates[i-1]-dt.timedelta(360))].max()
    quartely_earningspershare = annualized_earning/quarterly_shares
    quarterly_pe = quarterly_prices/quartely_earningspershare

    quarterly_dates = hist['Date'][(hist['Date'] > dates[i-1]) & (hist['Date'] < dates[i])]
    pe_list.append(quarterly_pe)
    date_list.append(quarterly_dates)


def flatten(xss):
    return [x for xs in xss for x in xs]

pe_df = pd.DataFrame({'date' : flatten(date_list),
              'pe' : flatten(pe_list)})




with row[0]:
    labels = ["Price per Share", "Earnings per Share"]
    values = [round(newest_price.mean(),2), round(newest_profitpershare.mean(),2)]

    # Create subplots: use 'domain' type for Pie subplot
    fig = pls.make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}],[{'type':'xy'}]], row_width=[0.3, 0.7])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"P/E <br> <b>{pe}</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        hole=.4, hoverinfo="label+value+name",
                        marker=dict(colors=['darkred', 'red'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 


    fig.add_trace(go.Line(
        x = pe_df['date'],
        y = pe_df['pe'],
        marker=dict(color='grey'),
        name="Net Income"
    ), row=2, col=1)

    fig.update_layout(
        title_text="",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)
    st.plotly_chart(fig, use_container_width=True)
#######################