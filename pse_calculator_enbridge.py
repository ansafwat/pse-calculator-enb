import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_iconify import DashIconify
import numpy as np
import pandas as pd
import json
from datetime import datetime
import uuid
import os
from create_static_equations import equations as static_equations, variable_definitions
from equipment_table_component import create_equipment_table_mini

# Gas properties: gamma (γ), R (J/kg·K), molecular weight (g/mol)
gas_data = {
    'Air': {'gamma': 1.4, 'R': 287, 'MW': 28.96},
    'Nitrogen': {'gamma': 1.4, 'R': 296.8, 'MW': 28.01},
    'Oxygen': {'gamma': 1.4, 'R': 259.8, 'MW': 32.0},
    'Helium': {'gamma': 1.66, 'R': 2077, 'MW': 4.0},
    'Hydrogen': {'gamma': 1.41, 'R': 4124, 'MW': 2.02},
    'CO2': {'gamma': 1.29, 'R': 188.9, 'MW': 44.01},
    'Natural Gas': {'gamma': 1.32, 'R': 518.3, 'MW': 16.04},
    'Argon': {'gamma': 1.67, 'R': 208.1, 'MW': 39.95},
}

# Unit conversion factors
pressure_units = {
    'bar(g)': 1e5,       # to Pa
    'psi(g)': 6894.76,   # to Pa
    'kPa(g)': 1e3,       # to Pa
    'MPa(g)': 1e6,       # to Pa
}

temperature_units = {
    '°C': lambda t: t + 273.15,       # to K
    '°F': lambda t: (t - 32) * 5/9 + 273.15,  # to K
    'K': lambda t: t,                 # already K
}

area_units = {
    'mm²': 1e-6,    # to m²
    'cm²': 1e-4,    # to m²
    'in²': 6.4516e-4,  # to m²
    'm²': 1,        # already m²
}

time_units = {
    'sec': 1,         # to seconds
    'min': 60,        # to seconds
    'hr': 3600,       # to seconds
}

# Output unit conversion functions
def convert_output_units(mdot_kgs, gas, unit):
    if unit == 'kg/s':
        return mdot_kgs, 'kg'
    elif unit == 'lb/s':
        return mdot_kgs * 2.20462, 'lb'
    elif unit == 'MSCF/hr':
        R_universal = 8314.5  # J/(kmol·K)
        MW = gas_data[gas]['MW']  # g/mol = kg/kmol
        std_temp = 288.71  # K (60°F)
        std_press = 101325  # Pa (1 atm)
        density = std_press * MW / (R_universal * std_temp)  # kg/m³
        vol_flow_m3_s = mdot_kgs / density  # m³/s
        scf_s = vol_flow_m3_s * 35.3147  # ft³/s
        return scf_s * 3600 / 1000, 'MSCF'  # MSCF/hr
    elif unit == 'st m³/hr':
        R_universal = 8314.5  # J/(kmol·K)
        MW = gas_data[gas]['MW']  # g/mol = kg/kmol
        std_temp = 288.15  # K (15°C)
        std_press = 101325  # Pa (1 atm)
        density = std_press * MW / (R_universal * std_temp)  # kg/m³
        vol_flow_m3_s = mdot_kgs / density  # m³/s
        return vol_flow_m3_s * 3600, 'st m³'  # m³/hr

ATM_PRESSURE = 101325  # Pa (standard atmospheric pressure)

def mass_flow_rate(Cd, A, P0, P2, T0, gamma, R):
    # Sonic (choked) condition
    critical_pressure_ratio = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    if P2 / P0 <= critical_pressure_ratio:
        mdot = (
            Cd * A * P0 * np.sqrt(gamma / (R * T0)) *
            ((2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1))))
        )
    else:
        mdot = (
            Cd * A * P0 * np.sqrt(
                2 * gamma / (R * T0 * (gamma - 1)) *
                ((P2 / P0) ** (2 / gamma) - (P2 / P0) ** ((gamma + 1) / gamma))
            )
        )
    return mdot

def calculate_required_area(target_tier, release_type, site, duration_seconds, Cd, P0, P2, T0, gamma, R, gas):
    """Calculate the required orifice area to achieve a target tier"""
    if site != "GTM US":
        return None, "Tier calculation only available for GTM US"
    
    # Determine target flow rate or total release based on tier and type
    if release_type == "Indoor":
        if duration_seconds > 3600:  # Greater than 1 hour - use flow rate thresholds
            if target_tier == "1":
                target_flow_rate_mscf = 2.47 * 1.0001  # Slightly above minimum for Tier 1
            elif target_tier == "2":
                target_flow_rate_mscf = 1.41 * 1.0001  # Slightly above minimum for Tier 2
            
            # Convert MSCF/hr to kg/s
            R_universal = 8314.5
            MW = gas_data[gas]['MW']
            std_temp = 288.71  # K (60°F)
            std_press = 101325  # Pa (1 atm)
            density = std_press * MW / (R_universal * std_temp)  # kg/m³
            target_mdot_kgs = (target_flow_rate_mscf * 1000 / 3600) / 35.3147 * density
        else:  # Less than 1 hour - use total release thresholds
            if target_tier == "1":
                target_total_mscf = 2.47 * 1.0001  # Slightly above minimum for Tier 1
            elif target_tier == "2":
                target_total_mscf = 1.41 * 1.0001  # Slightly above minimum for Tier 2
            
            # Convert to flow rate for calculation
            target_flow_rate_mscf = target_total_mscf * 3600 / duration_seconds
            
            # Convert to kg/s
            R_universal = 8314.5
            MW = gas_data[gas]['MW']
            std_temp = 288.71
            std_press = 101325
            density = std_press * MW / (R_universal * std_temp)
            target_mdot_kgs = (target_flow_rate_mscf * 1000 / 3600) / 35.3147 * density
    
    elif release_type == "Outdoor":
        if target_tier == "1":
            target_total_mscf = 3000 * 1.0001  # Slightly above minimum for Tier 1
        elif target_tier == "2":
            target_total_mscf = 300 * 1.0001  # Slightly above minimum for Tier 2
        
        # Convert to flow rate
        target_flow_rate_mscf = target_total_mscf * 3600 / duration_seconds
        
        # Convert to kg/s
        R_universal = 8314.5
        MW = gas_data[gas]['MW']
        std_temp = 288.71
        std_press = 101325
        density = std_press * MW / (R_universal * std_temp)
        target_mdot_kgs = (target_flow_rate_mscf * 1000 / 3600) / 35.3147 * density
    
    # Calculate required area by rearranging mass flow equation
    critical_pressure_ratio = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    
    if P2 / P0 <= critical_pressure_ratio:  # Sonic flow
        denominator = Cd * P0 * np.sqrt(gamma / (R * T0)) * ((2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1))))
        required_area = target_mdot_kgs / denominator
    else:  # Subsonic flow
        flow_term = np.sqrt(2 * gamma / (R * T0 * (gamma - 1)) * ((P2 / P0) ** (2 / gamma) - (P2 / P0) ** ((gamma + 1) / gamma)))
        denominator = Cd * P0 * flow_term
        required_area = target_mdot_kgs / denominator
    
    return required_area, None

# File path for persistent storage
CALCULATIONS_FILE = 'saved_calculations.json'

# Utility functions for data persistence
def load_calculations_from_file():
    """Load calculations from JSON file"""
    try:
        if os.path.exists(CALCULATIONS_FILE):
            with open(CALCULATIONS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading calculations: {e}")
        return []

def save_calculations_to_file(data):
    """Save calculations to JSON file"""
    try:
        with open(CALCULATIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving calculations: {e}")
        return False

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True
)

# Custom CSS for Enbridge theme - now loaded from external file
app.index_string = '''
<!DOCTYPE html>
<html class="theme-dark">
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="manifest" href="/assets/manifest.json">
        <meta name="theme-color" content="#d4af37">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="/assets/main.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout with Mantine Provider
app.layout = dmc.MantineProvider(
    theme={
        "colorScheme": "dark",
        "primaryColor": "yellow",
        "fontFamily": "'Inter', sans-serif",
    },
    children=[
        # Store components
        dcc.Store(id='calculations-store', data=load_calculations_from_file()),
        dcc.Store(id='current-calculation-id', data=None),
        
        # Header
        dmc.Paper(
            p="md",
            className="app-header",
            children=[
                dmc.Container(
                    size="xl",
                    children=[
                        dmc.Group(
                            justify="space-between",
                            children=[
                                dmc.Group(
                                    gap="md",
                                    children=[
                                        dmc.ThemeIcon(
                                            DashIconify(icon="mdi:gas-cylinder", width=28),
                                            size=44,
                                            radius="md",
                                            variant="gradient",
                                            gradient={"from": "yellow", "to": "orange"}
                                        ),
                                        dmc.Stack(
                                            gap=0,
                                            children=[
                                                dmc.Title("PSE Flow Calculator", order=3),
                                                dmc.Text("Gas Orifice Mass Flow Analysis", size="sm", c="dimmed")
                                            ]
                                        )
                                    ]
                                ),
                                dmc.Badge(
                                    "ENBRIDGE",
                                    size="lg",
                                    radius="sm",
                                    variant="gradient",
                                    gradient={"from": "yellow", "to": "orange"}
                                )
                            ]
                        )
                    ]
                )
            ]
        ),
        
        # Main content
        dmc.Container(
            size="xl",
            children=[
                dmc.Tabs(
                    id="main-tabs",
                    value="calculator",
                    children=[
                        dmc.TabsList([
                            dmc.TabsTab("Calculator", value="calculator", leftSection=DashIconify(icon="tabler:calculator", width=16)),
                            dmc.TabsTab("Saved Calculations", value="saved", leftSection=DashIconify(icon="tabler:database", width=16)),
                            dmc.TabsTab("Information", value="info", leftSection=DashIconify(icon="tabler:info-circle", width=16))
                        ]),
                        
                        # Calculator Tab
                        dmc.TabsPanel(
                            value="calculator",
                            pt="xl",
                            children=[
                                dmc.Grid(
                                    gutter="xl",
                                    children=[
                                        # Input Column
                                        dmc.GridCol(
                                            span={"base": 12, "md": 7},
                                            children=[
                                                dmc.Paper(
                                                    p="xl",
                                                    radius="md",
                                                    children=[
                                                        dmc.Stack(
                                                            gap="lg",
                                                            children=[
                                                                # Title
                                                                dmc.Title("Input Parameters", order=4, className="section-title"),
                                                                
                                                                # User Information
                                                                dmc.Paper(
                                                                    p="md",
                                                                    className="input-card",
                                                                    children=[
                                                                        dmc.Text("User Information", size="sm", fw=600, c="yellow", mb="sm"),
                                                                        dmc.Grid(
                                                                            gutter="md",
                                                                            children=[
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.TextInput(
                                                                                            id='user-name',
                                                                                            label='Name',
                                                                                            placeholder="Enter your name",
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:user", width=16)
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.TextInput(
                                                                                            id='calculation-title',
                                                                                            label='Calculation Title',
                                                                                            placeholder="Enter title",
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:tag", width=16),
                                                                                            rightSection=dmc.Tooltip(
                                                                                                label="Enter facility name and equipment tag/location where leak occurred",
                                                                                                children=[DashIconify(icon="tabler:info-circle", width=16)]
                                                                                            )
                                                                                        )
                                                                                    ]
                                                                                )
                                                                            ]
                                                                        )
                                                                    ]
                                                                ),
                                                                
                                                                # Gas Properties
                                                                dmc.Paper(
                                                                    p="md",
                                                                    className="input-card",
                                                                    children=[
                                                                        dmc.Text("Gas Properties", size="sm", fw=600, c="yellow", mb="sm"),
                                                                        dmc.Grid(
                                                                            gutter="md",
                                                                            children=[
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.Select(
                                                                                            id='gas-dropdown',
                                                                                            label='Gas Type',
                                                                                            data=list(gas_data.keys()),
                                                                                            value='Natural Gas',
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:gas-station", width=16),
                                                                                            searchable=False,
                                                                                            required=True,
                                                                                            allowDeselect=False
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.Select(
                                                                                            id='release-type-dropdown',
                                                                                            label='Release Type',
                                                                                            data=['Indoor', 'Outdoor'],
                                                                                            value='Outdoor',
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:wind", width=16),
                                                                                            searchable=False,
                                                                                            required=True,
                                                                                            allowDeselect=False
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.Select(
                                                                                            id='site-dropdown',
                                                                                            label='Site',
                                                                                            data=['GTM US', 'GTM Canada'],
                                                                                            value='GTM US',
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:map-pin", width=16),
                                                                                            searchable=False,
                                                                                            required=True,
                                                                                            allowDeselect=False
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                dmc.GridCol(
                                                                                    span=6,
                                                                                    children=[
                                                                                        dmc.Select(
                                                                                            id='cd-dropdown',
                                                                                            label='Discharge Coefficient (Cd)',
                                                                                            data=[
                                                                                                {'label': '0.61 - Sharp-edged', 'value': '0.61'},
                                                                                                {'label': '0.98 - Well-rounded', 'value': '0.98'},
                                                                                                {'label': '0.85 - Typical PSV', 'value': '0.85'}
                                                                                            ],
                                                                                            value='0.61',
                                                                                            size="sm",
                                                                                            leftSection=DashIconify(icon="tabler:percentage", width=16),
                                                                                            searchable=False,
                                                                                            required=True,
                                                                                            allowDeselect=False
                                                                                        )
                                                                                    ]
                                                                                )
                                                                            ]
                                                                        )

                                                                    ]
                                                                ),
                                                                
                                                                # Operating Conditions
                                                                dmc.Paper(
                                                                    p="md",
                                                                    className="input-card",
                                                                    children=[
                                                                        dmc.Text("Operating Conditions", size="sm", fw=600, c="yellow", mb="sm"),
                                                                        dmc.Stack(
                                                                            gap="md",
                                                                            children=[
                                                                                # Pressures
                                                                                dmc.Grid(
                                                                                    gutter="md",
                                                                                    children=[
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Upstream Pressure", size="xs", fw=500),
                                                                                                        dmc.Tooltip(
                                                                                                            label="This is the pipe internal pressure",
                                                                                                            children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                                        )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='p0',
                                                                                                            value=100,
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:gauge", width=16),
                                                                                                            required=True
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='p0-unit',
                                                                                                            data=list(pressure_units.keys()),
                                                                                                            value='psi(g)',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        ),
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Downstream Pressure", size="xs", fw=500),
                                                                                                        dmc.Tooltip(
                                                                                                            label="This is mostly atmospheric pressure and by default it's 0 psig. Don't change unless relieving to somewhere other than atmospheric",
                                                                                                            children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                                        )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='p2',
                                                                                                            value=0,
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:gauge", width=16),
                                                                                                            required=True
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='p2-unit',
                                                                                                            data=list(pressure_units.keys()),
                                                                                                            value='psi(g)',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                
                                                                                # Temperature and Area
                                                                                dmc.Grid(
                                                                                    gutter="md",
                                                                                    children=[
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Temperature", size="xs", fw=500),
                                                                                                        dmc.Tooltip(
                                                                                                            label="This is the temperature of the gas prior to leak/rupture",
                                                                                                            children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                                        )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='t0',
                                                                                                            value=20,
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:temperature", width=16),
                                                                                                            required=True
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='t0-unit',
                                                                                                            data=list(temperature_units.keys()),
                                                                                                            value='°C',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        ),
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Release Duration", size="xs", fw=500),
                                                                                                        dmc.Tooltip(
                                                                                                            label="If you don't know the release duration, use 48 hr",
                                                                                                            children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                                        )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='duration',
                                                                                                            value=10,
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:clock", width=16),
                                                                                                            required=True
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='duration-unit',
                                                                                                            data=list(time_units.keys()),
                                                                                                            value='min',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                
                                                                                # Orifice Configuration
                                                                                dmc.Divider(label="Orifice Configuration", labelPosition="center", my="md"),
                                                                                dmc.Grid(
                                                                                    gutter="md",
                                                                                    children=[
                                                                                        dmc.GridCol(
                                                                                            span=12,
                                                                                            children=[
                                                                                                dmc.Center(
                                                                                                    children=[
                                                                                                        dmc.SegmentedControl(
                                                                                                            id="orifice-input-type",
                                                                                                            value="area",
                                                                                                            data=[
                                                                                                                {"value": "area", "label": "Input by Area"},
                                                                                                                {"value": "diameter", "label": "Input by Diameter"}
                                                                                                            ],
                                                                                                            size="sm"
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        ),
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                # Orifice Area input
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Orifice Area", size="xs", fw=500),
                                                                                                        dmc.Popover(
                                                                                                                        width=400,
                                                                                                                        position="bottom",
                                                                                                                        withArrow=True,
                                                                                                                        shadow="md",
                                                                                                                        children=[
                                                                                                                            dmc.PopoverTarget(
                                                                                                                                DashIconify(
                                                                                                                                    icon="tabler:info-circle", 
                                                                                                                                    width=14, 
                                                                                                                                    color="#868e96",
                                                                                                                                    style={"cursor": "pointer"}
                                                                                                                                )
                                                                                                                            ),
                                                                                                                            dmc.PopoverDropdown(
                                                                                                                                children=[
                                                                                                                                    html.Div(
                                                                                                                                        className="equipment-table-popover-content",
                                                                                                                                        children=[
                                                                                                                                            dmc.Text("Equipment Failure Hole Sizes", fw=600, size="sm", mb="xs"),
                                                                                                                                            create_equipment_table_mini(),
                                                                                                                                            dmc.Text(
                                                                                                                                                "Cox et al. (1990)",
                                                                                                                                                size="xs",
                                                                                                                                                c="dimmed",
                                                                                                                                                mt="xs",
                                                                                                                                                style={"fontStyle": "italic"}
                                                                                                                                            )
                                                                                                                                        ]
                                                                                                                                    )
                                                                                                                                ]
                                                                                                                            )
                                                                                                                        ]
                                                                                                                    )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='area',
                                                                                                            value=10,
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:circle", width=16),
                                                                                                            required=True,
                                                                                                            disabled=False
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='area-unit',
                                                                                                            data=list(area_units.keys()),
                                                                                                            value='mm²',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False,
                                                                                                            disabled=False
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        ),
                                                                                        dmc.GridCol(
                                                                                            span=6,
                                                                                            children=[
                                                                                                # Orifice Diameter input
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.Text("Orifice Diameter", size="xs", fw=500),
                                                                                                        dmc.Tooltip(
                                                                                                            label="Enter the diameter; area will be calculated automatically",
                                                                                                            children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                                        )
                                                                                                    ],
                                                                                                    mb=4
                                                                                                ),
                                                                                                dmc.Group(
                                                                                                    gap="xs",
                                                                                                    children=[
                                                                                                        dmc.NumberInput(
                                                                                                            id='diameter',
                                                                                                            value=3.57,  # sqrt(10/pi) ≈ 3.57 mm default diameter for 10 mm² area
                                                                                                            size="sm",
                                                                                                            className="input-flex",
                                                                                                            leftSection=DashIconify(icon="tabler:ruler", width=16),
                                                                                                            required=True,
                                                                                                            disabled=True
                                                                                                        ),
                                                                                                        dmc.Select(
                                                                                                            id='diameter-unit',
                                                                                                            data=['mm', 'inch'],
                                                                                                            value='mm',
                                                                                                            size="sm",
                                                                                                            className="input-width-small",
                                                                                                            searchable=False,
                                                                                                            allowDeselect=False,
                                                                                                            disabled=True
                                                                                                        )
                                                                                                    ]
                                                                                                )
                                                                                            ]
                                                                                        )
                                                                                    ]
                                                                                )
                                                                            ]
                                                                        )
                                                                    ]
                                                                ),
                                                                
                                                                # Reverse Calculation
                                                                dmc.Paper(
                                                                    p="md",
                                                                    className="input-card",
                                                                    children=[
                                                                        dmc.Group(
                                                                            gap="xs",
                                                                            children=[
                                                                                dmc.Text("Reverse Calculation", size="sm", fw=600, c="yellow"),
                                                                                dmc.Tooltip(
                                                                                    label="Using this feature is not required. It only helps you determine what is the area required to achieve a Tier 1 or Tier 2 release depending on the selected release type (indoor/outdoor)",
                                                                                    children=[DashIconify(icon="tabler:info-circle", width=14, color="#868e96")]
                                                                                )
                                                                            ],
                                                                            mb="sm"
                                                                        ),
                                                                        dmc.Group(
                                                                            align="flex-end",
                                                                            children=[
                                                                                dmc.Select(
                                                                                    id='target-tier-dropdown',
                                                                                    label='Target Tier',
                                                                                    data=['1', '2'],
                                                                                    value='2',
                                                                                    size="sm",
                                                                                    style={'flex': 1},
                                                                                    leftSection=DashIconify(icon="tabler:trophy", width=16),
                                                                                    allowDeselect=False
                                                                                ),
                                                                                dmc.Button(
                                                                                    'Calculate Required Area/Diameter',
                                                                                    id='reverse-calc-btn',
                                                                                    size="sm",
                                                                                    variant="light",
                                                                                    leftSection=DashIconify(icon="tabler:arrows-exchange", width=16),
                                                                                    className="button-calculate"
                                                                                )
                                                                            ]
                                                                        )
                                                                    ]
                                                                ),
                                                                
                                                                # Calculate Button
                                                                dmc.Button(
                                                                    'Calculate Release',
                                                                    id='calc-btn',
                                                                    size="lg",
                                                                    fullWidth=True,
                                                                    leftSection=DashIconify(icon="tabler:calculator", width=20),
                                                                    variant="filled"
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ]
                                        ),
                                        
                                        # Results Column
                                        dmc.GridCol(
                                            span={"base": 12, "md": 5},
                                            children=[
                                                dmc.Paper(
                                                    p="xl",
                                                    radius="md",
                                                    className="results-container",
                                                    children=[
                                                        dmc.Stack(
                                                            gap="lg",
                                                            children=[
                                                                dmc.Group(
                                                                    justify="space-between",
                                                                    children=[
                                                                        dmc.Title("Results", order=4, className="section-title"),
                                                                        dmc.Badge(
                                                                            "Ready",
                                                                            id="status-badge",
                                                                            color="gray",
                                                                            variant="dot"
                                                                        )
                                                                    ]
                                                                ),
                                                                html.Div(id='results', className="results-content"),
                                                                html.Div(id='notifications')
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        
                        # Saved Calculations Tab
                        dmc.TabsPanel(
                            value="saved",
                            pt="xl",
                            children=[
                                dmc.Paper(
                                    p="xl",
                                    radius="md",
                                    children=[
                                        dmc.Stack(
                                            gap="lg",
                                            children=[
                                                dmc.Group(
                                                    justify="space-between",
                                                    mb="md",
                                                    children=[
                                                        dmc.Title("Saved Calculations", order=4, className="section-title"),
                                                        dmc.Badge(
                                                            id="calc-count-badge",
                                                            variant="filled",
                                                            size="lg"
                                                        )
                                                    ]
                                                ),
                                                html.Div(id='calculations-table')
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        
                        # Information Tab
                        dmc.TabsPanel(
                            value="info",
                            pt="xl",
                            children=[
                                dmc.Paper(
                                    p="xl",
                                    radius="md",
                                    children=[
                                        dmc.Stack(
                                            gap="xl",
                                            children=[
                                                # Tiering Thresholds Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Tiering Thresholds", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Table(
                                                                    striped=True,
                                                                    highlightOnHover=True,
                                                                    className="tiering-table",
                                                                    children=[
                                                                        html.Thead([
                                                                            html.Tr([
                                                                                html.Th("Service Fluid Classification", rowSpan=2),
                                                                                html.Th([
                                                                                    "Indoor Release",
                                                                                    html.Br(),
                                                                                    html.Small([
                                                                                        html.Span("( Release Rate Threshold ", style={"white-space": "pre"}),
                                                                                        html.Span("—", style={"margin": "0 4px"}),
                                                                                        html.Span(" 60 minutes )", style={"white-space": "pre"})
                                                                                    ])
                                                                                ], colSpan=2, className="text-center"),
                                                                                html.Th([
                                                                                    "Outdoor Release",
                                                                                    html.Br(),
                                                                                    html.Small([
                                                                                        html.Span("( Total Release Volume Threshold )", style={"white-space": "pre"})
                                                                                    ])
                                                                                ], colSpan=2, className="text-center")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Th("Tier 1", className="tier-1-header"),
                                                                                html.Th("Tier 2", className="tier-2-header"),
                                                                                html.Th("Tier 1", className="tier-1-header"),
                                                                                html.Th("Tier 2", className="tier-2-header")
                                                                            ])
                                                                        ]),
                                                                        html.Tbody([
                                                                            html.Tr([
                                                                                html.Td("Flammable Gases"),
                                                                                html.Td([
                                                                                    "≥ 70 m³",
                                                                                    html.Span(" or ", style={"color": "var(--text-secondary)", "font-style": "italic"}),
                                                                                    "2.47 MSCF",
                                                                                    html.Br(),
                                                                                    html.Span("or ", style={"font-style": "italic"}),
                                                                                    "≥ 50 kg"
                                                                                ]),
                                                                                html.Td([
                                                                                    "≥ 40 m³",
                                                                                    html.Span(" or ", style={"color": "var(--text-secondary)", "font-style": "italic"}),
                                                                                    "1.41 MSCF",
                                                                                    html.Br(),
                                                                                    html.Span("or ", style={"font-style": "italic"}),
                                                                                    "≥ 25 kg"
                                                                                ]),
                                                                                html.Td([
                                                                                    "≥ 85,000 m³",
                                                                                    html.Span(" or ", style={"color": "var(--text-secondary)", "font-style": "italic"}),
                                                                                    "3000 MSCF"
                                                                                ]),
                                                                                html.Td([
                                                                                    "≥ 8,500 m³",
                                                                                    html.Span(" or ", style={"color": "var(--text-secondary)", "font-style": "italic"}),
                                                                                    "300 MSCF"
                                                                                ])
                                                                            ])
                                                                        ])
                                                                    ]
                                                                ),
                                                                dmc.Text("* Indoor release uses 60-minute rate threshold", size="xs", c="dimmed", mt="xs"),
                                                                dmc.Text("* Outdoor release uses total volume threshold", size="xs", c="dimmed")
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                
                                                # Roles and Responsibilities Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Roles and Responsibilities", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Table(
                                                                    striped=True,
                                                                    highlightOnHover=True,
                                                                    className="roles-table",
                                                                    children=[
                                                                        html.Thead([
                                                                            html.Tr([
                                                                                html.Th("Roles", style={"width": "30%"}),
                                                                                html.Th("Responsibilities")
                                                                            ])
                                                                        ]),
                                                                        html.Tbody([
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Regional Technical Staff (Operations)")),
                                                                                html.Td([
                                                                                    html.Ul([
                                                                                        html.Li("Gathers all relevant data from Area Operations Supervisor"),
                                                                                        html.Li("Performs calculations in accordance with this document"),
                                                                                        html.Li("Documents calculations and uploads in PDF format to EnCompass"),
                                                                                        html.Li("Informs personnel accountable for updating gas loss database"),
                                                                                        html.Li("Notifies Compliance team (US) or Regulatory team (Canada)")
                                                                                    ])
                                                                                ])
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td(html.Strong("GTM Measurement Engineer")),
                                                                                html.Td([
                                                                                    html.Ul([
                                                                                        html.Li("Supports Regional Measurement Engineer with questions"),
                                                                                        html.Li("Performs recalculation as necessary")
                                                                                    ])
                                                                                ])
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Area Operations Supervisor")),
                                                                                html.Td([
                                                                                    html.Ul([
                                                                                        html.Li("Provides relevant data to Regional Measurement Engineer")
                                                                                    ])
                                                                                ])
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Process Safety Engineer")),
                                                                                html.Td([
                                                                                    html.Ul([
                                                                                        html.Li("Categorizes PSE based on calculated volume of release")
                                                                                    ])
                                                                                ])
                                                                            ])
                                                                        ])
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                
                                                # Equations Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Calculation Equations", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Stack(
                                                                    gap="lg",
                                                                    children=[
                                                                        # Sonic Flow Equation
                                                                        html.Div([
                                                                            dmc.Text("Sonic (Choked) Flow:", fw=600, size="sm", mb="xs"),
                                                                            html.Div(
                                                                                className="equation-box",
                                                                                children=[static_equations['sonic_flow']]
                                                                            )
                                                                        ]),
                                                                        
                                                                        # Subsonic Flow Equation
                                                                        html.Div([
                                                                            dmc.Text("Subsonic Flow:", fw=600, size="sm", mb="xs"),
                                                                            html.Div(
                                                                                className="equation-box",
                                                                                children=[static_equations['subsonic_flow']]
                                                                            )
                                                                        ]),
                                                                        
                                                                        # Critical Pressure Ratio
                                                                        html.Div([
                                                                            dmc.Text("Critical Pressure Ratio:", fw=600, size="sm", mb="xs"),
                                                                            html.Div(
                                                                                className="equation-box",
                                                                                children=[static_equations['critical_pressure']]
                                                                            )
                                                                        ]),
                                                                        
                                                                        # Simplified Form Section
                                                                        html.Div([
                                                                            dmc.Text("Simplified Forms:", fw=600, size="sm", mb="xs"),
                                                                            dmc.Paper(
                                                                                p="sm",
                                                                                className="results-info-card",
                                                                                children=[
                                                                                    dmc.Stack(
                                                                                        gap="lg",
                                                                                        children=[
                                                                                            html.Div([
                                                                                                dmc.Text("For Sonic Flow:", size="sm", fw=500, mb="sm"),
                                                                                                static_equations['sonic_simplified'],
                                                                                                html.Div([
                                                                                                    "where ",
                                                                                                    static_equations['sonic_factor'],
                                                                                                    " is the sonic flow factor"
                                                                                                ], style={"textAlign": "center", "marginTop": "0.5rem"})
                                                                                            ]),
                                                                                            dmc.Divider(my="xs"),
                                                                                            html.Div([
                                                                                                dmc.Text("For Subsonic Flow:", size="sm", fw=500, mb="sm"),
                                                                                                static_equations['subsonic_simplified']
                                                                                            ])
                                                                                        ]
                                                                                    )
                                                                                ]
                                                                            )
                                                                        ]),
                                                                        
                                                                        # Flow Conditions
                                                                        html.Div([
                                                                            dmc.Text("Flow Conditions:", fw=600, size="sm", mb="xs"),
                                                                            dmc.Paper(
                                                                                p="sm",
                                                                                className="results-info-card",
                                                                                children=[
                                                                                    dmc.Stack(
                                                                                        gap="md",
                                                                                        children=[
                                                                                            html.Div([
                                                                                                html.Strong("Sonic (Choked) Flow occurs when:", style={"display": "block", "marginBottom": "0.5rem", "color": "var(--primary-color)"}),
                                                                                                static_equations['flow_condition_sonic']
                                                                                            ]),
                                                                                            dmc.Divider(my="xs"),
                                                                                            html.Div([
                                                                                                html.Strong("Subsonic Flow occurs when:", style={"display": "block", "marginBottom": "0.5rem", "color": "var(--primary-color)"}),
                                                                                                static_equations['flow_condition_subsonic']
                                                                                            ])
                                                                                        ]
                                                                                    )
                                                                                ]
                                                                            )
                                                                        ]),
                                                                        
                                                                        # Variables Legend
                                                                        dmc.Paper(
                                                                            p="sm",
                                                                            className="results-info-card",
                                                                            children=[
                                                                                dmc.Text("Where:", fw=600, size="sm", mb="xs"),
                                                                                dmc.SimpleGrid(
                                                                                    cols=2,
                                                                                    spacing="sm",
                                                                                    children=[
                                                                                        html.Div([
                                                                                            html.P(variable_definitions['mdot'], className="variable-item"),
                                                                                            html.P(variable_definitions['cd'], className="variable-item"),
                                                                                            html.P(variable_definitions['area'], className="variable-item"),
                                                                                            html.P(variable_definitions['p1'], className="variable-item"),
                                                                                            html.P(variable_definitions['p2'], className="variable-item"),
                                                                                        ]),
                                                                                        html.Div([
                                                                                            html.P(variable_definitions['gamma'], className="variable-item"),
                                                                                            html.P(variable_definitions['mw'], className="variable-item"),
                                                                                            html.P(variable_definitions['z'], className="variable-item"),
                                                                                            html.P(variable_definitions['r'], className="variable-item"),
                                                                                            html.P(variable_definitions['t1'], className="variable-item"),
                                                                                        ])
                                                                                    ]
                                                                                )
                                                                            ]
                                                                        )
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                
                                                # Common Gas Properties Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Common Gas Properties", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Table(
                                                                    striped=True,
                                                                    highlightOnHover=True,
                                                                    className="tiering-table",
                                                                    children=[
                                                                        html.Thead([
                                                                            html.Tr([
                                                                                html.Th("Gas"),
                                                                                html.Th("γ (k)"),
                                                                                html.Th("R (J/kg·K)"),
                                                                                html.Th("MW (g/mol)"),
                                                                                html.Th("Critical Pressure Ratio")
                                                                            ])
                                                                        ]),
                                                                        html.Tbody([
                                                                            html.Tr([
                                                                                html.Td("Natural Gas"),
                                                                                html.Td("1.32"),
                                                                                html.Td("518.3"),
                                                                                html.Td("16.04"),
                                                                                html.Td("0.546")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Air"),
                                                                                html.Td("1.40"),
                                                                                html.Td("287"),
                                                                                html.Td("28.96"),
                                                                                html.Td("0.528")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Nitrogen"),
                                                                                html.Td("1.40"),
                                                                                html.Td("296.8"),
                                                                                html.Td("28.01"),
                                                                                html.Td("0.528")
                                                                            ])
                                                                        ])
                                                                    ]
                                                                ),
                                                                dmc.Text("* Critical pressure ratio determines if flow is sonic or subsonic", size="xs", c="dimmed", mt="xs")
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                
                                                # Equipment Failure Hole Sizes Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Equipment Failure Hole Sizes", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Table(
                                                                    striped=True,
                                                                    highlightOnHover=True,
                                                                    className="equipment-table",
                                                                    children=[
                                                                        html.Thead([
                                                                            html.Tr([
                                                                                html.Th("Equipment Type"),
                                                                                html.Th("Failure"),
                                                                                html.Th("Hole Size")
                                                                            ])
                                                                        ]),
                                                                        html.Tbody([
                                                                            # Flanges header
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Flanges"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.1)"})
                                                                            ]),
                                                                            # CAF
                                                                            html.Tr([
                                                                                html.Td("CAF", rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Severe"),
                                                                                html.Td("1 mm × distance between 2 flange bolts")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Small release"),
                                                                                html.Td("2.5 mm²")
                                                                            ]),
                                                                            # SWJ
                                                                            html.Tr([
                                                                                html.Td("SWJ", rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Severe"),
                                                                                html.Td("0.05 mm × distance between 2 flange bolts")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Small release"),
                                                                                html.Td("0.25 mm²")
                                                                            ]),
                                                                            # RTJ
                                                                            html.Tr([
                                                                                html.Td("RTJ", rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Severe"),
                                                                                html.Td("0.05 mm × distance between 2 flange bolts")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Small release"),
                                                                                html.Td("0.1 mm²")
                                                                            ]),
                                                                            # Valves header
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Valves"), colSpan=3, style={"background": "rgba(212, 175, 55, 0.1)"})
                                                                            ]),
                                                                            # < 150 mm
                                                                            html.Tr([
                                                                                html.Td("< 150 mm", rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Severe"),
                                                                                html.Td("2.5 mm²")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Small release"),
                                                                                html.Td("0.25 mm²")
                                                                            ]),
                                                                            # > 150 mm
                                                                            html.Tr([
                                                                                html.Td("> 150 mm"),
                                                                                html.Td("All releases"),
                                                                                html.Td("0.25 mm²")
                                                                            ]),
                                                                            # Divider row
                                                                            html.Tr([
                                                                                html.Td(
                                                                                    "",
                                                                                    colSpan=3,
                                                                                    style={
                                                                                        "padding": "0",
                                                                                        "height": "2px",
                                                                                        "background": "var(--border-color)",
                                                                                        "border": "none"
                                                                                    }
                                                                                )
                                                                            ]),
                                                                            # Centrifugal compressor header
                                                                            html.Tr([
                                                                                html.Td([
                                                                                    html.Strong("Centrifugal compressor"),
                                                                                    html.Br(),
                                                                                    html.Small("Note: assumed to be a 150-mm shaft. For different sizes, pro-rate the hole size by the square of the shaft diameter", style={"font-style": "italic"})
                                                                                ], rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Purged labyrinth seal"),
                                                                                html.Td("250 mm²")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Floating ring seal"),
                                                                                html.Td("50 mm²")
                                                                            ]),
                                                                            # Reciprocating compressors
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Reciprocating compressors")),
                                                                                html.Td(""),
                                                                                html.Td("2.5 mm²")
                                                                            ]),
                                                                            # Small bore connections
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Small bore connections"), rowSpan=2, style={"vertical-align": "middle"}),
                                                                                html.Td("Failures < full bore"),
                                                                                html.Td("0.25 mm²")
                                                                            ]),
                                                                            html.Tr([
                                                                                html.Td("Full bore"),
                                                                                html.Td("Tubing diameter")
                                                                            ]),
                                                                            # Drains and sample points
                                                                            html.Tr([
                                                                                html.Td(html.Strong("Drains and sample points")),
                                                                                html.Td("All"),
                                                                                html.Td("Diameter of the connection")
                                                                            ])
                                                                        ])
                                                                    ]
                                                                ),
                                                                # Table caption
                                                                html.Div(
                                                                    html.Em(
                                                                        "Cox, A. W., Ang, M. L., & Lees, F. P. (1990). Standard Hole Sizes. In Classification of Hazardous Locations (pp. 132–134). Institution of Chemical Engineers."
                                                                    ),
                                                                    style={
                                                                        "font-size": "0.85rem",
                                                                        "color": "var(--text-secondary)",
                                                                        "text-align": "left",
                                                                        "margin-top": "0.5rem",
                                                                        "padding": "0 0.5rem"
                                                                    }
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                
                                                # Important Links Section
                                                dmc.Stack(
                                                    gap="md",
                                                    children=[
                                                        dmc.Title("Important Links", order=4, className="section-title"),
                                                        dmc.Paper(
                                                            p="md",
                                                            className="input-card",
                                                            children=[
                                                                dmc.Stack(
                                                                    gap="sm",
                                                                    children=[
                                                                        dmc.Group(
                                                                            gap="xs",
                                                                            children=[
                                                                                DashIconify(icon="tabler:external-link", width=16, color="#d4af37"),
                                                                                dmc.Anchor(
                                                                                    "Enbridge PSE Guidelines",
                                                                                    href="#",
                                                                                    className="info-link"
                                                                                )
                                                                            ]
                                                                        ),
                                                                        dmc.Group(
                                                                            gap="xs",
                                                                            children=[
                                                                                DashIconify(icon="tabler:external-link", width=16, color="#d4af37"),
                                                                                dmc.Anchor(
                                                                                    "EnCompass Document Repository",
                                                                                    href="#",
                                                                                    className="info-link"
                                                                                )
                                                                            ]
                                                                        ),
                                                                        dmc.Group(
                                                                            gap="xs",
                                                                            children=[
                                                                                DashIconify(icon="tabler:external-link", width=16, color="#d4af37"),
                                                                                dmc.Anchor(
                                                                                    "Gas Loss Database",
                                                                                    href="#",
                                                                                    className="info-link"
                                                                                )
                                                                            ]
                                                                        ),
                                                                        dmc.Group(
                                                                            gap="xs",
                                                                            children=[
                                                                                DashIconify(icon="tabler:mail", width=16, color="#d4af37"),
                                                                                dmc.Anchor(
                                                                                    "Contact GTM Measurement Engineering",
                                                                                    href="#",
                                                                                    className="info-link"
                                                                                )
                                                                            ]
                                                                        )
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# Calculate flow rate callback
@app.callback(
    [Output('results', 'children'),
     Output('status-badge', 'children'),
     Output('status-badge', 'color')],
    [Input('calc-btn', 'n_clicks')],
    [State('gas-dropdown', 'value'),
     State('release-type-dropdown', 'value'),
     State('site-dropdown', 'value'),
     State('p0', 'value'), State('p0-unit', 'value'),
     State('p2', 'value'), State('p2-unit', 'value'),
     State('t0', 'value'), State('t0-unit', 'value'),
     State('area', 'value'), State('area-unit', 'value'),
     State('duration', 'value'), State('duration-unit', 'value'),
     State('cd-dropdown', 'value')]
)
def update_results(n_clicks, gas, release_type, site, p0, p0_unit, p2, p2_unit, t0, t0_unit, 
                   area, area_unit, duration, duration_unit, cd):
    if not n_clicks:
        return (
            dmc.Center(
                dmc.Stack(
                    [
                        DashIconify(icon="tabler:calculator", width=64, color="#6c757d"),
                        dmc.Text("Enter parameters and click Calculate", size="sm", c="dimmed")
                    ],
                    align="center",
                    gap="md"
                ),
                className="results-placeholder"
            ),
            "Ready",
            "gray"
        )
    
    try:
        # Convert inputs
        p0 = float(p0)
        p2 = float(p2)
        t0 = float(t0)
        area = float(area)
        duration = float(duration)
        cd = float(cd)
        
        # Convert to SI units
        P0 = (p0 * pressure_units[p0_unit]) + ATM_PRESSURE
        P2 = (p2 * pressure_units[p2_unit]) + ATM_PRESSURE
        T0 = temperature_units[t0_unit](t0)
        A = area * area_units[area_unit]
        duration_seconds = duration * time_units[duration_unit]
        
        # Get gas properties
        props = gas_data[gas]
        
        # Calculate mass flow rate
        mdot_kgs = mass_flow_rate(cd, A, P0, P2, T0, props['gamma'], props['R'])
        
        # Convert to different units
        flow_rate_kgs, _ = convert_output_units(mdot_kgs, gas, 'kg/s')
        flow_rate_lbs, _ = convert_output_units(mdot_kgs, gas, 'lb/s')
        flow_rate_mscf, _ = convert_output_units(mdot_kgs, gas, 'MSCF/hr')
        flow_rate_stm3, _ = convert_output_units(mdot_kgs, gas, 'st m³/hr')
        
        # Calculate totals
        total_release_kg = flow_rate_kgs * duration_seconds
        total_release_lb = flow_rate_lbs * duration_seconds
        total_release_mscf = flow_rate_mscf * duration_seconds / 3600
        total_release_stm3 = flow_rate_stm3 * duration_seconds / 3600
        
        # Check flow condition
        critical_pressure_ratio = (2 / (props['gamma'] + 1)) ** (props['gamma'] / (props['gamma'] - 1))
        flow_status = "SONIC (CHOKED)" if P2 / P0 <= critical_pressure_ratio else "SUBSONIC"
        
        # Calculate Release Tier
        release_tier = "N/A"
        tier_color = "gray"
        if site == "GTM US":
            if release_type == "Indoor":
                if duration_seconds > 3600:
                    if flow_rate_mscf >= 2.47:
                        release_tier = "Tier 1"
                        tier_color = "red"
                    elif flow_rate_mscf >= 1.41:
                        release_tier = "Tier 2"
                        tier_color = "grape"
                    else:
                        release_tier = "Tier 3"
                        tier_color = "green"
                else:
                    if total_release_mscf >= 2.47:
                        release_tier = "Tier 1"
                        tier_color = "red"
                    elif total_release_mscf >= 1.41:
                        release_tier = "Tier 2"
                        tier_color = "grape"
                    else:
                        release_tier = "Tier 3"
                        tier_color = "green"
            else:  # Outdoor
                if total_release_mscf >= 3000:
                    release_tier = "Tier 1"
                    tier_color = "red"
                elif total_release_mscf >= 300:
                    release_tier = "Tier 2"
                    tier_color = "grape"
                else:
                    release_tier = "Tier 3"
                    tier_color = "green"
        
        # Create results display
        results = dmc.Stack([
            # Status badges
            dmc.Group(
                justify="center",
                mb="md",
                children=[
                    dmc.Badge(flow_status, size="lg", variant="filled", 
                             className=f"status-badge-{'red' if 'SONIC' in flow_status else 'blue'}"),
                    dmc.Badge(release_tier, size="lg", variant="filled", 
                             className=f"tier-badge-{tier_color}") if release_tier != "N/A" else None
                ]
            ),
            
            # Flow rates
            dmc.Paper(
                p="sm",
                className="results-info-card",
                children=[
                    dmc.Text("Flow Rates", size="sm", fw=600, c="yellow", mb="xs"),
                    dmc.SimpleGrid(
                        cols=2,
                        spacing="sm",
                        children=[
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{flow_rate_kgs:.3f}", size="xl", fw=700),
                                dmc.Text("kg/s", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{flow_rate_lbs:.3f}", size="xl", fw=700),
                                dmc.Text("lb/s", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{flow_rate_mscf:.3f}", size="xl", fw=700),
                                dmc.Text("MSCF/hr", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{flow_rate_stm3:.3f}", size="xl", fw=700),
                                dmc.Text("st m³/hr", size="xs", c="dimmed")
                            ])
                        ]
                    )
                ]
            ),
            
            # Total release
            dmc.Paper(
                p="sm",
                className="results-info-card",
                children=[
                    dmc.Text("Total Release", size="sm", fw=600, c="yellow", mb="xs"),
                    dmc.SimpleGrid(
                        cols=2,
                        spacing="sm",
                        children=[
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{total_release_kg:.3f}", size="xl", fw=700),
                                dmc.Text("kg", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{total_release_lb:.3f}", size="xl", fw=700),
                                dmc.Text("lb", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{total_release_mscf:.3f}", size="xl", fw=700),
                                dmc.Text("MSCF", size="xs", c="dimmed")
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(f"{total_release_stm3:.3f}", size="xl", fw=700),
                                dmc.Text("st m³", size="xs", c="dimmed")
                            ])
                        ]
                    )
                ]
            ),
            
            # Save button
            dmc.Button(
                'Save Calculation',
                id='save-calc-btn',
                fullWidth=True,
                variant="light",
                leftSection=DashIconify(icon="tabler:device-floppy", width=16)
            )
        ])
        
        return results, "Calculated", "green"
        
    except Exception as e:
        return (
            dmc.Alert(
                f"Error: {str(e)}",
                title="Calculation Error",
                color="red",
                icon=DashIconify(icon="tabler:alert-circle", width=24)
            ),
            "Error",
            "red"
        )

# Reverse calculation callback
@app.callback(
    [Output('area', 'value'),
     Output('diameter', 'value', allow_duplicate=True)],
    [Input('reverse-calc-btn', 'n_clicks')],
    [State('target-tier-dropdown', 'value'),
     State('gas-dropdown', 'value'),
     State('release-type-dropdown', 'value'),
     State('site-dropdown', 'value'),
     State('p0', 'value'), State('p0-unit', 'value'),
     State('p2', 'value'), State('p2-unit', 'value'),
     State('t0', 'value'), State('t0-unit', 'value'),
     State('area-unit', 'value'),
     State('diameter-unit', 'value'),
     State('duration', 'value'), State('duration-unit', 'value'),
     State('cd-dropdown', 'value')],
    prevent_initial_call=True
)
def calculate_reverse_area(n_clicks, target_tier, gas, release_type, site, p0, p0_unit, p2, p2_unit, 
                          t0, t0_unit, area_unit, diameter_unit, duration, duration_unit, cd):
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    try:
        # Convert inputs
        p0 = float(p0)
        p2 = float(p2)
        t0 = float(t0)
        duration = float(duration)
        cd = float(cd)
        
        # Convert to SI units
        P0 = (p0 * pressure_units[p0_unit]) + ATM_PRESSURE
        P2 = (p2 * pressure_units[p2_unit]) + ATM_PRESSURE
        T0 = temperature_units[t0_unit](t0)
        duration_seconds = duration * time_units[duration_unit]
        
        # Get gas properties
        props = gas_data[gas]
        
        # Calculate required area
        required_area_m2, error = calculate_required_area(
            target_tier, release_type, site, duration_seconds, cd, 
            P0, P2, T0, props['gamma'], props['R'], gas
        )
        
        if error:
            return dash.no_update, dash.no_update
        
        # Convert area to selected units
        area_conversion = {
            'mm²': 1e6,
            'cm²': 1e4,
            'in²': 1550.0031,
            'm²': 1,
        }
        
        required_area_display = required_area_m2 * area_conversion[area_unit]
        
        # Calculate diameter from area
        # First convert area to mm²
        if area_unit == 'cm²':
            area_mm2 = required_area_display * 100
        elif area_unit == 'in²':
            area_mm2 = required_area_display * 645.16
        elif area_unit == 'm²':
            area_mm2 = required_area_display * 1e6
        else:  # mm²
            area_mm2 = required_area_display
            
        # Calculate diameter in mm
        diameter_mm = 2 * np.sqrt(area_mm2 / np.pi)
        
        # Convert to selected diameter unit
        if diameter_unit == 'inch':
            diameter_display = diameter_mm / 25.4
        else:
            diameter_display = diameter_mm
        
        return round(required_area_display, 4), round(diameter_display, 4)
        
    except:
        return dash.no_update, dash.no_update

# Save calculation callback
@app.callback(
    [Output('calculations-store', 'data'),
     Output('notifications', 'children')],
    [Input('save-calc-btn', 'n_clicks')],
    [State('calculations-store', 'data'),
     State('user-name', 'value'),
     State('calculation-title', 'value'),
     State('gas-dropdown', 'value'),
     State('release-type-dropdown', 'value'),
     State('site-dropdown', 'value'),
     State('p0', 'value'), State('p0-unit', 'value'),
     State('p2', 'value'), State('p2-unit', 'value'),
     State('t0', 'value'), State('t0-unit', 'value'),
     State('area', 'value'), State('area-unit', 'value'),
     State('duration', 'value'), State('duration-unit', 'value'),
     State('cd-dropdown', 'value')]
)
def save_calculation(n_clicks, stored_data, user_name, calc_title, gas, release_type, site,
                    p0, p0_unit, p2, p2_unit, t0, t0_unit, area, area_unit, 
                    duration, duration_unit, cd):
    if not n_clicks:
        return stored_data, ""
    
    if not user_name or not calc_title:
        return stored_data, dmc.Notification(
            title="Error",
            message="Please enter both Name and Calculation Title",
            color="red",
            action="show",
            autoClose=3000,
            icon=DashIconify(icon="tabler:x", width=20)
        )
    
    # Create new calculation record
    new_calc = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_name': user_name,
        'calculation_title': calc_title,
        'gas': gas,
        'release_type': release_type,
        'site': site,
        'p0': p0, 'p0_unit': p0_unit,
        'p2': p2, 'p2_unit': p2_unit,
        't0': t0, 't0_unit': t0_unit,
        'area': area, 'area_unit': area_unit,
        'duration': duration, 'duration_unit': duration_unit,
        'cd': cd
    }
    
    # Add to stored data
    updated_data = stored_data + [new_calc]
    
    # Save to file
    if save_calculations_to_file(updated_data):
        notification = dmc.Notification(
            title="Success",
            message="Calculation saved successfully!",
            color="green",
            action="show",
            autoClose=3000,
            icon=DashIconify(icon="tabler:check", width=20)
        )
    else:
        notification = dmc.Notification(
            title="Warning",
            message="Calculation saved to session but file save failed",
            color="orange",
            action="show",
            autoClose=4000,
            icon=DashIconify(icon="tabler:alert-triangle", width=20)
        )
    
    return updated_data, notification

# Display calculations table callback
@app.callback(
    [Output('calculations-table', 'children'),
     Output('calc-count-badge', 'children')],
    [Input('calculations-store', 'data')]
)
def display_calculations_table(data):
    if not data:
        return (
            dmc.Center(
                dmc.Stack([
                    DashIconify(icon="tabler:database-off", width=64, color="#6c757d"),
                    dmc.Text("No saved calculations yet", size="sm", c="dimmed")
                ], align="center", gap="md"),
                className="saved-calculations-placeholder"
            ),
            "0 calculations"
        )
    
    # Prepare data for AG Grid
    df = pd.DataFrame(data)
    
    # Define column definitions with advanced features
    column_defs = [
        {
            "headerName": "Date",
            "field": "timestamp",
            "filter": "agDateColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "width": 180,
            "cellClassName": "ag-cell-small"
        },
        {
            "headerName": "User",
            "field": "user_name",
            "filter": "agSetColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "width": 150,
            "cellClassName": "ag-cell-small"
        },
        {
            "headerName": "Title",
            "field": "calculation_title",
            "filter": "agTextColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "flex": 1,
            "cellClassName": "ag-cell-value"
        },
        {
            "headerName": "Gas",
            "field": "gas",
            "filter": "agSetColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "width": 120,
            "cellClassName": "ag-cell-small"
        },
        {
            "headerName": "Release Type",
            "field": "release_type",
            "filter": "agSetColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "width": 130,
            "cellClassName": "ag-cell-small"
        },
        {
            "headerName": "Site",
            "field": "site",
            "filter": "agSetColumnFilter",
            "floatingFilter": True,
            "sortable": True,
            "resizable": True,
            "width": 100,
            "cellClassName": "ag-cell-small"
        }
    ]
    
    # Create the AG Grid component
    grid = dag.AgGrid(
        id='calc-table',
        rowData=df.to_dict('records'),
        columnDefs=column_defs,
        defaultColDef={
            "sortable": True,
            "resizable": True,
            "menuTabs": ["generalMenuTab", "filterMenuTab", "columnsMenuTab"],
            "cellClassName": "ag-cell-white"
        },
        className="ag-theme-alpine-dark ag-grid-full",
        enableEnterpriseModules=True,
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 10,
            "domLayout": "autoHeight",
            "rowSelection": "single",
            "animateRows": True,
            "rowHeight": 42,
            "headerHeight": 48,
            "suppressRowClickSelection": False,
            "enableCellTextSelection": True
        }
    )
    
    # Action buttons
    action_buttons = dmc.Group(
        mt="md",
        children=[
            dmc.Button(
                "View",
                id="view-calc-btn",
                variant="light",
                size="sm",
                leftSection=DashIconify(icon="tabler:eye", width=16)
            ),
            dmc.Button(
                "Delete",
                id="delete-calc-btn",
                variant="subtle",
                color="red",
                size="sm",
                leftSection=DashIconify(icon="tabler:trash", width=16)
            )
        ]
    )
    
    return (
        dmc.Stack([grid, action_buttons]),
        f"{len(data)} calculations"
    )

# View calculation callback
@app.callback(
    [Output('user-name', 'value', allow_duplicate=True),
     Output('calculation-title', 'value', allow_duplicate=True),
     Output('gas-dropdown', 'value', allow_duplicate=True),
     Output('release-type-dropdown', 'value', allow_duplicate=True),
     Output('site-dropdown', 'value', allow_duplicate=True),
     Output('p0', 'value', allow_duplicate=True), Output('p0-unit', 'value', allow_duplicate=True),
     Output('p2', 'value', allow_duplicate=True), Output('p2-unit', 'value', allow_duplicate=True),
     Output('t0', 'value', allow_duplicate=True), Output('t0-unit', 'value', allow_duplicate=True),
     Output('area', 'value', allow_duplicate=True), Output('area-unit', 'value', allow_duplicate=True),
     Output('duration', 'value', allow_duplicate=True), Output('duration-unit', 'value', allow_duplicate=True),
     Output('cd-dropdown', 'value', allow_duplicate=True),
     Output('main-tabs', 'value', allow_duplicate=True)],
    [Input('view-calc-btn', 'n_clicks')],
    [State('calc-table', 'selectedRows'),
     State('calculations-store', 'data')],
    prevent_initial_call=True
)
def view_calculation(n_clicks, selected_rows, data):
    if not n_clicks or not selected_rows or not data:
        return [dash.no_update] * 17
    
    # Get selected calculation
    selected_calc = selected_rows[0]
    
    # Switch to calculator tab and populate fields
    return (
        selected_calc.get('user_name', ''),
        selected_calc.get('calculation_title', ''),
        selected_calc.get('gas', 'Natural Gas'),
        selected_calc.get('release_type', 'Outdoor'),
        selected_calc.get('site', 'GTM US'),
        float(selected_calc.get('p0', 100)),
        selected_calc.get('p0_unit', 'psi(g)'),
        float(selected_calc.get('p2', 0)),
        selected_calc.get('p2_unit', 'psi(g)'),
        float(selected_calc.get('t0', 20)),
        selected_calc.get('t0_unit', '°C'),
        float(selected_calc.get('area', 10)),
        selected_calc.get('area_unit', 'mm²'),
        float(selected_calc.get('duration', 10)),
        selected_calc.get('duration_unit', 'minutes'),
        selected_calc.get('cd', '0.61'),
        'calculator'  # Switch to calculator tab
    )

# Delete calculation callback
@app.callback(
    [Output('calculations-store', 'data', allow_duplicate=True),
     Output('notifications', 'children', allow_duplicate=True)],
    [Input('delete-calc-btn', 'n_clicks')],
    [State('calc-table', 'selectedRows'),
     State('calculations-store', 'data')],
    prevent_initial_call=True
)
def delete_calculation(n_clicks, selected_rows, data):
    if not n_clicks or not selected_rows or not data:
        return data, ""
    
    # Get selected calculation ID
    selected_id = selected_rows[0]['id']
    
    # Remove calculation
    updated_data = [calc for calc in data if calc['id'] != selected_id]
    
    # Save to file
    if save_calculations_to_file(updated_data):
        notification = dmc.Notification(
            title="Deleted",
            message="Calculation deleted successfully!",
            color="red",
            action="show",
            autoClose=3000,
            icon=DashIconify(icon="tabler:trash", width=20)
        )
    else:
        notification = dmc.Notification(
            title="Warning",
            message="Calculation deleted from session but file save failed",
            color="orange",
            action="show",
            autoClose=4000,
            icon=DashIconify(icon="tabler:alert-triangle", width=20)
        )
    
    return updated_data, notification

# Combined callback for orifice input handling
@app.callback(
    [Output('area', 'disabled'),
     Output('area-unit', 'disabled'),
     Output('diameter', 'disabled'),
     Output('diameter-unit', 'disabled'),
     Output('area', 'value', allow_duplicate=True),
     Output('diameter', 'value')],
    [Input('orifice-input-type', 'value'),
     Input('diameter', 'value'),
     Input('diameter-unit', 'value'),
     Input('area', 'value'),
     Input('area-unit', 'value')],
    [State('area', 'value'),
     State('diameter', 'value')],
    prevent_initial_call=True
)
def handle_orifice_inputs(input_type, diameter, diameter_unit, area, area_unit, 
                         current_area, current_diameter):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Initialize return values
    area_disabled = False
    area_unit_disabled = False
    diameter_disabled = True
    diameter_unit_disabled = True
    new_area = current_area
    new_diameter = current_diameter
    
    # Handle input type toggle
    if trigger_id == 'orifice-input-type':
        if input_type == 'area':
            # Enable area, disable diameter
            area_disabled = False
            area_unit_disabled = False
            diameter_disabled = True
            diameter_unit_disabled = True
        else:
            # Enable diameter, disable area
            area_disabled = True
            area_unit_disabled = True
            diameter_disabled = False
            diameter_unit_disabled = False
    else:
        # Maintain current disabled states based on input_type
        if input_type == 'area':
            area_disabled = False
            area_unit_disabled = False
            diameter_disabled = True
            diameter_unit_disabled = True
        else:
            area_disabled = True
            area_unit_disabled = True
            diameter_disabled = False
            diameter_unit_disabled = False
    
    # Handle diameter to area conversion
    if trigger_id in ['diameter', 'diameter-unit'] and input_type == 'diameter':
        if diameter is not None and diameter > 0:
            # Convert diameter to mm
            if diameter_unit == 'inch':
                diameter_mm = diameter * 25.4
            else:
                diameter_mm = diameter
            
            # Calculate area in mm²
            area_mm2 = np.pi * (diameter_mm / 2) ** 2
            
            # Convert to selected area unit
            if area_unit == 'cm²':
                new_area = round(area_mm2 / 100, 4)
            elif area_unit == 'in²':
                new_area = round(area_mm2 / 645.16, 4)
            elif area_unit == 'm²':
                new_area = round(area_mm2 / 1e6, 4)
            else:  # mm²
                new_area = round(area_mm2, 4)
    
    # Handle area to diameter conversion
    elif trigger_id in ['area', 'area-unit'] and input_type == 'area':
        if area is not None and area > 0:
            # Convert area to mm²
            if area_unit == 'cm²':
                area_mm2 = area * 100
            elif area_unit == 'in²':
                area_mm2 = area * 645.16
            elif area_unit == 'm²':
                area_mm2 = area * 1e6
            else:  # mm²
                area_mm2 = area
            
            # Calculate diameter in mm
            diameter_mm = 2 * np.sqrt(area_mm2 / np.pi)
            
            # Convert to selected diameter unit
            if diameter_unit == 'inch':
                new_diameter = round(diameter_mm / 25.4, 4)
            else:
                new_diameter = round(diameter_mm, 4)
    
    return area_disabled, area_unit_disabled, diameter_disabled, diameter_unit_disabled, new_area, new_diameter

# For deployment
server = app.server

if __name__ == '__main__':
    app.run(debug=True, port=8052)