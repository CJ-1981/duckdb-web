import React from 'react';

export default function WorkflowLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#FAFBFC]">
      {children}
    </div>
  );
}
