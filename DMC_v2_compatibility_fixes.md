# Dash Mantine Components v2.0.0 Compatibility Fixes

## Summary of Changes Made to pse_calculator_enbridge.py

### 1. DashIconify Color Parameter
- Changed from `style={'color': '#6c757d'}` to `color="#6c757d"`
- Fixed in 2 locations:
  - Line 913: Calculator icon
  - Line 1246: Database-off icon

### 2. Stack Component Parameters
- Changed `spacing="md"` to `gap="md"`
- Fixed in 2 locations:
  - Line 917: Stack component in results display
  - Line 1248: Stack component in empty calculations display

### 3. GridCol Responsive Breakpoints
- Changed from separate `span` and `md` parameters to a single responsive `span` parameter
- Fixed in 2 locations:
  - Line 490-492: Changed `span=12, md=7` to `span={"base": 12, "md": 7}`
  - Line 813-815: Changed `span=12, md=5` to `span={"base": 12, "md": 5}`

### 4. LoadingOverlay Component Removal
- Removed LoadingOverlay component as it no longer accepts children in DMC v2.0.0
- LoadingOverlay is now meant to be used as a standalone overlay controlled by `visible` prop
- Replaced with simple html.Div for results display

### 5. Duplicate Callback Outputs
- Added `allow_duplicate=True` to all outputs in the view calculation callback
- Added `prevent_initial_call=True` to avoid initial execution
- This fixes the conflict with the reverse calculation callback that also outputs to area.value

### 6. SimpleGrid Component Parameters
- Changed `gap="sm"` to `spacing="sm"` for SimpleGrid components
- Fixed in 2 locations in the results display

### 7. Alert and Notification Components
- Changed `leftSection` to `icon` ONLY for Alert and Notification components
- Alert and Notification use `icon`, while Input and Button components still use `leftSection`
- Fixed in 5 locations:
  - 1 Alert component in error handling
  - 4 Notification components for save/delete operations
- Note: Input components (TextInput, NumberInput, Select) and Button components still use `leftSection` in DMC v2.0.0

## DMC v2.0.0 API Changes Reference

### Component Parameter Changes:
- `color` → `c` (for Text components)
- `weight` → `fw` (for Text components)
- `spacing` → `gap` (for Stack, Group components)
- `position` → `justify` (for Group components)
- `leftIcon` → `leftSection` (for Button, Input components)
- `align` → `align` (remains the same)

### Notes:
- The file already uses the correct v2.0.0 parameters for most components
- DashIconify now accepts color as a direct prop instead of within style object
- All other Mantine components in the file are using the correct v2.0.0 syntax

## Running the Application

To run the application, ensure you have the following dependencies installed:
```bash
pip install dash dash-mantine-components dash-ag-grid dash-iconify numpy pandas
```

Then run:
```bash
python pse_calculator_enbridge.py
```

The app will be available at http://localhost:8052