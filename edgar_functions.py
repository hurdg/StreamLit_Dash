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
def EDGAR_gettag(tag:str, tags:list=None):
    try:
        all_matching_tags = tags[tags.str.contains(tag, case = False)].unique()
        min_tag = min(all_matching_tags, key=len)
        print(f"The selected tag is: {min_tag}.")
        return(min_tag)
    except:
        print(f"No tags contain {tag}.")



#Calculate 4th quarter data
def EDGAR_getq4(df, net_income_tag:str):
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