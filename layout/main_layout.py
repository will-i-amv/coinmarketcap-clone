from dash import html, dcc

from layout.crypto_graph_section import title, crypto_params_selector, crypto_graph
from layout.fear_and_greed_index import fng_gauge_table, fng_selector_graph, fng_info_button
from layout.rsi_indicator import rsi_period_selector, rsi_graph, rsi_info_button
from layout.current_prices_table import fiat_rates_led_display, crypto_prices_table, warning_alert
from layout.moving_averages import ma_params_selector, ma_graph, ma_info_button

crypto_tabs = html.Div(
    [
        dcc.Tabs([
            dcc.Tab(
                label='Ranking',
                children=[
                    fiat_rates_led_display,
                    warning_alert,
                    crypto_prices_table,
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
                    fng_gauge_table,
                    fng_selector_graph,
                    fng_info_button
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
                    rsi_period_selector,
                    rsi_graph,
                    rsi_info_button
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
                    ma_params_selector,
                    ma_graph,
                    ma_info_button
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
