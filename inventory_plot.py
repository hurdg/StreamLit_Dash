import plotly.graph_objects as go
import plotly.subplots as pls

#Create variables for whatever tag name is used to describe raw, workinprocess, and finished
def get_inventory_tags(tags:list=None):
    raw_tags = tags[tags.str.contains('rawmaterials', case = False)].unique()
    raw_tag = min(raw_tags, key=len)

    wip_tags = tags[tags.str.contains('workinprocess', case = False)].unique()
    wip_tag = min(wip_tags, key=len)

    fin_tags = tags[tags.str.contains('FinishedGoods', case = False)].unique()
    fin_tag = min(fin_tags, key=len)

    inc_tags = tags[tags.str.contains('netincome', case = False)].unique()
    inc_tag = min(inc_tags, key=len)
    return(raw_tag, wip_tag, fin_tag, inc_tag)



#Create Inventory Chart
def create_inventory_chart(inventory_df, historical_df):
    raw_tag, wip_tag, fin_tag, inc_tag = get_inventory_tags(inventory_df['tag'])

    
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
        x = inventory_df['end'][inventory_df['tag']=='NetIncomeLoss'],
        y = inventory_df['val'][inventory_df['tag']=='NetIncomeLoss']/10,
        #legendgroup="group", 
        #legendgrouptitle_text="method one",
        marker=dict(color='darkblue'),
        name="Net Income"
    ), row=1, col=1, secondary_y=False)

    fig.update_layout(barmode='group', margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
                    bargroupgap=0.1, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True,
                    legend=dict(orientation="h", yanchor="top",y=0.99,xanchor="left",x=0.01))
    return(fig)