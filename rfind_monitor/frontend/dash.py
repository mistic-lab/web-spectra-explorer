import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash.exceptions import PreventUpdate

import numpy as np
import datetime
from dateutil import tz
import pandas as pd
import h5py
from brain_plasma import Brain

from rfind_monitor.frontend.crunch import fetch_integration, reduce_integration
import rfind_monitor.const as const


# h5f = h5py.File(const.SOURCE_H5,'r')
shared_brain = Brain(path=const.PLASMA_SOCKET)

y_range = [20, 60]

start_spec = np.zeros((const.WATERFALL_HEIGHT, const.SPEC_WIDTH))
start_freqs = np.linspace(0, 2e9, const.SPEC_WIDTH)

start_times = datetime.datetime.now(tz=tz.tzstr('America/Vancouver')) - np.arange(const.WATERFALL_HEIGHT) * datetime.timedelta(seconds=1)
start_timestamps=[int(t.timestamp()) for t in start_times[::-1]]
del start_times




app = dash.Dash(__name__, requests_pathname_prefix=const.DASH_PREFIX, title='RFInd Monitor', update_title=None)


app.layout = html.Div(
    [
        dcc.Store(id='userStore', storage_type='memory', data={'spec': start_spec, 'freqs': start_freqs, 'times': start_timestamps}),
        dcc.Interval(id='check_for_data', interval=500), # ms
        dcc.Interval(id='update_gui', interval=2000), # ms
        dcc.Graph(id='spec', responsive=True, config=dict(displayModeBar=False), 
            figure={
                'data': [
                    {
                        'type': 'scattergl',
                        'y': start_spec[0],
                        'x': start_freqs,
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
                        'ticksuffix': ' dB',
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
                    'x': start_freqs,
                    # 'y': start_times,
                    'z': start_spec,
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
                        'ticksuffix': ' dB',
                    },
                    'colorscale': 'Rainbow',
                    'zmin': y_range[0],
                    'zmax': y_range[1],
                    'hovertemplate': "Freq: %{x} <br />Time: %{y} <br />Power: %{z} dB<extra></extra>"
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
                        'showexponent': 'all',
                        'exponentformat': 'SI',
                        'ticksuffix': 'Hz',
                        'color': '#a3a7b0',
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


@app.callback(
    Output("userStore", "data"),
    [Input("check_for_data", "n_intervals")], # output n_intervals, an int
    [
        State("spec", "relayoutData"),
        State("userStore", "data")
    ],
)
def update_store(index, relayoutData, userStore):

    if 'timestamp' not in shared_brain.names() or shared_brain['timestamp'] == userStore['times'][0]:
        raise PreventUpdate
    else:
        timestamp = shared_brain['timestamp']

        latest_integration = shared_brain['spec']

        if relayoutData and 'xaxis.range[0]' in relayoutData:
            f1 = int(relayoutData['xaxis.range[0]'])
            f2 = int(relayoutData['xaxis.range[1]'])
        else:
            f1=const.FULL_FREQS[0]
            f2=const.FULL_FREQS[-1]

        reduced_integration, new_freqs = reduce_integration(latest_integration, f1, f2, const.SPEC_WIDTH)

        userStore['spec'].pop(0)
        userStore['spec'].append(reduced_integration)

        userStore['freqs'] = new_freqs

        userStore['times'] = timestamp-np.arange(const.WATERFALL_HEIGHT)#*datetime.timedelta(seconds=1)

        app.logger.info(f"Updated the store with timestamp {timestamp}")
        return userStore




# @app.callback(
#     Output("userStore", "data"),
#     [Input("check_for_data", "n_intervals")], # output n_intervals, an int
#     [
#         State("spec", "relayoutData"),
#         State("userStore", "data")
#     ],
#     prevent_initial_call=True
# )
# def update_store(index, relayoutData, storeData):

#     if relayoutData and 'xaxis.range[0]' in relayoutData:
#         f1 = int(relayoutData['xaxis.range[0]'])
#         f2 = int(relayoutData['xaxis.range[1]'])
#     else:
#         f1=const.FULL_FREQS[0]
#         f2=const.FULL_FREQS[-1]
    
#     newLine, freqs, timestamp = fetch_integration(index, h5f, f1, f2, const.SPEC_WIDTH)

#     storeData['spec'].pop(0)
#     storeData['spec'].append(newLine)

#     storeData['freqs'] = freqs

#     storeData['times'] = timestamp-np.arange(const.WATERFALL_HEIGHT)*datetime.timedelta(seconds=1)

#     app.logger.info(f"Updated the store with timestamp {timestamp}")
#     return storeData



# app.clientside_callback(
#     ClientsideFunction(
#         namespace='clientside',
#         function_name='update_plots'
#     ),
#     [
#         Output("spec", "extendData"),
#         Output("waterfall", "extendData"),
#     ],
#     [
#         Input("update_gui", "n_intervals"), # output n_intervals, an int
#     ],
#     State("userStore", "data"),
#     prevent_initial_call=True
# )

app.clientside_callback(
    """
    function (index, storeData) {
        if (index !== undefined) {
            console.log("Updating plot from timestamp "+storeData.times[0])
            const updatedSpec = [{y: [storeData.spec[storeData.spec.length-1]], x: [storeData.freqs]}, [0], storeData.freqs.length]
            const updatedWaterfall = [{z: [storeData.spec]}, [0], storeData.spec.length]
            return [updatedSpec, updatedWaterfall];
        } else {
            throw window.dash_clientside.PreventUpdate;
        }
    }
    """,
    [
        Output("spec", "extendData"),
        Output("waterfall", "extendData"),
    ],
    [
        Input("update_gui", "n_intervals"), # output n_intervals, an int
    ],
    State("userStore", "data"),
    prevent_initial_call=True
)

# @app.callback(
#     [
#         Output("spec", "extendData"),
#         Output("waterfall", "extendData"),
#     ],
#     [
#         Input("update_gui", "n_intervals"), # output n_intervals, an int
#         # Input("userStore", "data"),
#     ],
#     State("userStore", "data"),
#     prevent_initial_call=True
# )
# def update_plots(index, storeData):
#     app.logger.info(f'Updating plot {index}')
#     updatedSpec = [{'y': [storeData['spec'][const.WATERFALL_HEIGHT-1]], 'x': [storeData['freqs']]}, [0], const.SPEC_WIDTH]
#     updatedWaterfall = [{'z': [storeData['spec']]}, [0], const.WATERFALL_HEIGHT]
#     return [updatedSpec, updatedWaterfall]

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

