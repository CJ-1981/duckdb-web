import React from 'react';
import {
  Table, Filter, ArrowRightLeft, Settings, Play, Search, SlidersHorizontal,
  FileText, FileDown, Save, Sigma, Eye, SortAsc, ListOrdered, Calculator,
  Code, Fingerprint, PenLine, GitBranch, BarChart3, Plus, Trash2, Wand2,
  Microscope, PanelLeftClose, PanelLeftOpen, PanelBottomClose, Globe, Repeat,
  Dices, Braces, DatabaseBackup, MessageSquare
} from 'lucide-react';

interface NodePaletteProps {
  isCollapsed: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onShowTooltip: (e: React.MouseEvent, label: string, text: string) => void;
  onHideTooltip: () => void;
}

interface NodeItem {
  type: string;
  label: string;
  icon: React.ReactNode;
  tooltip: string;
  subtype?: string;
}

interface NodeCategory {
  title: string;
  items: NodeItem[];
}

export function NodePalette({ isCollapsed, searchQuery, onSearchChange, onShowTooltip, onHideTooltip }: NodePaletteProps) {
  const onDragStart = (event: React.DragEvent, nodeType: string, label: string, subtype?: string) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ type: nodeType, label, subtype }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const shouldShow = (label: string, desc?: string) => {
    const q = searchQuery.toLowerCase();
    return label.toLowerCase().includes(q) || (desc && desc.toLowerCase().includes(q));
  };

  const categories: NodeCategory[] = [
    {
      title: 'Data Sources',
      items: [
        { type: 'input', label: 'Data Files', icon: <Table size={16} />, tooltip: 'Upload or select local data files (CSV, Excel, JSON, Parquet) to analyze.' },
        { type: 'input', subtype: 'remote_file', label: 'Remote File / S3', icon: <Globe size={16} />, tooltip: 'Load data from an external HTTP URL or S3 Bucket.' },
        { type: 'input', subtype: 'rest_api', label: 'REST API', icon: <Repeat size={16} />, tooltip: 'Fetch data from REST API endpoints with auth and pagination.' },
        { type: 'input', subtype: 'web_scraper', label: 'Web Scraper', icon: <Search size={16} />, tooltip: 'Scrape tabular data from web pages using CSS selectors.' }
      ]
    },
    {
      title: 'Transformations',
      items: [
        { type: 'default', subtype: 'filter', label: 'Filter Records', icon: <Filter size={16} />, tooltip: 'Keep only records that match specific conditions.' },
        { type: 'default', subtype: 'combine', label: 'Combine Datasets', icon: <ArrowRightLeft size={16} />, tooltip: 'Join two separate tables together using common keys.' },
        { type: 'default', subtype: 'clean', label: 'Clean & Format', icon: <Settings size={16} />, tooltip: 'Standardize data quality: trim spaces, change case, or fix null values.' },
        { type: 'default', subtype: 'aggregate', label: 'Aggregate Data', icon: <Sigma size={16} />, tooltip: 'Summarize your data: calculate counts, averages, or totals grouped by categories.' },
        { type: 'default', subtype: 'sort', label: 'Sort Data', icon: <SortAsc size={16} />, tooltip: 'Reorder your records based on one or more column values.' },
        { type: 'default', subtype: 'limit', label: 'Limit Data', icon: <ListOrdered size={16} />, tooltip: 'Restrict the output to the first N rows of your dataset.' },
        { type: 'default', subtype: 'select', label: 'Select Columns', icon: <Table size={16} />, tooltip: 'Choose which columns to keep and which to discard from the dataset.' },
        { type: 'default', subtype: 'computed', label: 'Add Column', icon: <Calculator size={16} />, tooltip: 'Create new columns using arithmetic or SQL expressions.' },
        { type: 'default', subtype: 'rename', label: 'Rename Columns', icon: <PenLine size={16} />, tooltip: 'Modify column headers to make them more descriptive and readable.' },
        { type: 'default', subtype: 'distinct', label: 'Remove Duplicates', icon: <Fingerprint size={16} />, tooltip: 'Filter out identical rows to ensure data uniqueness.' },
        { type: 'default', subtype: 'case_when', label: 'Conditional Logic', icon: <GitBranch size={16} />, tooltip: 'Apply CASE-WHEN logic to create sophisticated branching rules.' },
        { type: 'default', subtype: 'window', label: 'Window Function', icon: <BarChart3 size={16} />, tooltip: 'Perform calculations across related rows (ranks, moving averages).' },
        { type: 'default', subtype: 'pivot', label: 'Pivot Data', icon: <Repeat size={16} />, tooltip: 'Reshape long data into wide format (rows to columns).' },
        { type: 'default', subtype: 'unpivot', label: 'Unpivot Data', icon: <Repeat size={16} />, tooltip: 'Reshape wide data into long format (columns to rows).' },
        { type: 'default', subtype: 'sample', label: 'Sample Data', icon: <Dices size={16} />, tooltip: 'Extract a random sample or specific percentage of the dataset.' },
        { type: 'default', subtype: 'unnest', label: 'Unnest / JSON', icon: <Braces size={16} />, tooltip: 'Unnest arrays or extract fields from JSON columns.' },
        { type: 'default', subtype: 'raw_sql', label: 'Custom SQL', icon: <Code size={16} />, tooltip: 'Maximum power: write your own DuckDB SQL to transform data.' }
      ]
    },
    {
      title: 'Outputs',
      items: [
        { type: 'output', subtype: 'report', label: 'Report Builder', icon: <FileText size={16} />, tooltip: 'Design a customized report (PDF/Markdown) from your pipeline results.' },
        { type: 'output', subtype: 'export', label: 'Export File', icon: <FileDown size={16} />, tooltip: 'Save your processed data to a CSV or Excel file for external use.' },
        { type: 'output', subtype: 'db_write', label: 'Write to DB', icon: <DatabaseBackup size={16} />, tooltip: 'Save your processed data directly as a table in the local database.' }
      ]
    },
    {
      title: 'Documentation',
      items: [
        { type: 'note', label: 'Note', icon: <MessageSquare size={16} />, tooltip: 'Add annotations and documentation to your workflow. Notes do not process data and are for documentation purposes only.' }
      ]
    }
  ];

  if (isCollapsed) {
    return null;
  }

  let totalShowing = 0;

  return (
    <aside className="w-64 bg-white border-r border-[#DFE1E6] flex flex-col overflow-y-auto">
      <div className="p-4 border-b border-[#DFE1E6]">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 text-[#6B778C]" size={16} />
          <input
            type="text"
            placeholder="Search components..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-10 py-2 text-sm border border-[#DFE1E6] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0052CC]"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-2.5 text-[#6B778C] hover:text-[#172B4D]"
            >
              <PanelLeftClose size={16} />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 p-4">
        {categories.map((category, catIdx) => {
          const filteredItems = category.items.filter(item => shouldShow(item.label, item.tooltip));
          totalShowing += filteredItems.length;

          if (filteredItems.length === 0) return null;

          return (
            <div key={catIdx} className="mb-6">
              <h3 className="text-xs font-semibold text-[#6B778C] uppercase tracking-wider mb-3">
                {category.title}
              </h3>
              <div className="space-y-2">
                {filteredItems.map((item, itemIdx) => (
                  <div
                    key={itemIdx}
                    draggable
                    onDragStart={(e) => onDragStart(e, item.type, item.label, item.subtype)}
                    onMouseEnter={(e) => onShowTooltip(e, item.label, item.tooltip)}
                    onMouseLeave={onHideTooltip}
                    className={`flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] rounded-md cursor-grab transition-all hover:shadow-sm ${
                      item.type === 'input' ? 'hover:border-[#0052CC]' :
                      item.type === 'output' ? 'hover:border-[#36B37E]' :
                      item.type === 'note' ? 'hover:border-[#F59E0B]' :
                      'hover:border-[#6554C0]'
                    }`}
                  >
                    <div className={`p-1.5 rounded ${
                      item.type === 'input' ? 'bg-blue-50 text-[#0052CC]' :
                      item.type === 'output' ? 'bg-green-50 text-[#36B37E]' :
                      item.type === 'note' ? 'bg-yellow-50 text-[#F59E0B]' :
                      'bg-purple-50 text-[#6554C0]'
                    }`}>
                      {item.icon}
                    </div>
                    <span className="text-sm font-medium text-gray-700">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {totalShowing === 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center bg-[#FAFBFC] rounded-lg border border-dashed border-[#DFE1E6]">
            <Search className="text-[#6B778C] mb-2 opacity-20" size={32} />
            <p className="text-sm font-medium text-[#171717]">No components found</p>
            <p className="text-xs text-[#6B778C] mt-1">Try another search term</p>
          </div>
        )}
      </div>
    </aside>
  );
}
