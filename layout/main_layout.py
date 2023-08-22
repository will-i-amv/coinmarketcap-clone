import datetime as dt

from dash import html, dcc

from constants import CURRENCY_SYMBOLS, TODAY
from layout.tab_sections import ranking, fng, ma, rsi 


def render_layout(asset_names, df_fng):
    title = (
        html.H1(
            children="Dash application for cryptocurrencies monitoring",
            className="main-header"
        )
    )
    crypto_params_selector = (
        html.Section(
            children=[
                html.Div(
                    children=[
                        html.Label('Select base currency: '),
                        dcc.Dropdown(
                            id='base-currency',
                            options=list(CURRENCY_SYMBOLS.keys()),
                            value='USD'
                        ),
                    ],
                    className='select-data higher-width'
                ),
                html.Div(
                    children=[
                        html.Label('Select crypto: '),
                        dcc.Dropdown(
                            id='crypto-dropdown',
                            options=asset_names,
                            value='bitcoin',
                            multi=True
                        ),
                    ],
                    className='select-data higher-width'
                ),
                html.Div(
                    children=[
                        html.Label('Select start date: '),
                        html.Div(
                            dcc.DatePickerSingle(
                                id='start-date-picker',
                                min_date_allowed=dt.datetime(2015, 1, 1),
                                max_date_allowed=(
                                    dt.datetime.today() -
                                    dt.timedelta(days=7)
                                ),
                                date=dt.datetime(2019, 1, 1),
                                initial_visible_month=dt.datetime(2019, 1, 1)
                            ),
                        ),
                    ],
                    className='select-data small-width'
                ),
                html.Div(
                    children=[
                        html.Label('Select end date: '),
                        html.Div(
                            dcc.DatePickerSingle(
                                id='end-date-picker',
                                min_date_allowed=dt.datetime(2015, 1, 1),
                                max_date_allowed=TODAY,
                                date=TODAY,
                                initial_visible_month=TODAY,
                            ),
                        ),
                    ],
                    className='select-data small-width'
                )
            ],
            className='main-options'
        )
    )
    crypto_graph = (
        html.Section(
            dcc.Graph(id='crypto-graph'),
            className='graph-container'
        )
    )
    crypto_tabs = html.Div(
        [
            dcc.Tabs([
                dcc.Tab(
                    label='Ranking',
                    children=[
                        ranking.fiat_rates_led_display,
                        ranking.warning_alert,
                        ranking.crypto_prices_table,
                    ],
                    style={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'borderBottom': '1px solid #d6d6d6',
                    },
                    selected_style={
                        'backgroundColor': '#111111',
                        'borderTop': '2px solid #007eff',
                        'borderBottom': '1px solid #d6d6d6',
                        'color': '#007eff',
                    },
                    className="tab-box"
                ),
                dcc.Tab(
                    label='Fear and Greed Index',
                    children=[
                        fng.render_fng_table(df_fng),
                        fng.fng_selector_graph,
                        fng.fng_info_button
                    ],
                    style={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'borderBottom': '1px solid #d6d6d6',
                    },
                    selected_style={
                        'backgroundColor': '#111111',
                        'borderTop': '2px solid #007eff',
                        'borderBottom': '1px solid #d6d6d6',
                        'color': '#007eff',
                    },
                    className="tab-box"
                ),
                dcc.Tab(
                    label='Relative Strength Index',
                    children=[
                        rsi.rsi_period_selector,
                        rsi.rsi_graph,
                        rsi.rsi_info_button
                    ],
                    style={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'borderBottom': '1px solid #d6d6d6',
                    },
                    selected_style={
                        'backgroundColor': '#111111',
                        'borderTop': '2px solid #007eff',
                        'borderBottom': '1px solid #d6d6d6',
                        'color': '#007eff',
                    },
                    className="tab-box"
                ),
                dcc.Tab(
                    label='Moving Averages',
                    children=[
                        ma.ma_params_selector,
                        ma.ma_graph,
                        ma.ma_info_button
                    ],
                    style={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'borderBottom': '1px solid #d6d6d6',
                    },
                    selected_style={
                        'backgroundColor': '#111111',
                        'borderTop': '2px solid #007eff',
                        'borderBottom': '1px solid #d6d6d6',
                        'color': '#007eff',
                    },
                    className="tab-box"
                ),
            ])
        ],
        className='tabs-menu'
    )
    layout = html.Div(
        className="main",
        children=[
            title,
            crypto_params_selector,
            crypto_graph,
            crypto_tabs,
        ]
    )
    return layout