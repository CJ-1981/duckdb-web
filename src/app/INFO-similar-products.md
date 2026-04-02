# INFO on similar products

Listed directory duckdb-web
Searched web: "open source DuckDB visual workflow builder web UI sql node editor"

To find similar tools, it's helpful to categorize the features you've built: **visual node-based workflows**, **DuckDB as a core engine**, and **SQL-first data processing**.

While many enterprise tools (like Alteryx or Matillion) offer visual data pipelines, they are quite heavy and expensive. Here are the most relevant open-source and freeware alternatives that share dna with your "DuckDB-Web" tool:

### 1. Modern Data Pipeline Builders (Node-Based)
These are the closest matches to your workflow-style interface, allowing you to chain data transformations visually.

*   **[Mage.ai](https://www.mage.ai/) (Open Source)**
    *   **How it's similar**: It uses a block-based (notebook-meets-pipeline) approach to building data workflows. You can write SQL or Python in blocks and see results immediately.
    *   **DuckDB Support**: It has native DuckDB integration and is designed to replace traditional tools with a more modern, UI-heavy experience.
*   **[n8n](https://n8n.io/) (Fair-code / Open Source)**
    *   **How it's similar**: A highly interactive node-based workflow builder. While it's often used for API automation, it has powerful database nodes (including DuckDB via extensions/community) that let you build visual data logic.
*   **[Enso](https://enso.org/) (Open Source)**
    *   **How it's similar**: A visual programming language specifically for data science. It is extremely interactive, allowing you to switch between visual nodes and code (Rust/Java) seamlessly. It’s built for high-performance data processing.

### 2. DuckDB-Specific Web UIs
If your tool is more about "SQL exploration and light transformation," these are the competitors:

*   **[DuckDB-Studio](https://github.com/sql-js/duckdb-studio) (Open Source)**
    *   **How it's similar**: A web-based SQL editor specifically for DuckDB. It's lightweight and runs in the browser using Wasm.
    *   **Note**: It lacks the node-graph workflow component you've built, focusing instead on a classic SQL editor experience.
*   **[Duck-UI](https://github.com/caioricciuti/duck-ui) (Open Source)**
    *   **How it's similar**: Another Wasm-based IDE for DuckDB. Very fast and specialized for local data files.
*   **[Harlequin](https://github.com/tconbeer/harlequin) (Open Source)**
    *   **How it's similar**: A Terminal UI (TUI) for DuckDB. While not a web-app, it provides a very professional "IDE" feel for SQL workflows.

### 3. Visual BI & Analysis (The "Result" Side)
If your tool focuses on getting to a final report or dashboard:

*   **[Evidence.dev](https://evidence.dev/) (Open Source)**
    *   **How it's similar**: Built specifically for the "DuckDB + SQL" era. You write SQL and Markdown to create professional-grade data reports.
*   **[Rill Data](https://www.rilldata.com/) (Open Source Core)**
    *   **How it's similar**: An incredibly fast "BI-in-a-box" for DuckDB. It detects CSV/Parquet files and automatically builds a dashboard where you can filter and pivot data visually.

### How your tool compares:
Based on your recent progress (Undo/Redo, SQL beautification inside nodes, and group selection), your tool occupies a very specific niche: **a lightweight, visual "Data Engineering" IDE for DuckDB.**

Most tools are either:
1.  **Too heavy** (Enterprise ETL tools like NiFi).
2.  **Too static** (Classic SQL editors like DuckDB-Studio).
3.  **Too specific** (BI-only tools like Evidence).

Your tool bridges the gap by making the *logic-building* visual while keeping the engine (DuckDB) fast and the code (SQL) front and center.

**Are you looking to see how any of these specific tools handle a feature (like undo/redo or node-grouping) for inspiration?**