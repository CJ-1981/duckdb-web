# Design System

This file is the persistent design memory for this project. It is maintained by MoAI agents
and accumulates design intent, domain vocabulary, and craft decisions across sessions.

See `.claude/skills/moai-design-craft/` for the protocol that governs this file.

---

## Design Intent

Build a professional data analysis platform that empowers business analysts to perform complex data analysis without writing SQL or Python code. The interface should convey confidence and competence while remaining approachable, making users feel like data experts rather than technical novices. The experience should be fluid, responsive, and intuitive, with immediate visual feedback that makes complex data analysis feel manageable and even enjoyable.

## Domain Vocabulary

| Term | Definition |
|------|-----------|
| Data Pipeline | The visual representation of data flow from source through transformation to output |
| Query Builder | Visual interface for constructing database queries without SQL knowledge |
| Workflow Canvas | Drag-and-drop workspace where users build and connect analysis steps |
| Data Transformation | Operations that clean, filter, aggregate, or reshape data |
| Visualization Cards | Modular components that display data as charts, tables, or metrics |
| Execution Engine | Background system that runs workflows and manages data processing |
| Result Explorer | Interface for examining, filtering, and exporting analysis results |

## Craft Principles

**Visibility Over Hidden Complexity**
Make data flow visible at every step. Show what data looks like after each transformation. Never hide data behind "black box" operations.

**Business Language First**
All interface text, error messages, and help content should use business terminology. Technical terms appear only in optional advanced modes.
- Use "Combine datasets" not "JOIN tables"
- Use "Filter conditions" not "WHERE clause"
- Use "Group by category" not "GROUP BY"

**Progressive Disclosure**
Start simple. Reveal complexity only when users request it or when context suggests they're ready. Default interfaces should feel spacious and uncluttered.

**Immediate Feedback**
Every user action should produce visual feedback within 100ms. Processing states should be animated and communicative. Errors should be specific and actionable.

**Forgiving Exploration**
Users should feel free to experiment without consequences. Enable undo/redo, non-destructive branching, and easy reversion to previous states.

## Per-Feature Direction

### Full-Stack Data Analysis Platform (SPEC-UI-001)

**Signature Element: The Workflow Canvas**
A sophisticated, infinite workspace where data analysis comes alive through intuitive drag-and-drop interactions. Features include:
- Living Connections with animated data flow lines between components
- Smart Snapping with intelligent alignment suggestions
- Mini-Map Navigator for bird's-eye view of entire workflow
- Contextual Inspectors with hover previews showing data shape at each step
- Gesture-Based Interactions with pinch-to-zoom and pan support

**Color Palette**
- Primary Blue (#0052CC) - Trust, intelligence, data expertise
- Success Green (#36B37E) - Confirmation, completed workflows
- Warning Amber (#FFAB00) - Attention needed, data quality issues
- Error Red (#DE350B) - Failed executions, validation errors
- Creative Purple (#6554C0) - Advanced features, optional power user modes

**Anti-Patterns to Avoid**
1. SQL-first interfaces - Hide SQL completely behind visual abstractions
2. Technical jargon - Use business language, not database terminology
3. Monolithic wizards - Enable free-form workflow building with parallel paths
4. Developer-centric dashboards - Focus on business outcomes, not technical metrics
5. Static export only - Enable round-tripping workflows with preserved context

## Anti-Patterns

[Patterns that were tried and failed — added during /moai review --critique.]
