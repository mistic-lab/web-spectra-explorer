import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output, State
import h5py
import numpy as np

from dataService import fetch_integration

waterfall_height = 200 # px
spec_width = 1000
y_range = [20, 60]
simDataFile = h5py.File('data.h5','r')

spec = np.zeros((waterfall_height, spec_width))
freqs = np.linspace(8*(-(400e6)/3), 8*(400e6)/3, spec_width)



app = dash.Dash(__name__, requests_pathname_prefix='/live/')

app.layout = html.Div(
    [
        dcc.Interval(id='refresh_rate', interval=1000), # ms
        dcc.Graph(id='spec', responsive=True, config=dict(displayModeBar=False), 
            figure={
                'data': [
                    {
                        'type': 'scattergl',
                        'y': spec[0],
                        'x': freqs,
                        'line': {
                            'color': 'white',
                            'width': 2,
                        },
                        'fill': 'tozeroy',
                    },
                ],
                'layout': {
                    'width': '100%',
                    'height': '100%',
                    'margin': {
                        't': 10,
                        'b': 40,
                        'r': 0,
                        'l': 0,
                    },
                    'yaxis': {
                        'range': y_range,
                        'fixedRange': True,
                        # 'title': 'dB',
                        'ticklabelposition': 'inside',
                        'showticklabels': False,
                        'color': '#a3a7b0',

                    },
                    'xaxis': {
                        'showexponent': 'all',
                        'exponentformat': 'SI',
                        'ticksuffix': 'Hz',
                        'color': '#a3a7b0',

                    },
                    'plot_bgcolor': '#23272c',
                    'paper_bgcolor': '#23272c',
                }
            },
            style={
                'height': '20%',
                'margin': 0
            }
        ),
        dcc.Graph(id='waterfall', responsive=True, config=dict(displayModeBar=False, doubleClick='reset'), 
            figure={
                'data': [{
                    'type': 'heatmap',
                    'z': spec,
                    'x': freqs,
                    'colorbar': {
                        'len': 0.5,
                        'x': 0.98,
                        'y': 0.98,
                        'yanchor': 'top',
                        'xanchor': 'right',
                        'bgcolor': '#23272c',
                        'tickfont': {
                            'color': 'white',
                        },
                    },
                    'colorscale': 'Rainbow',
                    'zmin': y_range[0],
                    'zmax': y_range[1],
                }],
                'layout': {
                    'width': '100%',
                    'height': '100%',
                    'margin': {
                        't': 0,
                        'b': 0,
                        'r': 0,
                        'l': 0,
                    },
                    'yaxis': {
                        'fixedrange': True,
                        'showticklabels': False,
                        'showgrid': False,
                        'color': '#a3a7b0',
                        'ticks': '',
                    },
                    'xaxis': {
                        'fixedrange': True,
                        'color': '#a3a7b0',
                        'ticks': '',
                    },
                    'plot_bgcolor': '#23272c',
                    'paper_bgcolor': '#23272c',
                }
            },
            style={'height': '80%', 'margin': 0}
        ),
    ], style={
        'height':'100vh',
        'margin':0,
    }
)


# Whenever the Interval triggers this runs
@app.callback(
    [
        Output("spec", "extendData"),
        Output("waterfall", "extendData"),
    ],
    [
        Input("refresh_rate", "n_intervals") # output n_intervals, an int
    ],
    [
        State("spec", "relayoutData")
    ],
    prevent_initial_call=True
)
def update_spec(index, relayoutData, spec=spec, freqs=freqs):

    if relayoutData and 'xaxis.range[0]' in relayoutData:# and 'xaxis.range[1]' in relayoutData:
        f1 = int(relayoutData['xaxis.range[0]'])
        f2 = int(relayoutData['xaxis.range[1]'])
    else:
        f1 = freqs[0]
        f2 = freqs[-1]
    
    newLine, freqs = fetch_integration(index, simDataFile, f1=f1, f2=f2, length=spec_width)

    spec[0:-1] = spec[1:]
    spec[-1] = newLine

    updatedSpec = dict(y=[newLine], x=[freqs]), [0], spec_width
    updatedWaterfall = dict(z=[spec]), [0], waterfall_height

    return updatedSpec, updatedWaterfall



server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

    simDataFile.close()
