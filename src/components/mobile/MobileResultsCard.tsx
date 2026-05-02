"use client";

import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Table,
  BarChart3,
  Download,
  Share2,
  Maximize2,
  Eye,
  Filter,
  Search,
  X,
  FileText,
  Calendar,
  Hash,
  CheckCheck
} from 'lucide-react';
import { type ColumnTypeDef } from '@/components/panels/DataInspectionPanel';

interface MobileResultsCardProps {
  title: string;
  data: any[];
  columns?: ColumnTypeDef[];
  rowCount?: number;
  onExport?: () => void;
  onShare?: () => void;
  onFilter?: () => void;
  maxHeight?: string;
}

// Helper components defined outside to avoid "Components created during render" ESLint error
interface TableViewProps {
  displayData: any[];
  columns?: ColumnTypeDef[];
  getDataTypeIcon: (dataType: string) => React.ReactElement;
  formatCellValue: (value: any) => React.ReactNode;
}

function TableView({ displayData, columns, getDataTypeIcon, formatCellValue }: TableViewProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-[#F4F5F7] border-b border-[#DFE1E6]">
            <th className="px-3 py-2 text-left font-bold text-[#172B4D] uppercase tracking-wider text-[10px]">
              Row
            </th>
            {columns?.slice(0, 3).map((col) => (
              <th key={col.column_name} className="px-3 py-2 text-left font-bold text-[#172B4D] uppercase tracking-wider text-[10px]">
                <div className="flex items-center space-x-1">
                  {getDataTypeIcon(col.column_type)}
                  <span className="truncate">{col.column_name}</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, idx) => (
            <tr
              key={idx}
              className="border-b border-[#DFE1E6] hover:bg-[#FAFBFC] transition-colors"
            >
              <td className="px-3 py-2 text-[#6B778C] font-medium">{idx + 1}</td>
              {columns?.slice(0, 3).map((col) => (
                <td key={col.column_name} className="px-3 py-2">
                  {formatCellValue(row[col.column_name])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface CardViewProps {
  displayData: any[];
  expandedRow: number | null;
  setExpandedRow: (idx: number | null) => void;
  formatCellValue: (value: any) => React.ReactNode;
}

function CardView({ displayData, expandedRow, setExpandedRow, formatCellValue }: CardViewProps) {
  return (
    <div className="space-y-2">
      {displayData.map((row, idx) => (
        <div
          key={idx}
          className="bg-white border border-[#DFE1E6] rounded-lg overflow-hidden transition-all"
        >
          <button
            onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
            className="w-full px-3 py-2.5 flex items-center justify-between hover:bg-[#FAFBFC] transition-colors"
          >
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded-full bg-[#EDEFFF] flex items-center justify-center text-[10px] font-bold text-[#0052CC]">
                {idx + 1}
              </div>
              <span className="text-xs font-semibold text-[#172B4D]">Row {idx + 1}</span>
            </div>
            {expandedRow === idx ? (
              <ChevronUp size={16} className="text-[#6B778C]" />
            ) : (
              <ChevronDown size={16} className="text-[#6B778C]" />
            )}
          </button>

          {expandedRow === idx && (
            <div className="px-3 pb-3 border-t border-[#DFE1E6] pt-2">
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(row).map(([key, value]) => (
                  <div key={key} className="flex items-start justify-between">
                    <span className="text-[10px] font-medium text-[#6B778C] uppercase tracking-wide">
                      {key}
                    </span>
                    <span className="text-xs font-semibold text-[#172B4D] text-right ml-2">
                      {formatCellValue(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function MobileResultsCard({
  title,
  data,
  columns,
  rowCount,
  onExport,
  onShare,
  onFilter,
  maxHeight = '400px',
}: MobileResultsCardProps) {
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'card'>('card');

  // Filter data based on search
  const filteredData = data.filter(row => {
    if (!searchQuery) return true;
    const searchStr = JSON.stringify(row).toLowerCase();
    return searchStr.includes(searchQuery.toLowerCase());
  });

  const displayData = filteredData.slice(0, isExpanded ? undefined : 5);

  const getDataTypeIcon = (dataType: string) => {
    const type = dataType.toLowerCase();
    if (type.includes('int') || type.includes('numeric') || type.includes('bigint') || type.includes('double') || type.includes('float')) return <Hash size={12} />;
    if (type.includes('char') || type.includes('text') || type.includes('varchar')) return <FileText size={12} />;
    if (type.includes('date') || type.includes('timestamp')) return <Calendar size={12} />;
    return <Table size={12} />;
  };

  const formatCellValue = (value: any) => {
    if (value === null || value === undefined) return <span className="text-[#6B778C] italic">NULL</span>;
    if (typeof value === 'number') return <span className="text-[#0052CC] font-semibold">{value.toLocaleString()}</span>;
    if (typeof value === 'boolean') return <span className={value ? 'text-[#36B37E]' : 'text-[#FF5630]'}>{value.toString()}</span>;
    if (typeof value === 'object') return <span className="text-[#6B778C] text-[10px]">{JSON.stringify(value)}</span>;
    return <span className="text-[#172B4D]">{String(value)}</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-[#DFE1E6] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-[#FAFBFC] border-b border-[#DFE1E6]">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-bold text-[#172B4D]">{title}</h3>
          <div className="flex items-center space-x-1">
            {onFilter && (
              <button
                onClick={onFilter}
                className="p-1.5 hover:bg-[#F4F5F7] rounded-md transition-colors"
                title="Filter"
              >
                <Filter size={14} className="text-[#6B778C]" />
              </button>
            )}
            {onShare && (
              <button
                onClick={onShare}
                className="p-1.5 hover:bg-[#F4F5F7] rounded-md transition-colors"
                title="Share"
              >
                <Share2 size={14} className="text-[#6B778C]" />
              </button>
            )}
            {onExport && (
              <button
                onClick={onExport}
                className="p-1.5 hover:bg-[#F4F5F7] rounded-md transition-colors"
                title="Export"
              >
                <Download size={14} className="text-[#6B778C]" />
              </button>
            )}
          </div>
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <Hash size={12} className="text-[#6B778C]" />
              <span className="text-[10px] text-[#6B778C]">
                {rowCount !== undefined ? rowCount.toLocaleString() : data.length} rows
              </span>
            </div>
            {columns && (
              <div className="flex items-center space-x-1">
                <Table size={12} className="text-[#6B778C]" />
                <span className="text-[10px] text-[#6B778C]">{columns.length} columns</span>
              </div>
            )}
          </div>

          <button
            onClick={() => setViewMode(viewMode === 'table' ? 'card' : 'table')}
            className="p-1.5 hover:bg-[#F4F5F7] rounded-md transition-colors"
            title="Toggle view"
          >
            {viewMode === 'table' ? <Table size={14} /> : <BarChart3 size={14} />}
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="px-4 py-2 border-b border-[#DFE1E6]">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B778C]" />
          <input
            type="text"
            placeholder="Search data..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 text-xs border border-[#DFE1E6] rounded-md focus:ring-2 focus:ring-[#0052CC] focus:border-transparent outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[#6B778C] hover:text-[#172B4D]"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {filteredData.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-[#6B778C]">
            <Search size={24} className="mb-2" />
            <p className="text-xs">No results found for &quot;{searchQuery}&quot;</p>
          </div>
        ) : (
          <>
            {viewMode === 'table' ? (
              <TableView displayData={displayData} columns={columns} getDataTypeIcon={getDataTypeIcon} formatCellValue={formatCellValue} />
            ) : (
              <CardView displayData={displayData} expandedRow={expandedRow} setExpandedRow={setExpandedRow} formatCellValue={formatCellValue} />
            )}

            {/* Show More/Less Button */}
            {filteredData.length > 5 && (
              <div className="px-4 py-3 border-t border-[#DFE1E6] bg-[#FAFBFC]">
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="w-full py-2 text-xs font-bold text-[#0052CC] hover:bg-[#EDEFFF] rounded-md transition-colors flex items-center justify-center space-x-1"
                >
                  {isExpanded ? (
                    <>
                      <ChevronUp size={14} />
                      <span>Show Less</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={14} />
                      <span>Show {filteredData.length - 5} More Rows</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer with Quick Actions */}
      <div className="px-4 py-2 bg-[#FAFBFC] border-t border-[#DFE1E6] flex items-center justify-between">
        <span className="text-[10px] text-[#6B778C]">
          Showing {displayData.length} of {filteredData.length} rows
        </span>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              // Handle fullscreen view
            }}
            className="p-1.5 hover:bg-[#F4F5F7] rounded-md transition-colors"
            title="Fullscreen"
          >
            <Maximize2 size={12} className="text-[#6B778C]" />
          </button>
          <button
            onClick={() => {
              // Handle preview action
            }}
            className="p-1.5 bg-[#0052CC] hover:bg-[#0065FF] text-white rounded-md transition-colors"
            title="Preview"
          >
            <Eye size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

interface ExecutionStatusCardProps {
  isExecuting: boolean;
  success?: boolean;
  message?: string;
  result?: any;
  onRetry?: () => void;
}

export function ExecutionStatusCard({
  isExecuting,
  success,
  message,
  result,
  onRetry,
}: ExecutionStatusCardProps) {
  if (isExecuting) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-[#DFE1E6] p-4 animate-pulse">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 border-2 border-[#0052CC] border-t-transparent rounded-full animate-spin" />
          <div>
            <p className="text-sm font-bold text-[#172B4D]">Executing Workflow...</p>
            <p className="text-xs text-[#6B778C]">Please wait</p>
          </div>
        </div>
      </div>
    );
  }

  if (success === false) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-[#FF5630] p-4">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-[#FFEBE6] rounded-full flex items-center justify-center flex-shrink-0">
            <X size={16} className="text-[#FF5630]" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-[#172B4D] mb-1">Execution Failed</p>
            <p className="text-xs text-[#6B778C] mb-3">{message || 'An error occurred'}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="w-full py-2 bg-[#0052CC] text-white text-xs font-bold rounded-md active:scale-95 transition-transform"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (success === true && result) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-[#36B37E] p-4">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-[#E3FCEF] rounded-full flex items-center justify-center flex-shrink-0">
            <CheckCheck size={16} className="text-[#36B37E]" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-[#172B4D] mb-1">Execution Successful</p>
            <div className="space-y-1 mb-3">
              {result.row_count && (
                <p className="text-xs text-[#6B778C]">
                  Processed <span className="font-bold text-[#0052CC]">{result.row_count.toLocaleString()}</span> rows
                </p>
              )}
              {result.execution_time && (
                <p className="text-xs text-[#6B778C]">
                  Completed in <span className="font-bold text-[#172B4D]">{(result.execution_time / 1000).toFixed(2)}s</span>
                </p>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  // Handle view results
                }}
                className="flex-1 py-2 bg-[#0052CC] text-white text-xs font-bold rounded-md active:scale-95 transition-transform"
              >
                View Results
              </button>
              <button
                onClick={() => {
                  // Handle export
                }}
                className="px-3 py-2 bg-[#EDEFFF] text-[#0052CC] text-xs font-bold rounded-md active:scale-95 transition-transform"
              >
                <Download size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
