# CSS Styling and Theming Instructions

## Overview
This project follows a strict separation of concerns between styling and functionality. All CSS styling must be maintained in a single external CSS file, with no inline styles in Python code.

## CSS File Structure

### Main CSS File
- **File**: `assets/main.css`
- **Purpose**: Contains all styling and theming for the entire application
- **Location**: Must be placed in the `assets` directory (Dash automatically serves files from this folder)

## Styling Guidelines

### 1. No Inline Styles
- **NEVER** use inline CSS in Python files
- **NEVER** hardcode style attributes directly in widget creation
- All styling must reference CSS classes defined in `main.css`

### 2. CSS Class Naming Convention
Use BEM (Block Element Modifier) methodology:
- Block: `calculator`
- Element: `calculator__button`
- Modifier: `calculator__button--primary`

### 3. Theme Variables
Define all colors, fonts, and spacing as CSS custom properties:
```css
:root {
  /* Colors */
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --background-color: #f8f9fa;
  --text-color: #212529;
  
  /* Fonts */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-base: 16px;
  
  /* Spacing */
  --spacing-unit: 8px;
  --spacing-small: calc(var(--spacing-unit) * 1);
  --spacing-medium: calc(var(--spacing-unit) * 2);
  --spacing-large: calc(var(--spacing-unit) * 3);
}
```

### 4. Component Styling
Each component should have its own CSS class:
```css
.component-name {
  /* Component styles */
}

.component-name__element {
  /* Element styles */
}
```

## Implementation in Python

### 1. Loading CSS
Always load the CSS file at application initialization:
```python
# At the beginning of your main application file
with open('styles/main.css', 'r') as css_file:
    css_content = css_file.read()
    # Apply CSS to your application framework
```

### 2. Applying Classes
Use only CSS class names when creating widgets:
```python
# Good - Using CSS classes
widget.setObjectName("calculator__button")
widget.setProperty("class", "calculator__button calculator__button--primary")

# Bad - Inline styles
widget.setStyleSheet("background-color: #007bff; color: white;")  # NEVER DO THIS
```

### 3. Dynamic Styling
For dynamic style changes, toggle CSS classes instead of modifying styles:
```python
# Good - Toggle classes
if condition:
    widget.setProperty("class", "button button--active")
else:
    widget.setProperty("class", "button button--inactive")

# Bad - Direct style manipulation
widget.setStyleSheet(f"background-color: {'red' if error else 'green'}")  # NEVER DO THIS
```

## File Organization

```
project-root/
├── assets/
│   └── main.css          # All CSS styles (Dash serves from assets/)
├── *.py                  # Python files with NO inline styles
└── STYLING_INSTRUCTIONS.md  # This file
```

## Enforcement Rules

1. **Code Review**: All code must be reviewed to ensure no inline styles
2. **CSS-Only Changes**: Style modifications require only CSS file updates
3. **Class References**: Python code may only reference CSS class names
4. **Single Source**: `main.css` is the single source of truth for all styling

## Hover Effects and Interactive Styles

### Select Dropdown Hover Effects
The CSS file includes comprehensive hover states for select dropdowns that may require multiple selectors for proper browser compatibility:

```css
/* Multiple selectors ensure hover works across Mantine versions */
.mantine-Select-dropdown [data-combobox-option]:hover,
.mantine-Select-dropdown [data-hovered="true"],
.mantine-Select-item:hover,
[data-hovered] {
    background-color: #cc6600 !important;
}
```

**Important**: Hover effects are applied automatically by CSS. No JavaScript or Python code is needed.

### Other Interactive Elements
- **Buttons**: Transform and shadow effects on hover
- **Tabs**: Color changes for non-active tabs on hover
- **Input fields**: Border color changes on focus
- **Table rows**: Background highlight on hover

## Responsive Design

### Mobile Layout Rules
1. **One input group per row**: Each input and its unit selector stay together
2. **Full-width grid columns**: All columns expand to 100% width on mobile
3. **Adjusted spacing**: Reduced padding and margins for mobile screens
4. **Unit selectors**: Fixed width (120px) while inputs take remaining space

### Special CSS Classes for Layout
- **`.input-flex`**: Makes inputs flexible width
- **`.input-width-small`**: Fixed width for unit selectors
- **`.grid-responsive`**: Responsive grid container
- **`.input-row`**: Keeps input+unit pairs together

### Unit Selector Text Positioning
Unit selectors (without icons) have special padding override:
```css
.input-width-small .mantine-Select-input {
    padding-left: var(--spacing-md) !important; /* Normal padding */
}
```

## Benefits

- **Maintainability**: All styles in one location
- **Consistency**: Unified theming across the application
- **Flexibility**: Easy to update styles without touching Python code
- **Performance**: CSS can be cached and optimized separately
- **Collaboration**: Designers can work on CSS without Python knowledge
- **Responsive**: Automatic mobile-friendly layouts

## Mathematical Equations (Static HTML Rendering)

### IMPORTANT: Performance-Optimized Equation Display

For optimal performance, mathematical equations are rendered as static HTML instead of using MathJax:

1. **DO NOT use MathJax or LaTeX** - This causes performance issues and slow rendering
2. **DO use static HTML with proper CSS classes**:
   ```python
   # Correct way - Import static equations
   from create_static_equations import equations as static_equations, variable_definitions
   
   # Use in layout
   html.Div(
       className="equation-box",
       children=[static_equations['sonic_flow']]  # Returns a Dash html.Div component
   )
   
   # For variable definitions
   html.P(variable_definitions['cd'], className="variable-item")  # Returns formatted HTML
   ```

3. **CSS Classes for Static Equations**:
   - `.static-equation` - Main equation displays
   - `.static-equation-small` - Smaller equations
   - `.frac` - Fractions with `.frac-num` and `.frac-den`
   - `.bracket-group` - Brackets for grouping with exponents
   - `.var-with-dot` - Variables with dot notation (ṁ)
   - `.paren-group` - Parentheses grouping
   - `.complex-exp` - Complex exponents

4. **Benefits of Static Equations**:
   - Instant rendering (no JavaScript processing)
   - Better performance, especially on mobile devices
   - No external library dependencies
   - Consistent appearance across all browsers
   - Reduced page load time

### Equation Styling in CSS

The main.css file includes comprehensive static equation styling:
- Custom fraction rendering with proper spacing
- Bracket notation with exponents for roots (e.g., [x]^1/2)
- Dot notation for derivatives
- Responsive equation containers

## Quick Reference for Claude Code

When working on this project:
1. **CHECK** `assets/main.css` before adding any styling
2. **ADD** new styles only to `main.css` in the assets folder
3. **USE** CSS class names in Python code (e.g., `className="section-title"`)
4. **NEVER** write inline styles or style attributes
5. **REFER** to this document for any styling decisions
6. **TEST** hover effects and responsive layouts in the browser
7. **USE** static HTML equations from `create_static_equations.py`, not MathJax

### Common CSS Classes to Use:
- `app-header` - Header section styling
- `section-title` - Section headings
- `input-card` - Form container cards
- `input-flex` - Flexible width inputs
- `input-width-small` - Fixed width unit selectors
- `button-calculate` - Calculate button styling
- `results-container` - Results section container
- `results-info-card` - Result display cards
- `ag-cell-small` - Small table cells
- `ag-cell-value` - Highlighted table values
- `static-equation` - Main equation displays
- `static-equation-small` - Smaller equation displays
- `equation-box` - Equation container boxes
- `variable-item` - Variable definitions
- `frac`, `frac-num`, `frac-den` - Fraction components
- `bracket-group`, `bracket` - Bracket notation for grouping
- `var-with-dot` - Variables with dot notation
- `paren-group`, `paren` - Parentheses components

Remember: If it's about appearance, it belongs in `main.css`, not in Python code.