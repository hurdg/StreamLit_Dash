import plotly.graph_objects as go
import plotly.subplots as pls

from EDGAR_functions import EDGAR_gettag


#Create Inventory Chart
def create_inventory_chart(balance_sheet, income_statement, historical_df):
    raw_tag = EDGAR_gettag('rawmaterials', balance_sheet['tag'])
    wip_tag = EDGAR_gettag('workinprocess', balance_sheet['tag'])
    fin_tag = EDGAR_gettag('FinishedGoods', balance_sheet['tag'])
    inc_tag = EDGAR_gettag('netincome', income_statement['tag'])


    fig = go.Figure()
    fig = pls.make_subplots(rows=1, cols=1,
                            specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x = historical_df['Date'],
        y = historical_df['Close'],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        line=dict(color='white', width = 0.1),
        name="Stock Price",
        mode='lines'
    ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Bar(
        x = balance_sheet['end'][balance_sheet['tag']==raw_tag],
        y = balance_sheet['val'][balance_sheet['tag']==raw_tag],
        #legendgroup="group",
        marker=dict(color='forestgreen'),
        #legendgrouptitle_text="method one",
        name="Raw Materials"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = balance_sheet['end'][balance_sheet['tag']==wip_tag],
        y = balance_sheet['val'][balance_sheet['tag']==wip_tag],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='goldenrod'),
        name="Work In Process"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = balance_sheet['end'][balance_sheet['tag']==fin_tag],
        y = balance_sheet['val'][balance_sheet['tag']==fin_tag],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='darkred'),
        name="Finished Goods"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x = income_statement['end'][income_statement['tag']==inc_tag],
        y = income_statement['val'][income_statement['tag']==inc_tag],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='darkblue'),
        name="Net Income",
        mode='lines'
    ), row=1, col=1, secondary_y=False)

    fig.update_layout(barmode='group', margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
                    bargroupgap=0.1, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True,
                    legend=dict(orientation="h", yanchor="top",y=0.99,xanchor="left",x=0.01))
    return(fig)