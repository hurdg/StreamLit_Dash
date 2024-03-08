import pandas as pd
import requests
import streamlit as st
import datetime as dt

#Download data from API
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


#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
def get_raw_tag(tags:list=None):
    raw_tags = tags[tags.str.contains('rawmaterials', case = False)].unique()
    raw_tag = min(raw_tags, key=len)
    return(raw_tag)

def get_wip_tag(tags:list=None):
    wip_tags = tags[tags.str.contains('workinprocess', case = False)].unique()
    wip_tag = min(wip_tags, key=len)
    return(wip_tag)

def get_fg_tag(tags:list=None):
    fg_tags = tags[tags.str.contains('FinishedGoods', case = False)].unique()
    fg_tag = min(fg_tags, key=len)
    return(fg)

def get_inc_tag(tags:list=None):
    inc_tags = tags[tags.str.contains('netincome', case = False)].unique()
    inc_tag = min(inc_tags, key=len)
    return(inc_tag)


#Calculate 4th quarter data
def get_quarter4th_data(df, net_income_tag:str):
    inc_index = df[df['tag'] == net_income_tag].index
    delta = df.iloc[inc_index]['end'] - df.iloc[inc_index]['start']
    annual_index = delta > dt.timedelta(345)

    for i in inc_index[annual_index]:
        infile =  df.iloc[i]
        k_val = infile['val']
        k_enddate = infile['end']
        k_startdate = infile['start']

        quartervals = (df['val'].iloc[inc_index][(df['start'] >= k_startdate) & #Within time period defined by 10-k 
                                                            (df['end'] <= k_enddate) &
                                                            ((df['end'] - df['start']) < dt.timedelta(200))]) #Exclude the 10-k vlaue
        new_val = k_val - sum(quartervals)
        df['val'].iloc[i] = new_val
    return(df)