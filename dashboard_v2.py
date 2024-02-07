from dash import Dash, html, dcc, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import glob2
import os
import dash_auth
import login_dev


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets) #[dbc.themes.VAPOR, dbc_css])

# Keep this out of source code repository - save in a file or a database

# auth = dash_auth.BasicAuth(
#     app,
#     login_dev.VALID_USERNAME_PASSWORD_PAIRS
# )


input_folder = input_folder = "/Users/assansanogo/Downloads/dashboard/refactor/refactor/src/powerbi"
#input_folder = "/mnt/c/Users/jeans/Downloads/assan/powerbi_data/content/refactor/refactor/src/powerbi"
excel_path = os.path.join(input_folder,"out.xlsx")
csv_path = os.path.join(input_folder,"out.csv")
if os.path.exists(excel_path):
    df = pd.read_excel(os.path.join(input_folder,"out.xlsx"))
else:
    df = pd.read_csv(os.path.join(input_folder,"out.csv"))
print(df.columns)
df = df.dropna(subset = ['year'])
print(df.year.unique())
print(df.date.unique())

app.layout = html.Div([
    html.Div([
        html.Div([
            # dropdown with default values
            html.Div([html.P('You can select the following brands')]),
            dcc.Dropdown(df.Marque_corrected.unique(), df.Marque_corrected.unique()[0:2], multi=True, id='brand-dropdown')

        ]),
        html.Div([
            # dropdown with default values
            html.Div([html.P('You can UNselect the following brands')]),
            dcc.Dropdown(df.Marque_corrected.unique(), "OTHER", multi=True, id='remove-dropdown')

        ]),

        html.Div([
            # dropdown with desired x dimensions
            dcc.Dropdown(
                ['CA_Brut_TTC_corrected', 'Qte_corrected'],
                id='crossfilter-xaxis-column',
            ),
            # format of the dimension on the plot (linear or log)
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='crossfilter-xaxis-type',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            # dropdown with desired y dimensions
            dcc.Dropdown(['CA_Brut_TTC_corrected', 'Qte_corrected'],
                id='crossfilter-yaxis-column'
            ),
            # format of the dimension on the plot (linear or log)
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='crossfilter-yaxis-type',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'padding': '10px 5px'
    }),
    # main figure  (dimension x vs dimension y)
    html.Div([
        dcc.Graph(
            id='crossfilter-indicator-scatter',
            hoverData={'points': [{'customdata': 'AVENE'}]}
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(id='x-time-series'),
        dcc.Graph(id='y-time-series'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    # dateslider used as a date picker 
    html.Div(dcc.Slider(
        df['year'].min(),
        df['year'].max(),
        step=None,
        id='crossfilter-year--slider',
        value=df['year'].max(),
        marks={str(year): str(year) for year in df['year'].unique()}
    ), style={'width': '49%', 'padding': '0px 20px 20px 20px'}),
    # data table with records (down to product)
    
        dbc.Card(
            dbc.CardBody(
            html.Div(
                dash_table.DataTable(data=df.to_dict('records'),
                columns = [{"name": i, "id": i} for i in df.columns], 
                id='tbl',
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current= 0,
                page_size= 10
                ), 
                style={"maxHeight": "200px", "overflow": "scroll"}
                ))
            )
])


# # call back for brand selection
# @callback(
#     Output('dd-output-container', 'children'),
#     Input('brand-dropdown', 'value')
# )
# def update_output(value):
#     return f'You have selected {(",").join(value)}'


# # call back for brand UNselection
# @callback(
#     Output('dd-rm-output-container', 'children'),
#     Input('remove-dropdown', 'value')
# )
# def update_output(value):
#     return f'You have selected {(",").join(value)}'




# callback for updating the data table (down to product)
@callback(
    [Output("tbl", "data"), Output('tbl', 'columns')],
    Input('brand-dropdown', 'value'),
    Input('crossfilter-year--slider', 'value'),
    Input('remove-dropdown', 'value')
)
def update_output(value, year_value, removed_brand):
    if value:
        dff = df[(df['Marque_corrected'].isin(value)) & (df['year']==year_value)] #.sort_values(by=['CA_Brut_TTC_corrected'], ascending=False)
    else:
        dff = df[df['year']==year_value]

    try:
        dff = dff[dff["Marque_corrected"]!=removed_brand]
    except:
        pass

    dff=dff.iloc[:100,:]
    records = dff.to_dict('records')
    cols = [{"name": i, "id": i} for i in dff.columns]
    
    return records, cols



# callback for xtime series (CA)
@callback(
Output('crossfilter-indicator-scatter', 'figure'),
Input('crossfilter-xaxis-column', 'value'),
Input('crossfilter-yaxis-column', 'value'),
Input('crossfilter-xaxis-type', 'value'),
Input('crossfilter-yaxis-type', 'value'),
Input('crossfilter-year--slider', 'value'),
Input('brand-dropdown','value'),
Input('remove-dropdown', 'value')
)

def update_graph(xaxis_column_name, 
                yaxis_column_name,
                xaxis_type, 
                yaxis_type,
                year_value, 
                brand_value,
                removed_brand):

   

    dff = df[df['year'] == year_value]
    dff_copy = dff.copy()

    print(removed_brand)

    if brand_value != []:
        dff = dff[dff['Marque_corrected'].isin(brand_value)]
        dff = dff[dff['year'] == year_value]
        if removed_brand != []:
            if type(removed_brand) != str:
                dff = dff[~dff["Marque_corrected"].isin(removed_brand)]
            else:
                dff = dff[dff["Marque_corrected"]!= removed_brand]
    else:
        dff = df[df['year'] == year_value]
        if type(removed_brand) != str:
            dff = dff[~dff["Marque_corrected"].isin(removed_brand)]
        else:
            dff = dff[dff["Marque_corrected"]!= removed_brand]

    try:
        dffx = dff.groupby("Marque_corrected")[xaxis_column_name].sum().reset_index()
        dffx.columns = ["Marque_corrected",xaxis_column_name]

        dffy = dff.groupby("Marque_corrected")[yaxis_column_name].sum().reset_index()
        dffy.columns = ["Marque_corrected",yaxis_column_name]
    except:
        xaxis_column_name = "CA_Brut_TTC_corrected"
        yaxis_column_name = "Qte_corrected"

        dffx = dff.groupby("Marque_corrected")[xaxis_column_name].sum().reset_index()
        dffx.columns = ["Marque_corrected",xaxis_column_name]

        dffy = dff.groupby("Marque_corrected")[yaxis_column_name].sum().reset_index()
        dffy.columns = ["Marque_corrected",yaxis_column_name]

    try:
        fig = px.scatter(x=dffx[xaxis_column_name],
                y=dffy[yaxis_column_name],
                hover_name=dffy['Marque_corrected'].unique()
                )
    except:
        fig = px.scatter(x=dffx["Qte_corrected"],
        y=dffy["CA_Brut_TTC_corrected"],
        hover_name=dffy['Marque_corrected'].unique()
        )

    fig.update_traces(customdata=dffx['Marque_corrected'])

    fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')

    fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig


def create_time_series(dff,
                    dim, 
                    axis_type, 
                    title, 
                    type="bar"):

    if type=="bar":
        fig = px.bar(dff, x='month', y=dim)
    else:
        print(dim)
        fig = px.scatter(dff, x='month', y=["CA_objective_2023",'CA_Brut_TTC_corrected'])
        fig.update_traces(mode='lines+markers')

        fig.update_xaxes(showgrid=False)

        fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)

    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

    return fig

# callback for y time series
@callback(
    Output('x-time-series', 'figure'),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'),
    Input('crossfilter-year--slider', 'value'),
    Input('tbl', 'active_cell'),
    Input('remove-dropdown', 'value'))

def update_x_timeseries(hoverData, 
                        xaxis_column_name, 
                        axis_type, 
                        year_value,
                        active_cell,
                        removed_brand):

    marque = hoverData['points'][0]['customdata']
    print(marque)
    dff = df[df['Marque_corrected'] == marque]
    dff = dff[dff['year'] == year_value]

    print(active_cell)

    selected_col = None
    selected_row = None
    if type(active_cell) == dict:
        selected_col = active_cell["column_id"]
        selected_row = active_cell["row"]

        if selected_col == "Designation":
            designation = dff[selected_col].values[selected_row]
            dff = dff[dff["Designation"]==designation]

    #dff = dff.groupby("month")["CA_Brut_TTC_corrected"].sum().reset_index()
    print(dff.head())
    print(dff.columns)

    try:
        dff = dff[dff["Marque_corrected"]!=removed_brand]
    except:
        pass

    dff = dff.groupby("month").agg({'CA_Brut_TTC_corrected':'sum','CA_objective_2023':'sum'}).reset_index()
    dff.columns = ["month", "CA_Brut_TTC_corrected","CA_objective_2023"]
    
    dim=["CA_Brut_TTC_corrected","CA_Objective"]
    #dff = dff[dff['Indicator Name'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(marque, xaxis_column_name)
    return create_time_series(dff,dim, axis_type, title, type="linear")


@callback(
    Output('y-time-series', 'figure'),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'),
    Input('crossfilter-year--slider', 'value'),
    Input('tbl', 'active_cell'),
    Input('remove-dropdown', 'value'))

def update_y_timeseries(hoverData, 
                        yaxis_column_name, 
                        axis_type, 
                        year_value, 
                        active_cell,
                        removed_brand):

    marque = hoverData['points'][0]['customdata']
    print(marque)
    
    dff = df[df['Marque_corrected'] == marque]
    dff = dff[dff['year'] == year_value]

    print(active_cell)

    selected_col = None
    selected_row = None
    if type(active_cell) == dict:
        selected_col = active_cell["column_id"]
        selected_row = active_cell["row"]

        if selected_col == "Designation":
            designation = dff[selected_col].values[selected_row]
            dff = dff[dff["Designation"]==designation]
    try:
        dff = dff[dff["Marque_corrected"]!=removed_brand]
    except:
        pass


    dff = dff.groupby("month")["Qte_corrected"].sum().reset_index()
    dff.columns = ["month", "Qte_corrected"]
    dim="Qte_corrected"
    #dff = dff[dff['Indicator Name'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(marque, yaxis_column_name)
    return create_time_series(dff, dim,axis_type, title)



# @callback(
#     Output('y-time-series', 'figure'),
#     Input('crossfilter-indicator-scatter', 'hoverData'),
#     Input('crossfilter-yaxis-column', 'value'),
#     Input('crossfilter-yaxis-type', 'value'))
# def update_y_timeseries(hoverData, yaxis_column_name, axis_type):
#     dff = df[df['Country Name'] == hoverData['points'][0]['customdata']]
#     dff = dff[dff['Indicator Name'] == yaxis_column_name]
#     return create_time_series(dff, axis_type, yaxis_column_name)


if __name__ == '__main__':
    app.run(debug=True)