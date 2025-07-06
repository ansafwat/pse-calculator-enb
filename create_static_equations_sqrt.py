#!/usr/bin/env python3
"""
Create static HTML representations of equations for the PSE calculator
"""

from dash import html

def create_sonic_flow_equation():
    """Create HTML for sonic (choked) flow equation"""
    return html.Div(
        className="static-equation",
        children=[
            html.Span("ṁ", className="var-with-dot"),
            html.Sub("choked"),
            " = C",
            html.Sub("d"),
            " · A · P",
            html.Sub("1"),
            " · ",
            html.Span([
                html.Span("√"),
                html.Span([
                    html.Span([
                        html.Span("k · M", className="frac-num"),
                        html.Span(["Z · R", html.Sub("g"), " · T", html.Sub("1")], className="frac-den")
                    ], className="frac")
                ], className="sqrt-content")
            ], className="sqrt"),
            " · ",
            html.Span([
                html.Span("(", className="paren"),
                html.Span([
                    html.Span("2", className="frac-num"),
                    html.Span("k+1", className="frac-den")
                ], className="frac"),
                html.Span(")", className="paren"),
                html.Sup([
                    html.Span([
                        html.Span("k+1", className="frac-num"),
                        html.Span("2(k-1)", className="frac-den")
                    ], className="frac frac-small")
                ], className="complex-exp")
            ], className="paren-group")
        ]
    )

def create_subsonic_flow_equation():
    """Create HTML for subsonic flow equation"""
    return html.Div(
        className="static-equation",
        children=[
            html.Span("ṁ", className="var-with-dot"),
            " = C",
            html.Sub("d"),
            " · A · P",
            html.Sub("1"),
            " · ",
            html.Span([
                html.Span("√"),
                html.Span([
                    html.Span([
                        html.Span("2 · M", className="frac-num"),
                        html.Span(["Z · R", html.Sub("g"), " · T", html.Sub("1")], className="frac-den")
                    ], className="frac"),
                    " · ",
                    html.Span([
                        html.Span("k", className="frac-num"),
                        html.Span("k-1", className="frac-den")
                    ], className="frac"),
                    " · ",
                    html.Span([
                        html.Span("[", className="bracket"),
                        html.Span([
                            html.Span("(", className="paren"),
                            html.Span([
                                html.Span(["P", html.Sub("2")], className="frac-num"),
                                html.Span(["P", html.Sub("1")], className="frac-den")
                            ], className="frac"),
                            html.Span(")", className="paren"),
                            html.Sup([
                                html.Span([
                                    html.Span("2", className="frac-num"),
                                    html.Span("k", className="frac-den")
                                ], className="frac frac-small")
                            ])
                        ], className="paren-group"),
                        " - ",
                        html.Span([
                            html.Span("(", className="paren"),
                            html.Span([
                                html.Span(["P", html.Sub("2")], className="frac-num"),
                                html.Span(["P", html.Sub("1")], className="frac-den")
                            ], className="frac"),
                            html.Span(")", className="paren"),
                            html.Sup([
                                html.Span([
                                    html.Span("k+1", className="frac-num"),
                                    html.Span("k", className="frac-den")
                                ], className="frac frac-small")
                            ])
                        ], className="paren-group"),
                        html.Span("]", className="bracket")
                    ], className="bracket-group")
                ], className="sqrt-content")
            ], className="sqrt")
        ]
    )

def create_critical_pressure_equation():
    """Create HTML for critical pressure ratio equation"""
    return html.Div(
        className="static-equation",
        children=[
            html.Span([
                html.Span(["P", html.Sub("choked")], className="frac-num"),
                html.Span(["P", html.Sub("1")], className="frac-den")
            ], className="frac"),
            " = ",
            html.Span([
                html.Span("(", className="paren"),
                html.Span([
                    html.Span("2", className="frac-num"),
                    html.Span("k+1", className="frac-den")
                ], className="frac"),
                html.Span(")", className="paren"),
                html.Sup([
                    html.Span([
                        html.Span("k", className="frac-num"),
                        html.Span("k-1", className="frac-den")
                    ], className="frac frac-small")
                ])
            ], className="paren-group")
        ]
    )

def create_sonic_simplified_equation():
    """Create HTML for simplified sonic flow equation"""
    return html.Div(
        className="static-equation",
        children=[
            html.Span("ṁ", className="var-with-dot"),
            html.Sub("choked"),
            " = C",
            html.Sub("d"),
            " · A · P",
            html.Sub("1"),
            " · ",
            html.Span([
                html.Span("√"),
                html.Span([
                    html.Span([
                        html.Span("γ", className="frac-num"),
                        html.Span(["R · T", html.Sub("1")], className="frac-den")
                    ], className="frac")
                ], className="sqrt-content")
            ], className="sqrt"),
            " · K",
            html.Sub("sonic")
        ]
    )

def create_sonic_factor_equation():
    """Create HTML for sonic factor equation"""
    return html.Div(
        className="static-equation-small",
        children=[
            "K",
            html.Sub("sonic"),
            " = ",
            html.Span([
                html.Span("(", className="paren"),
                html.Span([
                    html.Span("2", className="frac-num"),
                    html.Span("γ+1", className="frac-den")
                ], className="frac"),
                html.Span(")", className="paren"),
                html.Sup([
                    html.Span([
                        html.Span("γ+1", className="frac-num"),
                        html.Span("2(γ-1)", className="frac-den")
                    ], className="frac frac-small")
                ])
            ], className="paren-group")
        ]
    )

def create_subsonic_simplified_equation():
    """Create HTML for simplified subsonic flow equation"""
    return html.Div(
        className="static-equation",
        children=[
            html.Span("ṁ", className="var-with-dot"),
            " = C",
            html.Sub("d"),
            " · A · P",
            html.Sub("1"),
            " · ",
            html.Span([
                html.Span("√"),
                html.Span([
                    html.Span([
                        html.Span("2 · γ", className="frac-num"),
                        html.Span(["(γ-1) · R · T", html.Sub("1")], className="frac-den")
                    ], className="frac")
                ], className="sqrt-content")
            ], className="sqrt"),
            " · ",
            html.Span([
                html.Span("√"),
                html.Span([
                    html.Span([
                        html.Span("(", className="paren"),
                        html.Span([
                            html.Span(["P", html.Sub("2")], className="frac-num"),
                            html.Span(["P", html.Sub("1")], className="frac-den")
                        ], className="frac"),
                        html.Span(")", className="paren"),
                        html.Sup([
                            html.Span([
                                html.Span("2", className="frac-num"),
                                html.Span("γ", className="frac-den")
                            ], className="frac frac-small")
                        ])
                    ], className="paren-group"),
                    " - ",
                    html.Span([
                        html.Span("(", className="paren"),
                        html.Span([
                            html.Span(["P", html.Sub("2")], className="frac-num"),
                            html.Span(["P", html.Sub("1")], className="frac-den")
                        ], className="frac"),
                        html.Span(")", className="paren"),
                        html.Sup([
                            html.Span([
                                html.Span("γ+1", className="frac-num"),
                                html.Span("γ", className="frac-den")
                            ], className="frac frac-small")
                        ])
                    ], className="paren-group")
                ], className="sqrt-content")
            ], className="sqrt")
        ]
    )

def create_flow_condition_sonic():
    """Create HTML for sonic flow condition"""
    return html.Div(
        className="static-equation-small",
        children=[
            html.Span([
                html.Span(["P", html.Sub("2")], className="frac-num"),
                html.Span(["P", html.Sub("1")], className="frac-den")
            ], className="frac"),
            " ≤ ",
            html.Span([
                html.Span("(", className="paren"),
                html.Span([
                    html.Span("2", className="frac-num"),
                    html.Span("γ+1", className="frac-den")
                ], className="frac"),
                html.Span(")", className="paren"),
                html.Sup([
                    html.Span([
                        html.Span("γ", className="frac-num"),
                        html.Span("γ-1", className="frac-den")
                    ], className="frac frac-small")
                ])
            ], className="paren-group")
        ]
    )

def create_flow_condition_subsonic():
    """Create HTML for subsonic flow condition"""
    return html.Div(
        className="static-equation-small",
        children=[
            html.Span([
                html.Span(["P", html.Sub("2")], className="frac-num"),
                html.Span(["P", html.Sub("1")], className="frac-den")
            ], className="frac"),
            " > ",
            html.Span([
                html.Span("(", className="paren"),
                html.Span([
                    html.Span("2", className="frac-num"),
                    html.Span("γ+1", className="frac-den")
                ], className="frac"),
                html.Span(")", className="paren"),
                html.Sup([
                    html.Span([
                        html.Span("γ", className="frac-num"),
                        html.Span("γ-1", className="frac-den")
                    ], className="frac frac-small")
                ])
            ], className="paren-group")
        ]
    )

# Variable definitions as Dash HTML components
def create_variable_definition(symbol_html, description):
    """Create a variable definition with proper HTML structure"""
    return html.Span([symbol_html, f" = {description}"])

variable_definitions = {
    'mdot': create_variable_definition(html.Span([html.Span("ṁ", className="var-with-dot")]), "Mass flow rate (kg/s)"),
    'cd': create_variable_definition(html.Span(["C", html.Sub("d")]), "Discharge coefficient"),
    'area': create_variable_definition("A", "Orifice area (m²)"),
    'p1': create_variable_definition(html.Span(["P", html.Sub("1")]), "Upstream pressure (Pa abs)"),
    'p2': create_variable_definition(html.Span(["P", html.Sub("2")]), "Downstream pressure (Pa abs)"),
    'gamma': create_variable_definition("k or γ", "Specific heat ratio"),
    'mw': create_variable_definition("M", "Molecular weight (kg/kmol)"),
    'z': create_variable_definition("Z", "Compressibility factor"),
    'r': create_variable_definition("R", "Specific gas constant (J/kg·K)"),
    't1': create_variable_definition(html.Span(["T", html.Sub("1")]), "Upstream temperature (K)"),
}

# Export all equations as Dash components
equations = {
    'sonic_flow': create_sonic_flow_equation(),
    'subsonic_flow': create_subsonic_flow_equation(),
    'critical_pressure': create_critical_pressure_equation(),
    'sonic_simplified': create_sonic_simplified_equation(),
    'sonic_factor': create_sonic_factor_equation(),
    'subsonic_simplified': create_subsonic_simplified_equation(),
    'flow_condition_sonic': create_flow_condition_sonic(),
    'flow_condition_subsonic': create_flow_condition_subsonic(),
}

if __name__ == "__main__":
    # Test output
    print("Static equations created as Dash HTML components")
    for name in equations.keys():
        print(f"- {name}")