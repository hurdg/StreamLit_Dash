import requests
import json
import pandas as pd
from secedgar import CompanyFilings, FilingType
import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as pls
import altair as alt
import datetime as dt
import yfinance as yf


st.set_page_config(
    page_title="My First Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

header = {'User-Agent':'gavinhurd11@gmail.com'}
tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
tickers_cik['cik_str']=tickers_cik['cik_str'].astype(str).str.zfill(10)


selected_ticker = st.sidebar.selectbox('Ticker', options = tickers_cik['ticker'])
cik_str = tickers_cik['cik_str'][tickers_cik['ticker'] == selected_ticker].values[0]

#Company data
@st.cache_data  # 👈 Add the caching decorator
def EDGAR_query(cik:str, header:dict, tag:list=None)->pd.DataFrame:
    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK'+cik+'.json'
    response = requests.get(url, headers=header)

    try:
        if tag == None:
            tags = list(response.json()['facts']['us-gaap'].keys())
        else:
            tags=tag
        
        company_data = pd.DataFrame()


        for i in range(len(tags)):
            try:
                tag = tags[i]
                units = list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
                data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units])
                data['tag']=tag
                data['units']=units
                company_data = pd.concat([company_data, data], ignore_index=True)
            except:
                print(tag+'not found')
    except:print('company data not found')
    return company_data

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')

df = EDGAR_query(cik_str, header = header)

# Notify the reader that the data was successfully loaded.
data_load_state.text('')

#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
raw_tags = df['tag'][df['tag'].str.contains('rawmaterials', case = False)].unique()
raw_tag = min(raw_tags, key=len)

wip_tags = df['tag'][df['tag'].str.contains('workinprocess', case = False)].unique()
wip_tag = min(wip_tags, key=len)

fin_tags = df['tag'][df['tag'].str.contains('FinishedGoods', case = False)].unique()
fin_tag = min(fin_tags, key=len)

inc_tags = df['tag'][df['tag'].str.contains('netincome', case = False)].unique()
inc_tag = min(inc_tags, key=len)

#Clean up df
df[["start", 'end']] = df[["start", 'end']].apply(pd.to_datetime, errors='coerce', utc=False)
df = df[df['frame'].notna() & df['frame'].notnull()]
df.sort_values(by='end', inplace = True) 
df.reset_index(inplace = True)

#Subset by desired data
df_inventory = df[df['tag'].isin([raw_tag, wip_tag, fin_tag, inc_tag])][['start','end','val','tag', 'frame']]
df_inventory.reset_index(inplace = True)

#Calculate 4th quarter data
inc_index = df_inventory[df_inventory['tag'] == inc_tag].index
delta = df_inventory.iloc[inc_index]['end'] - df_inventory.iloc[inc_index]['start']
annual_index = delta > dt.timedelta(345)

for i in inc_index[annual_index]:
    infile =  df_inventory.iloc[i]
    k_val = infile['val']
    k_enddate = infile['end']
    k_startdate = infile['start']

    quartervals = (df_inventory['val'].iloc[inc_index][(df_inventory['start'] >= k_startdate) & #Within time period defined by 10-k 
                                                         (df_inventory['end'] <= k_enddate) &
                                                         ((df_inventory['end'] - df_inventory['start']) < dt.timedelta(200))]) #Exclude the 10-k vlaue
    new_val = k_val - sum(quartervals)
    df_inventory['val'].iloc[i] = new_val


# get historical stock price data
df_hist = yf.Ticker(selected_ticker)
hist = df_hist.history(period="max")
hist.reset_index(inplace = True)
hist["Date"] = hist["Date"].dt.tz_localize(tz = None)
hist = hist[hist["Date"] > (min(df_inventory['start']))]

row = st.columns((1, 4), gap='medium')
with row[1]:
    #Create Figure
    #######################
    fig = go.Figure()
    fig = pls.make_subplots(rows=1, cols=1,
                            specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Line(
        x = hist['Date'],
        y = hist['Close'],
        legendgroup="group", 
        legendgrouptitle_text="method one",
        line=dict(color='white', width = 0.1),
        name="Stock Price"
    ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Bar(
        x = df_inventory['end'][df_inventory['tag']==raw_tag],
        y = df_inventory['val'][df_inventory['tag']==raw_tag],
        legendgroup="group",
        marker=dict(color='forestgreen'),
        legendgrouptitle_text="method one",
        name="Raw Materials"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = df_inventory['end'][df_inventory['tag']==wip_tag],
        y = df_inventory['val'][df_inventory['tag']==wip_tag],
        legendgroup="group", 
        legendgrouptitle_text="method one",
        marker=dict(color='goldenrod'),
        name="Work In Process"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = df_inventory['end'][df_inventory['tag']==fin_tag],
        y = df_inventory['val'][df_inventory['tag']==fin_tag],
        legendgroup="group", 
        legendgrouptitle_text="method one",
        marker=dict(color='darkred'),
        name="Finished Goods"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Line(
        x = df_inventory['end'][df_inventory['tag']=='NetIncomeLoss'],
        y = df_inventory['val'][df_inventory['tag']=='NetIncomeLoss']/10,
        legendgroup="group", 
        legendgrouptitle_text="method one",
        marker=dict(color='darkblue'),
        name="Net Income"
    ), row=1, col=1, secondary_y=False)

    fig.update_layout(barmode='group', margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
                    bargroupgap=0.1, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True,
                    legend=dict(yanchor="top",y=0.99,xanchor="left",x=0.01))


    st.plotly_chart(fig, use_container_width=True)

with row[0]:
    newest_annual_dates = pd.Series.nlargest((df['end'][df['tag']==inc_tag]),4)
    newest_profit = df['val'][(df['tag']==inc_tag) & (df['end'].isin(newest_annual_dates))]
    newest_sharesoutstanding = df['val'][(df['tag']=='CommonStockSharesOutstanding') & (df['end']== max(newest_annual_dates))]
    newest_profitpershare = newest_profit.sum()/newest_sharesoutstanding.mean()
    newest_price = hist['Close'][hist["Date"]==max(hist["Date"])]
    pe = round((newest_price/newest_profitpershare).mean(),2)
    labels = ["Price per Share", "Earnings per Share"]
    values = [round(newest_price.mean(),2), round(newest_profitpershare.mean(),2)]

    # Create subplots: use 'domain' type for Pie subplot
    fig = pls.make_subplots(rows=1, cols=1, specs=[[{'type':'domain'}]])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"P/E <br> <b>{pe}</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        marker=dict(colors=['darkred', 'red'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 

    # Use `hole` to create a donut-like pie chart
    fig.update_traces(hole=.4, hoverinfo="label+value+name")

    fig.update_layout(
        title_text="",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)
    st.plotly_chart(fig, use_container_width=True)
#######################