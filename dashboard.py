import requests
import json
import pandas as pd
from secedgar import CompanyFilings, FilingType
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as pls
import altair as alt
import datetime as dt


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

df = EDGAR_query(cik_str, header = header)


#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
raw_tags = df['tag'][df['tag'].str.contains('rawmaterials', case = False)].unique()
raw_tag = min(raw_tags, key=len)

wip_tags = df['tag'][df['tag'].str.contains('workinprocess', case = False)].unique()
wip_tag = min(wip_tags, key=len)

fin_tags = df['tag'][df['tag'].str.contains('FinishedGoods', case = False)].unique()
fin_tag = min(fin_tags, key=len)

inc_tags = df['tag'][df['tag'].str.contains('netincome', case = False)].unique()
inc_tag = min(inc_tags, key=len)

#Subset by desired data
df_inventory = df[df['tag'].isin([raw_tag, wip_tag, fin_tag, inc_tag])][['start','end','val','tag']]
df_inventory[["start", 'end']] = df_inventory[["start", 'end']].apply(pd.to_datetime, errors='coerce')
df_inventory = df_inventory[df_inventory['frame'].notna() & df_inventory['frame'].notnull()]
df_inventory.sort_values(by='end', inplace = True) 
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

#Create Figure
#######################
fig = go.Figure()
fig = pls.make_subplots(rows=1, cols=1)

fig.add_trace(go.Bar(
    x = df_inventory['date'][df_inventory['tag']==raw_tag],
    y = df_inventory['val'][df_inventory['tag']==raw_tag],
    legendgroup="group",
    marker=dict(color='forestgreen'),
    legendgrouptitle_text="method one",
    name="Raw Materials"
), row=1, col=1)

fig.add_trace(go.Bar(
    x = df_inventory['date'][df_inventory['tag']==wip_tag],
    y = df_inventory['val'][df_inventory['tag']==wip_tag],
    legendgroup="group", 
    legendgrouptitle_text="method one",
    marker=dict(color='goldenrod'),
    name="Work In Process"
), row=1, col=1)

fig.add_trace(go.Bar(
    x = df_inventory['date'][df_inventory['tag']==fin_tag],
    y = df_inventory['val'][df_inventory['tag']==fin_tag],
    legendgroup="group", 
    legendgrouptitle_text="method one",
    marker=dict(color='darkred'),
    name="Finished Goods"
), row=1, col=1)

fig.add_trace(go.Line(
    x = df_inventory['date'][df_inventory['tag']=='NetIncomeLoss'],
    y = df_inventory['val'][df_inventory['tag']=='NetIncomeLoss']/10,
    legendgroup="group", 
    legendgrouptitle_text="method one",
    marker=dict(color='darkblue'),
    name="Net Income"
), row=1, col=1)

fig.update_layout(barmode='group', bargroupgap=0.1, plot_bgcolor='rgb(0,0,0)',paper_bgcolor='rgb(0,0,0)' )

st.plotly_chart(fig)
#######################