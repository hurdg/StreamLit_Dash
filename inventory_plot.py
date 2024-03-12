import plotly.graph_objects as go
import plotly.subplots as pls

from EDGAR_functions import EDGAR_gettag


#Create Inventory Chart
def create_inventory_chart(inventory_df, quarterly_df, historical_df):
    raw_tag = EDGAR_gettag('rawmaterials', inventory_df['tag'])
    wip_tag = EDGAR_gettag('workinprocess', inventory_df['tag'])
    fin_tag = EDGAR_gettag('FinishedGoods', inventory_df['tag'])
    inc_tag = EDGAR_gettag('netincome', quarterly_df['tag'])


    fig = go.Figure()
    fig = pls.make_subplots(rows=1, cols=1,
                            specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Line(
        x = historical_df['Date'],
        y = historical_df['Close'],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        line=dict(color='white', width = 0.1),
        name="Stock Price"
    ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Bar(
        x = inventory_df['end'][inventory_df['tag']==raw_tag],
        y = inventory_df['val'][inventory_df['tag']==raw_tag],
        #legendgroup="group",
        marker=dict(color='forestgreen'),
        #legendgrouptitle_text="method one",
        name="Raw Materials"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = inventory_df['end'][inventory_df['tag']==wip_tag],
        y = inventory_df['val'][inventory_df['tag']==wip_tag],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='goldenrod'),
        name="Work In Process"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Bar(
        x = inventory_df['end'][inventory_df['tag']==fin_tag],
        y = inventory_df['val'][inventory_df['tag']==fin_tag],
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='darkred'),
        name="Finished Goods"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Line(
        x = inventory_df['end'][quarterly_df['tag']==inc_tag],
        y = inventory_df['val'][quarterly_df['tag']==inc_tag]/10,
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='darkblue'),
        name="Net Income"
    ), row=1, col=1, secondary_y=False)

    fig.update_layout(barmode='group', margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
                    bargroupgap=0.1, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True,
                    legend=dict(orientation="h", yanchor="top",y=0.99,xanchor="left",x=0.01))
    return(fig)