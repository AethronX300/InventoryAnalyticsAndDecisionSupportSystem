# Meridian Inventory IQ - Graph Explanations

Here is a breakdown of how each graph on the dashboard works, what data it uses, and how it is computed:

## 1. Overview Page

### KPI Sparklines
- **Location:** The small charts inside the top KPI cards (Revenue, Units).
- **How it works:** They show the daily trend over the last 30 days. The data is pulled directly from the daily sales aggregation. The charts are minimal `go.Scatter` plots with `fill="tozeroy"` to create an area chart effect, completely hiding the axes for a clean look.

### Sales Trend vs Previous Period
- **Location:** The main line chart on the overview page.
- **How it works:** Displays daily revenue, units, or orders over a selected timeframe (e.g. 14, 30, 90 days). It uses a standard line chart (`go.Scatter` with `mode="lines"`). If you are looking at analytics, it often plots a dashed secondary line representing the *previous* equivalent period so you can compare current performance to the past.

### Revenue by Category (Donut)
- **Location:** The "Revenue by category" card on the Overview page.
- **How it works:** A `go.Pie` chart with a `hole` parameter (donut chart). It aggregates the last 30 days of revenue by product category, assigning a distinct color to each. Hovering over a slice displays the exact rupee amount and percentage.

## 2. Analytics Page

### Movers (Horizontal Bar charts)
- **Location:** The "Fast movers" and "Slow movers" columns.
- **How it works:** These are constructed using custom HTML/CSS (horizontal divs with inline widths) rather than Plotly, allowing for very dense, list-like layouts. The width of the bar corresponds to the velocity (units per day) relative to the highest velocity product. 

### Category Performance (Bar + Line)
- **Location:** "Category performance" chart.
- **How it works:** A dual-axis Plotly chart. It overlays a `go.Bar` chart representing total revenue per category, and a `go.Scatter` line chart representing the gross margin percentage. This lets you quickly see if your highest revenue categories are actually your most profitable ones.

### Velocity vs Margin (Scatter Plot)
- **Location:** "Velocity vs. margin" chart.
- **How it works:** A `go.Scatter` plot with `mode="markers"`.
  - **X-Axis:** Velocity (units sold per day).
  - **Y-Axis:** Gross Margin (percentage).
  - **Bubble Size:** Represents the total 30-day revenue for that product (using `marker=dict(size=...)`).
  - **Color:** Indicates the product category.
This chart helps identify your best products (top right: fast-selling, high-margin) and worst products (bottom left: slow-selling, low-margin).

## 3. Product Drawer / History

### Stock Step History
- **Location:** Inside the product details drawer when you click on a specific item.
- **How it works:** This is a step chart (`go.Scatter` with `line_shape="hv"` for horizontal-vertical steps). It traces every historical stock movement (sales, receipts, adjustments) chronologically to visualize exactly how your stock depleted over time. It also plots a dashed horizontal line indicating your "Reorder Point" so you can visually see when stock dipped below safe levels.
