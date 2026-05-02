"use client";

import {
  Play,
  FolderOpen,
  ChevronRight,
  Plus,
  FileText,
  Home,
  X
} from 'lucide-react';

interface MobileNavigationProps {
  onExecute: () => void;
  onLoad: () => void;
  currentWorkflowName?: string;
}

export function MobileNavigation({
  onExecute,
  onLoad,
  currentWorkflowName,
}: MobileNavigationProps) {
  const primaryActions = [
    { icon: Play, label: 'Run', action: onExecute, color: 'bg-[#0052CC]' },
    { icon: FolderOpen, label: 'Open', action: onLoad, color: 'bg-[#6554C0]' },
  ];

  const secondaryActions: Array<{ icon: any; label: string; action: () => void }> = [];

  return (
    <>
      {/* Bottom Navigation Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-[#DFE1E6] shadow-lg md:hidden safe-area-inset-bottom">
        {/* Primary Actions Row */}
        <div className="flex items-center justify-around px-2 py-3">
          {primaryActions.map((action) => (
            <button
              key={action.label}
              onClick={action.action}
              className={`flex flex-col items-center space-y-1 px-4 py-2 rounded-lg transition-all active:scale-95 ${action.color} text-white`}
              style={{ minWidth: '70px' }}
            >
              <action.icon size={20} strokeWidth={2.5} />
              <span className="text-[10px] font-bold uppercase tracking-wide">{action.label}</span>
            </button>
          ))}
        </div>

        {/* Secondary Actions Row */}
        <div className="flex items-center justify-around px-2 pb-3 border-t border-[#DFE1E6] pt-2">
          {secondaryActions.map((action) => (
            <button
              key={action.label}
              onClick={action.action}
              className="flex flex-col items-center space-y-1 px-3 py-1.5 rounded-md transition-all active:scale-95 text-[#6B778C] hover:bg-[#F4F5F7] hover:text-[#0052CC]"
              style={{ minWidth: '60px' }}
            >
              <action.icon size={16} strokeWidth={2} />
              <span className="text-[9px] font-semibold">{action.label}</span>
            </button>
          ))}
        </div>

        {/* Workflow Name Indicator */}
        {currentWorkflowName && (
          <div className="px-3 py-2 bg-[#FAFBFC] border-t border-[#DFE1E6] flex items-center space-x-2">
            <FileText size={12} className="text-[#0052CC]" />
            <span className="text-[10px] font-semibold text-[#172B4D] truncate flex-1">
              {currentWorkflowName}
            </span>
            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase bg-[#EDEFFF] text-[#0052CC]">
              View Only
            </span>
          </div>
        )}
      </div>

      {/* Spacer for bottom navigation */}
      <div className="h-40 md:hidden" />
    </>
  );
}

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onNewWorkflow: () => void;
  onLoad: () => void;
}

export function MobileMenu({
  isOpen,
  onClose,
  onNewWorkflow,
  onLoad,
}: MobileMenuProps) {
  if (!isOpen) return null;

  const menuItems = [
    { icon: Home, label: 'Dashboard', action: () => window.location.href = '/' },
    { icon: Plus, label: 'New Workflow', action: onNewWorkflow },
    { icon: FolderOpen, label: 'Open Workflow', action: onLoad },
  ];

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-50 md:hidden"
        onClick={onClose}
      />
      <div className="fixed left-0 top-0 bottom-0 w-72 bg-white z-50 shadow-xl md:hidden">
        <div className="p-4 bg-[#0052CC] text-white">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-bold">Menu</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-md transition-colors"
            >
              <X size={20} />
            </button>
          </div>
          <p className="text-xs opacity-80">DuckDB Workflow Builder</p>
        </div>

        <nav className="p-2">
          {menuItems.map((item) => (
            <button
              key={item.label}
              onClick={() => {
                item.action();
                onClose();
              }}
              className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-[#172B4D] hover:bg-[#F4F5F7] transition-colors mb-1"
            >
              <item.icon size={18} className="text-[#0052CC]" />
              <span className="font-medium">{item.label}</span>
              <ChevronRight size={16} className="ml-auto text-[#6B778C]" />
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#FAFBFC] border-t border-[#DFE1E6]">
          <p className="text-[10px] text-[#6B778C] text-center">
            v1.0.0 • Mobile Optimized
          </p>
        </div>
      </div>
    </>
  );
}
