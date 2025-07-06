#!/usr/bin/env python3
"""
Equipment Failure Hole Sizes table component for tooltips
"""

from dash import html
import dash_mantine_components as dmc

def create_equipment_table_mini():
    """Create a mini version of the equipment failure hole sizes table for tooltips"""
    return dmc.Table(
        striped=True,
        highlightOnHover=True,
        className="equipment-table-mini",
        style={"fontSize": "0.8rem"},
        children=[
            html.Thead([
                html.Tr([
                    html.Th("Equipment", style={"padding": "0.4rem"}),
                    html.Th("Failure", style={"padding": "0.4rem"}),
                    html.Th("Hole Size", style={"padding": "0.4rem"})
                ])
            ]),
            html.Tbody([
                # Flanges
                html.Tr([
                    html.Td(html.Strong("Flanges"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.15)", "padding": "0.4rem", "color": "#6c757d"})
                ]),
                html.Tr([
                    html.Td("CAF/SWJ", style={"padding": "0.4rem"}),
                    html.Td("All", style={"padding": "0.4rem"}),
                    html.Td("0.1 mm²", style={"padding": "0.4rem"})
                ]),
                html.Tr([
                    html.Td("RTJ", style={"padding": "0.4rem"}),
                    html.Td("All", style={"padding": "0.4rem"}),
                    html.Td("0.25 mm²", style={"padding": "0.4rem"})
                ]),
                # Valves
                html.Tr([
                    html.Td(html.Strong("Valves"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.15)", "padding": "0.4rem", "color": "#6c757d"})
                ]),
                html.Tr([
                    html.Td("< 150 mm", style={"padding": "0.4rem"}),
                    html.Td("Severe", style={"padding": "0.4rem"}),
                    html.Td("2.5 mm²", style={"padding": "0.4rem"})
                ]),
                html.Tr([
                    html.Td("< 150 mm", style={"padding": "0.4rem"}),
                    html.Td("Small", style={"padding": "0.4rem"}),
                    html.Td("0.25 mm²", style={"padding": "0.4rem"})
                ]),
                html.Tr([
                    html.Td("> 150 mm", style={"padding": "0.4rem"}),
                    html.Td("All", style={"padding": "0.4rem"}),
                    html.Td("0.25 mm²", style={"padding": "0.4rem"})
                ]),
                # Compressors
                html.Tr([
                    html.Td(html.Strong("Compressors"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.15)", "padding": "0.4rem", "color": "#6c757d"})
                ]),
                html.Tr([
                    html.Td("Centrifugal", style={"padding": "0.4rem"}),
                    html.Td("Seal", style={"padding": "0.4rem"}),
                    html.Td("50-250 mm²", style={"padding": "0.4rem"})
                ]),
                html.Tr([
                    html.Td("Reciprocating", style={"padding": "0.4rem"}),
                    html.Td("All", style={"padding": "0.4rem"}),
                    html.Td("2.5 mm²", style={"padding": "0.4rem"})
                ]),
                # Other
                html.Tr([
                    html.Td(html.Strong("Other"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.15)", "padding": "0.4rem", "color": "#6c757d"})
                ]),
                html.Tr([
                    html.Td("Small bore", style={"padding": "0.4rem"}),
                    html.Td("< Full", style={"padding": "0.4rem"}),
                    html.Td("0.25 mm²", style={"padding": "0.4rem"})
                ]),
                html.Tr([
                    html.Td("Drains", style={"padding": "0.4rem"}),
                    html.Td("All", style={"padding": "0.4rem"}),
                    html.Td("Pipe Ø", style={"padding": "0.4rem"})
                ])
            ])
        ]
    )