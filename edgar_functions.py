import pandas as pd
import requests
import streamlit as st
import datetime as dt
import re

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
def EDGAR_gettag(tag:str, tags:list=None):
    try:
        all_matching_tags = tags[tags.str.contains(tag, case = False)].unique()
        min_tag = min(all_matching_tags, key=len)
        print(f"The selected tag is: {min_tag}.")
        return(min_tag)
    except:
        print(f"No tags contain {tag}.")



#Calculate 4th quarter data
def EDGAR_q4df(row, full_df):
    if "K" in row['form']:
        row_tag = row['tag']
        row_year = re.search(r'\d+', row['frame'])[0]
        k_val = row['val']
        q_vals = full_df['val'][(full_df['frame'].str.contains(row_year)) &
                                (full_df['tag'] == row_tag) &
                                (full_df['form'].str.contains('q', case = False))].sum()
        q4_val = k_val - q_vals
        q4_row = row.copy()
        q4_row['val']  = q4_val
        q4_row['form'] = '10-Qd'
        return(q4_row)
    else:
        return(row)
