import dash_daq as daq
import dash_bootstrap_components as dbc
from dash import html, dash_table

from constants import COLORS, CURRENCY_SYMBOLS


warning_alert = (
    html.Section(
        children=[
            dbc.Alert(
                color="warning",
                id="alert",
                dismissable=True,
                is_open=False,
            ),
        ],
        className='main-options'
    )
)
fiat_rates_led_display = (
    html.Section(
        children=[
            html.Div(
                children=[
                    daq.LEDDisplay(
                        id='LED-display-usd',
                        label=f"USD [{CURRENCY_SYMBOLS['USD']}]",
                        backgroundColor='#111111'
                    ),
                ],
                className='select-data higher-width'
            ),
            html.Div(
                children=[
                    daq.LEDDisplay(
                        id='LED-display-pln',
                        label=f"PLN [{CURRENCY_SYMBOLS['PLN']}]",
                        backgroundColor='#111111'
                    ),
                ],
                className='select-data higher-width'
            ),
            html.Div(
                children=[
                    daq.LEDDisplay(
                        id='LED-display-eur',
                        label=f"EUR [{CURRENCY_SYMBOLS['EUR']}]",
                        backgroundColor='#111111'
                    ),
                ],
                className='select-data higher-width'
            ),
            html.Div(
                children=[
                    daq.LEDDisplay(
                        id='LED-display-gpb',
                        label=f"GBP [{CURRENCY_SYMBOLS['GBP']}]",
                        backgroundColor='#111111'
                    ),
                ],
                className='select-data higher-width'
            ),
            html.Div(
                children=[
                    daq.LEDDisplay(
                        id='LED-display-chf',
                        label=f"CHF [{CURRENCY_SYMBOLS['CHF']}]",
                        backgroundColor='#111111'
                    ),
                ],
                className='select-data higher-width'
            )
        ],
        className='main-options'
    )
)
crypto_prices_table = (
    html.Section(
        children=[
            html.H2(id="table-header"),
            dash_table.DataTable(
                id='crypto-table',
                merge_duplicate_headers=True,
                fill_width=False,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': '#007eff',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'fontSize': '15px'
                },
                style_cell={
                    'padding': '10px',
                    'backgroundColor': COLORS['background'],
                    'color': COLORS['text'],
                    'textAlign': 'center',
                    'marginLeft': 'auto',
                    'marginRight': 'auto'
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{Change24h[%]} < 0',
                            'column_id': 'Change24h[%]'
                        },
                        'color': 'tomato'
                    },
                    {
                        'if': {
                            'filter_query': '{Change24h[%]} > 0',
                            'column_id': 'Change24h[%]'
                        },
                        'color': 'rgb(8, 130, 8)'
                    },
                    {
                        'if': {
                            'column_id': 'Logo'
                        },
                        'padding-top': '25px'
                    },
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(30, 30, 30)',
                    }
                ]
            ),
        ],
        className='main-table-options'
    )
)
