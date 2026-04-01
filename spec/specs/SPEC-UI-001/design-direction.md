# Design Direction: Data Analysis Platform for Business Analysts

**Project:** Full-Stack Data Analysis Platform
**Date:** 2026-03-28
**Version:** 1.0

---

## Intent Statement

### Who is this human?

Business analysts and non-technical users who need to perform data analysis without writing SQL or Python code. They understand their business logic and data requirements but lack technical implementation skills. They value efficiency, clarity, and control over their data workflows.

### What must they accomplish?

- Build and execute data analysis workflows through visual interfaces
- Query databases using intuitive drag-and-drop builders
- Transform raw data into actionable business insights
- Visualize results through charts, tables, and dashboards
- Export findings in multiple formats (CSV, Excel, PDF)
- Iterate quickly on analysis without waiting for technical teams

### What should this feel like?

Professional, empowering, intuitive, and efficient. The interface should convey confidence and competence while remaining approachable. Users should feel like data experts, not technical novices. The experience should be fluid and responsive, with immediate visual feedback that makes complex data analysis feel manageable and even enjoyable.

---

## Domain Concepts

### Core Vocabulary

1. **Data Pipeline** - The visual representation of data flow from source through transformation to output

2. **Query Builder** - Visual interface for constructing database queries without SQL knowledge

3. **Workflow Canvas** - Drag-and-drop workspace where users build and connect analysis steps

4. **Data Transformation** - Operations that clean, filter, aggregate, or reshape data

5. **Visualization Cards** - Modular components that display data as charts, tables, or metrics

6. **Execution Engine** - Background system that runs workflows and manages data processing

7. **Result Explorer** - Interface for examining, filtering, and exporting analysis results

### Concept Relationships

```
Workflow Canvas contains → Query Builder + Data Transformations + Visualization Cards
Query Builder feeds into → Data Pipeline
Data Pipeline outputs to → Result Explorer
Execution Engine powers → All workflow components
```

---

## Color World

### Primary Palette

**Professional Blue** - Trust, intelligence, data expertise
- Primary: `#0052CC` (Core brand color)
- Secondary: `#0065FF` (Interactive elements)
- Tertiary: `#2684FF` (Highlights and accents)

**Usage:** Primary buttons, active states, brand elements, data flow indicators

### Semantic Colors

**Success Green** - Confirmation, completed workflows, valid data
- Standard: `#36B37E`
- Dark: `#00875A`
**Usage:** Success toasts, completed pipeline nodes, valid data indicators

**Warning Amber** - Attention needed, data quality issues
- Standard: `#FFAB00`
- Dark: `#FF991F`
**Usage:** Warning toasts, data quality alerts, configuration issues

**Error Red** - Failed executions, validation errors
- Standard: `#DE350B`
- Dark: `#FF5630`
**Usage:** Error toasts, failed pipeline nodes, validation failures

### Neutral Palette

**Gray Scale** - Interface structure, secondary information
- Dark Gray: `#6B778C` (Secondary text)
- Light Gray: `#DFE1E6` (Borders, dividers)
- Background: `#FAFBFC` (Page background)
- Surface: `#FFFFFF` (Card backgrounds)

### Accent Colors

**Creative Purple** - Advanced features, optional power user modes
- Primary: `#6554C0`
- Secondary: `#8777D9`
**Usage:** Advanced mode toggles, SQL view reveal, expert settings

---

## Signature Element

### The Workflow Canvas

A sophisticated, infinite workspace where data analysis comes alive through intuitive drag-and-drop interactions.

#### Key Features

1. **Living Connections**
   - Animated data flow lines between components
   - Pulse animation when data is actively processing
   - Color-coded by data state (processing, complete, error)

2. **Smart Snapping**
   - Intelligent alignment suggestions as users drag components
   - Auto-connection of compatible components
   - Visual feedback indicating valid connection points

3. **Mini-Map Navigator**
   - Bird's-eye view of entire workflow
   - Click-to-navigate to different sections
   - Zoom indicator showing current viewport

4. **Contextual Inspectors**
   - Hover previews showing data shape at each step
   - Real-time statistics (row count, column types)
   - Sample data preview without leaving canvas

5. **Gesture-Based Interactions**
   - Pinch-to-zoom for overview or detail view
   - Pan across large workflows
   - Multi-select for batch operations

#### Differentiation

Unlike traditional form-based interfaces or rigid wizards, our canvas:
- **Supports non-linear thinking** - Build workflows in any order
- **Encourages exploration** - Try different approaches without commitment
- **Makes data visible** - See pipeline shape and data flow at every step
- **Feels tangible** - Manipulate analysis like physical objects

---

## Defaults to Avoid

### 1. SQL-First Interfaces ❌

**Avoid:** Leading with SQL editors, code snippets, or query text areas as primary interfaces.

**Instead:** Hide SQL completely behind visual abstractions. Only reveal as optional "Advanced View" for power users who explicitly request it.

**Rationale:** Business analysts think in business logic, not SQL syntax. Technical barriers create friction and reinforce feelings of inadequacy.

### 2. Technical Jargon ❌

**Avoid:** Database terminology like "INNER JOIN," "WHERE clause," "GROUP BY," "ETL pipeline," "schema," "index."

**Instead:** Use business language:
- "Combine datasets" not "JOIN tables"
- "Filter conditions" not "WHERE clause"
- "Group by category" not "GROUP BY"
- "Data workflow" not "ETL pipeline"

**Rationale:** Language shapes user perception. Business terminology reinforces user expertise and domain knowledge.

### 3. Monolithic Wizards ❌

**Avoid:** Linear, multi-step wizards that force sequential completion and prevent exploration.

**Instead:** Enable free-form workflow building with:
- Parallel paths and branches
- Save and continue at any point
- Iterate on any section independently
- Build bottom-up or top-down as preferred

**Rationale:** Analysis is inherently non-linear and iterative. rigid workflows don't match how users think.

### 4. Developer-Centric Dashboards ❌

**Avoid:** Technical metrics, execution logs, database schema visualizations as primary interfaces.

**Instead:** Focus on business outcomes:
- Revenue trends and growth metrics
- Customer segments and behavior insights
- Inventory levels and supply chain data
- Marketing campaign performance

**Rationale:** Users care about business insights, not technical implementation details.

### 5. Static Export Only ❌

**Avoid:** Treating exports as terminal, one-way operations.

**Instead:** Enable round-tripping workflows:
- Export to Excel with workflow metadata embedded
- Re-import Excel changes with preserved context
- Maintain link between exported file and live workflow

**Rationale:** Analysis doesn't end at export. Users iterate in tools they know best.

---

## Design Principles

### 1. Visibility Over Hidden Complexity

Make data flow visible at every step. Show what data looks like after each transformation. Never hide data behind "black box" operations.

### 2. Business Language First

All interface text, error messages, and help content should use business terminology. Technical terms appear only in optional advanced modes.

### 3. Progressive Disclosure

Start simple. Reveal complexity only when users request it or when context suggests they're ready. Default interfaces should feel spacious and uncluttered.

### 4. Immediate Feedback

Every user action should produce visual feedback within 100ms. Processing states should be animated and communicative. Errors should be specific and actionable.

### 5. Forgiving Exploration

Users should feel free to experiment without consequences. Enable undo/redo, non-destructive branching, and easy reversion to previous states.

---

## Integration with Design System

This design direction references and extends the project-level design system at `.moai/design/system.md`.

**Current Status:** The design system file is currently empty (template only).

**Next Steps:** After SPEC creation, these design decisions should be persisted to the project-level design system to establish consistent vocabulary and patterns across all future work.

---

## References and Inspiration

### Visual Language
- **Linear** - For smooth, professional interactions and gesture-based canvas
- **Figma** - For infinite canvas with smart snapping and contextual tools
- **Airtable** - For business-friendly data interfaces and visual builders

### Workflow Patterns
- **Node-RED** - For node-based workflow canvas (simplified for business users)
- **Zapier** - For trigger-action workflow simplification
- **Retool** - For internal tool UI patterns and component libraries

### Data Visualization
- **Tableau** - For drag-and-drop analytics without code
- **Metabase** - For visual query builder patterns
- **Microsoft Power BI** - For business-centric analytics UX

---

**End of Design Direction Document**
