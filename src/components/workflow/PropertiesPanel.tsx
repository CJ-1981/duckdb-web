import React from 'react';
import { Node, Edge } from '@xyflow/react';
import { SlidersHorizontal, PenLine, Trash2, Plus, Save } from 'lucide-react';

interface PropertiesPanelProps {
  node: Node;
  onUpdate: (node: Node) => void;
  getUpstreamColumns: () => string[];
  nodes: Node[];
  edges: Edge[];
}

export function PropertiesPanel({ node, onUpdate, getUpstreamColumns, nodes, edges }: PropertiesPanelProps) {
  const [saveSuccess, setSaveSuccess] = React.useState(false);

  const handleSave = () => {
    onUpdate(node);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const updateNodeData = (key: string, value: any) => {
    onUpdate({
      ...node,
      data: {
        ...node.data,
        [key]: value
      }
    });
  };

  const updateConfig = (key: string, value: any) => {
    onUpdate({
      ...node,
      data: {
        ...node.data,
        config: {
          ...(node.data.config as any || {}),
          [key]: value
        }
      }
    });
  };

  return (
    <aside className="w-80 bg-white border-l border-[#DFE1E6] flex flex-col overflow-y-auto">
      <div className="p-4 border-b border-[#DFE1E6] bg-[#FAFBFC] flex items-center space-x-2">
        <SlidersHorizontal size={18} className="text-[#6B778C]" />
        <h2 className="text-sm font-semibold text-gray-800">Node Properties</h2>
      </div>

      <div className="p-4 flex-1">
        <h3 className="text-base font-medium text-[#171717] mb-4 flex items-center justify-between group">
          <div className="flex items-center flex-1 mr-2">
            <input
              type="text"
              value={String(node.data?.label || '')}
              onChange={(e) => updateNodeData('label', e.target.value)}
              className="flex-1 bg-transparent border-none focus:outline-none font-semibold text-lg"
              placeholder="Node Label"
            />
          </div>
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-2">Node Type</label>
            <div className="px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md text-sm text-[#171717]">
              {String(node.type)}
              {node.data?.subtype ? <span className="ml-2 text-[#6B778C]">({String(node.data.subtype)})</span> : null}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-2">Node ID</label>
            <div className="px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md text-xs font-mono text-[#6B778C]">
              {node.id}
            </div>
          </div>

          {node.type === 'note' && (
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-2">Description</label>
              <textarea
                value={String(node.data?.description || '')}
                onChange={(e) => updateNodeData('description', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm min-h-[100px] resize-vertical"
                placeholder="Add documentation, notes, or instructions..."
              />
            </div>
          )}

          {(node.data?.config as any)?.file_path && (
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-2">File Path</label>
              <div className="px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md text-xs font-mono text-[#171717]">
                {(node.data.config as any).file_path}
              </div>
            </div>
          )}

          {node.data?.rowCount !== undefined && node.data.rowCount !== null && (
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-2">Row Count</label>
              <div className="px-3 py-2 bg-[#EAE6FF] border border-[#D1CAFF] rounded-md text-sm font-bold text-[#403294]">
                {(node.data.rowCount as number).toLocaleString()} rows
              </div>
            </div>
          )}

          {/* Add more configuration fields based on node type */}
          {node.data?.subtype === 'filter' && (
            <div className="space-y-3 pt-3 border-t border-[#DFE1E6]">
              <h4 className="text-xs font-semibold text-[#6B778C]">Filter Configuration</h4>
              <div>
                <label className="block text-xs text-[#6B778C] mb-1">Column</label>
                <select
                  value={String((node.data?.config as any)?.column || '')}
                  onChange={(e) => updateConfig('column', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select column...</option>
                  {getUpstreamColumns().map((col: string) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-[#6B778C] mb-1">Operator</label>
                <select
                  value={String((node.data?.config as any)?.operator || '==')}
                  onChange={(e) => updateConfig('operator', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                >
                  <option value="==">is equal to</option>
                  <option value="!=">is not equal to</option>
                  <option value=">">is greater than</option>
                  <option value="<">is less than</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-[#6B778C] mb-1">Value</label>
                <input
                  type="text"
                  value={String((node.data?.config as any)?.value || '')}
                  onChange={(e) => updateConfig('value', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                  placeholder="Filter value..."
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-[#DFE1E6]">
        <button
          onClick={handleSave}
          disabled={saveSuccess}
          className={`w-full px-4 py-2 text-white text-sm font-medium rounded-md transition-all flex items-center justify-center space-x-2 ${
            saveSuccess ? 'bg-[#36B37E]' : 'bg-[#0052CC] hover:bg-[#0065FF]'
          }`}
        >
          <Save size={16} />
          <span>{saveSuccess ? 'Saved!' : 'Save Changes'}</span>
        </button>
      </div>
    </aside>
  );
}
