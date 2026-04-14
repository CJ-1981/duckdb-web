import React from 'react';
import {
  FolderOpen, Save, FileDown, FileText, Settings, Play, DatabaseBackup, Plus, Trash2, Edit2, PanelLeftOpen, PanelLeftClose, LayoutDashboard, PenLine, Wand2, SlidersHorizontal
 , RefreshCw } from 'lucide-react';

interface WorkflowToolbarProps {
  workflowName: string;
  onOpenLoadModal: () => void;
  onOpenSaveModal: () => void;
  onOpenSettings: () => void;
  onExecute: () => void;
  isExecuting: boolean;
  onRenameClick: () => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (val: boolean) => void;
  showHeaderTooltip: (e: React.MouseEvent, title: string, desc: string) => void;
  hideTooltip: () => void;
  isMac: boolean;
  setIsAiPipelinePanelOpen: (val: boolean) => void;
  handleBeautify: () => void;
  mod: string;
}

export function WorkflowToolbar({
  workflowName,
  onOpenLoadModal,
  onOpenSaveModal,
  onOpenSettings,
  onExecute,
  isExecuting,
  onRenameClick,
  isSidebarCollapsed,
  setIsSidebarCollapsed,
  showHeaderTooltip,
  hideTooltip,
  isMac,
  setIsAiPipelinePanelOpen,
  handleBeautify,
  mod
}: WorkflowToolbarProps) {
  return (
    <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-[#DFE1E6] shrink-0">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            onMouseEnter={(e) => showHeaderTooltip(e, isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar', `Toggle the component palette sidebar (${isMac ? '⌘' : 'Ctrl'}+[).`)}
            onMouseLeave={hideTooltip}
            className="p-2 text-[#6B778C] hover:bg-gray-100 rounded-md transition-colors mr-1"
          >
            {isSidebarCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
          </button>
          <div className="p-2 bg-[#0052CC] text-white rounded-md">
            <LayoutDashboard size={20} />
          </div>
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-bold text-[#171717]">
              Data Analyst Platform
            </h1>
            {workflowName && (
              <button
                onClick={onRenameClick}
                onMouseEnter={(e) => showHeaderTooltip(e, 'Rename Pipeline', 'Click to change the name of this pipeline.')}
                onMouseLeave={hideTooltip}
                className="text-sm font-medium text-[#6B778C] border-l border-[#DFE1E6] pl-3 flex items-center gap-1.5 hover:bg-gray-50 rounded px-1.5 py-0.5 transition-colors group animate-in fade-in slide-in-from-left-2 duration-300"
              >
                <FileText size={14} className="text-[#0052CC]/70 group-hover:text-[#0052CC]" />
                <span className="group-hover:text-[#172B4D]">{workflowName}</span>
                <PenLine size={12} className="opacity-0 group-hover:opacity-100 transition-opacity ml-1" />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsAiPipelinePanelOpen(true)}
            onMouseEnter={(e) => showHeaderTooltip(e, 'AI Pipeline Builder', 'Generate a pipeline using natural language.')}
            onMouseLeave={hideTooltip}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#0052CC] bg-[#EAE6FF] hover:bg-[#DED7FF] rounded-md transition-colors"
          >
            <Wand2 size={16} />
            <span>AI Builder</span>
          </button>
          <button
            onClick={handleBeautify}
            onMouseEnter={(e) => showHeaderTooltip(e, 'Beautify Layout', `Automatically organize nodes into a clean, hierarchical structure (${mod}B).`)}
            onMouseLeave={hideTooltip}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#0052CC] bg-white border border-[#0052CC]/30 hover:bg-blue-50 rounded-md transition-colors"
          >
            <SlidersHorizontal size={16} />
            <span>Beautify</span>
          </button>
          <button
            onClick={onOpenSaveModal}
            onMouseEnter={(e) => showHeaderTooltip(e, 'Save Pipeline', `Save your current workflow configuration to the server (${mod}S or ${mod}L).`)}
            onMouseLeave={hideTooltip}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors"
          >
            <Save size={16} />
            <span>Save</span>
          </button>
          <button
            onClick={onOpenSettings}
            onMouseEnter={(e) => showHeaderTooltip(e, 'Settings', 'Configure backend API connection and other settings.')}
            onMouseLeave={hideTooltip}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors"
          >
            <Settings size={16} />
            <span>Settings</span>
          </button>
          <button
            onClick={onOpenLoadModal}
            onMouseEnter={(e) => showHeaderTooltip(e, 'Open Pipeline', `Load a previously saved workflow from your library (${mod}O, ${mod}I, or ${mod}E).`)}
            onMouseLeave={hideTooltip}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors"
          >
            <FolderOpen size={16} />
            <span>Open</span>
          </button>
          <button
            onClick={onExecute}
            onMouseEnter={(e) => showHeaderTooltip(e, 'Execute Workflow', `Run the entire pipeline processing logic and generate results (${mod}R or ${mod}Enter).`)}
            onMouseLeave={hideTooltip}
            disabled={isExecuting}
            className={`ml-2 flex items-center space-x-2 px-4 py-2 text-sm font-bold text-white bg-[#0052CC] hover:bg-[#0047B3] rounded-md transition-colors ${
              isExecuting ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            {isExecuting ? (
              <><RefreshCw size={16} className="animate-spin" /><span>Executing...</span></>
            ) : (
              <><Play size={16} fill="currentColor" /><span>Execute Pipeline</span></>
            )}
          </button>
        </div>
      </header>
  );
}
