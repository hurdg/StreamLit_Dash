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
df.rename(columns = {'end' : 'date'}, inplace = True)

#Subset by desired data
df_inventory = df[df['tag'].str.contains('inventory|netincome', case = False)]
df_inventory["date"] = pd.to_datetime(df_inventory["date"])
df_inventory['tag'].unique()

#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
raw_tags = df_inventory['tag'][df_inventory['tag'].str.contains('rawmaterials', case = False)].unique()
raw_tag = min(raw_tags, key=len)

wip_tags = df_inventory['tag'][df_inventory['tag'].str.contains('workinprocess', case = False)].unique()
wip_tag = min(wip_tags, key=len)

fin_tags = df_inventory['tag'][df_inventory['tag'].str.contains('FinishedGoods', case = False)].unique()
fin_tag = min(fin_tags, key=len)


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

fig.update_layout(barmode='group', bargroupgap=0.01)

st.plotly_chart(fig)