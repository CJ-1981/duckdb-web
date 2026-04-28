import React from 'react';
import { 
  Database, DatabaseBackup, Globe, FileSpreadsheet, 
  ShoppingCart, Users, BarChart, HardDrive, Search, X
} from 'lucide-react';

interface SamplePipelinesProps {
  isCollapsed: boolean;
  categories: Record<string, any[]>;
  onLoadSample: (sampleName: string) => void;
}

export function SamplePipelines({ isCollapsed, categories, onLoadSample }: SamplePipelinesProps) {
  if (isCollapsed) return null;

  const categoryNames = Object.keys(categories);

  return (
    <aside className="w-64 bg-white border-r border-[#DFE1E6] flex flex-col h-full">
      <div className="p-4 border-b border-gray-100 bg-gray-50/50">
        <h2 className="text-[12px] font-bold text-[#172B4D] uppercase tracking-wider flex items-center gap-2">
          <Database size={14} className="text-[#0052CC]" />
          Sample Pipelines
        </h2>
        <p className="text-[10px] text-[#6B778C] mt-1">
          Pre-built workflow templates for common data scenarios.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-6 custom-scrollbar">
        {categoryNames.map(cat => (
          <div key={cat} className="space-y-2">
            <h3 className="text-[10px] font-bold text-[#6B778C] uppercase tracking-tighter px-1 flex items-center gap-1.5">
              {cat}
            </h3>
            <div className="space-y-1">
              {categories[cat].map(sample => (
                <button
                  key={sample.name}
                  onClick={() => onLoadSample(sample.name)}
                  className="w-full text-left p-2.5 rounded-lg border border-transparent hover:border-[#0052CC]/20 hover:bg-[#DEEBFF]/30 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white rounded-md shadow-sm border border-gray-100 group-hover:scale-110 transition-transform">
                      {cat.includes('SQL') ? <DatabaseBackup size={16} className="text-blue-600" /> : 
                       cat.includes('MySQL') ? <DatabaseBackup size={16} className="text-cyan-600" /> :
                       cat.includes('API') ? <Globe size={16} className="text-orange-500" /> :
                       cat.includes('Ingestion') ? <HardDrive size={16} className="text-green-600" /> :
                       <BarChart size={16} className="text-[#0052CC]" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] font-bold text-[#172B4D] truncate group-hover:text-[#0052CC]">
                        {sample.name}
                      </div>
                      <div className="text-[9px] text-[#6B778C] line-clamp-2 mt-0.5 leading-tight">
                        {sample.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 bg-blue-50 border-t border-blue-100">
        <div className="text-[9px] text-blue-700 font-medium">
          💡 Clicking a sample will load it into a new tab.
        </div>
      </div>
    </aside>
  );
}
