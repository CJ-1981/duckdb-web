import { useState, useEffect } from 'react';
import { listSavedWorkflows, deleteWorkflow, loadWorkflowGraph } from '@/lib/api-unified';
import { FolderOpen, Trash2, PenLine, FileDown, Search, AlertCircle } from 'lucide-react';

interface WorkflowListProps {
  onLoadWorkflow: (name: string) => void;
  onClose: () => void;
}

export function WorkflowList({ onLoadWorkflow, onClose }: WorkflowListProps) {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [renamingWorkflow, setRenamingWorkflow] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const { workflows: workflowList } = await listSavedWorkflows();
      setWorkflows(workflowList || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleLoad = async (name: string) => {
    try {
      await loadWorkflowGraph(name);
      // Pass the loaded workflow data to parent
      onLoadWorkflow(name);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to load workflow');
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete workflow '${name}'? This cannot be undone.`)) return;

    try {
      setDeleteLoading(name);
      await deleteWorkflow(name);
      setWorkflows(workflows.filter(w => w !== name));
    } catch (err: any) {
      setError(err.message || 'Failed to delete workflow');
    } finally {
      setDeleteLoading(null);
    }
  };

  const startRename = (name: string) => {
    setRenamingWorkflow(name);
    setRenameValue(name);
  };

  const cancelRename = () => {
    setRenamingWorkflow(null);
    setRenameValue('');
  };

  const confirmRename = async (_oldName: string) => {
    // Implement rename logic if API supports it
    setRenamingWorkflow(null);
    setRenameValue('');
  };

  const exportWorkflow = async (name: string) => {
    try {
      const workflowData = await loadWorkflowGraph(name);
      const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Failed to export workflow');
    }
  };

  const filteredWorkflows = workflows.filter(w =>
    w.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
      <div className="p-6 border-b border-[#DFE1E6]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-[#171717] flex items-center gap-2">
            <FolderOpen size={24} className="text-[#0052CC]" />
            Saved Workflows
          </h2>
          <button
            onClick={onClose}
            className="text-[#6B778C] hover:text-[#171717] transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-2.5 text-[#6B778C]" size={18} />
          <input
            type="text"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[#DFE1E6] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0052CC]"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0052CC]"></div>
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="text-center py-12">
            <FolderOpen size={48} className="mx-auto text-[#6B778C] mb-4 opacity-20" />
            <p className="text-[#6B778C]">
              {searchQuery ? 'No workflows match your search' : 'No saved workflows found'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredWorkflows.map((name) => (
              <div
                key={name}
                className="flex items-center justify-between p-4 border border-[#DFE1E6] rounded-md hover:bg-[#F4F5F7] transition-colors group"
              >
                {renamingWorkflow === name ? (
                  <div className="flex-1 flex items-center gap-2">
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') confirmRename(name);
                        if (e.key === 'Escape') cancelRename();
                      }}
                      className="flex-1 px-3 py-2 border border-[#DFE1E6] rounded-md text-sm"
                      autoFocus
                    />
                    <button
                      onClick={() => confirmRename(name)}
                      className="px-3 py-2 bg-[#0052CC] text-white rounded-md text-sm hover:bg-[#0065FF]"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelRename}
                      className="px-3 py-2 bg-white border border-[#DFE1E6] rounded-md text-sm hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleLoad(name)}
                      className="flex-1 text-left font-medium text-[#171717] group-hover:text-[#0052CC]"
                    >
                      {name}
                    </button>

                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => exportWorkflow(name)}
                        className="p-2 text-[#6B778C] hover:text-[#0052CC] hover:bg-blue-50 rounded-md transition-colors"
                        title="Export workflow"
                      >
                        <FileDown size={16} />
                      </button>
                      <button
                        onClick={() => startRename(name)}
                        className="p-2 text-[#6B778C] hover:text-[#0052CC] hover:bg-blue-50 rounded-md transition-colors"
                        title="Rename workflow"
                      >
                        <PenLine size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(name)}
                        disabled={deleteLoading === name}
                        className="p-2 text-[#6B778C] hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                        title="Delete workflow"
                      >
                        {deleteLoading === name ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-[#DFE1E6] bg-[#FAFBFC]">
        <div className="flex items-center justify-between text-sm text-[#6B778C]">
          <span>{workflows.length} workflows</span>
          <button
            onClick={loadWorkflows}
            className="text-[#0052CC] hover:underline"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
}
