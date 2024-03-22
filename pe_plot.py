import plotly.graph_objects as go
import plotly.subplots as pls
import streamlit as st

@st.cache_data
def trailing_pe_plot(newest_price, trailing_eps, trailing_pe, pe_df):
    labels = ["Price per Share", "Earnings per Share"]
    values = [newest_price, trailing_eps]

    # Create subplots: use 'domain' type for Pie subplot
    fig = pls.make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}],[{'type':'xy'}]], row_width=[0.7, 0.3])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"P/E <br> <b>{trailing_pe}</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        hole=.4, hoverinfo="label+value+name",
                        marker=dict(colors=['darkred', 'red'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 


    fig.add_trace(go.Scatter(
        x = pe_df['date'],
        y = pe_df['pe'],
        marker=dict(color='green'),
        name="Net Income",
        mode = 'lines'
    ), row=2, col=1)

    fig.update_layout(
        title_text="Trailing PE",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)
    
    return(fig)

@st.cache_data
def forward_pe_plot(newest_price:float, forward_eps:float, forward_pe, pe_df):
    labels = ["Price per Share", "Earnings per Share"]
    values = [round(newest_price,2), round(forward_eps,2)]

    # Create subplots: use 'domain' type for Pie subplot
    fig = pls.make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}],[{'type':'xy'}]], row_width=[0.7, 0.3])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"P/E <br> <b>{forward_pe}</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        hole=.4, hoverinfo="label+value+name",
                        marker=dict(colors=['darkred', 'red'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 


    fig.add_trace(go.Scatter(
        x = pe_df['date'],
        y = pe_df['pe'],
        marker=dict(color='red'),
        name="Net Income",
        mode = 'lines'
    ), row=2, col=1)

    fig.update_layout(
        title_text="Forward PE",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)
    
    return(fig)