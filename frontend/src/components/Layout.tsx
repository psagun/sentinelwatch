import { useState } from 'react';
import Sidebar from './Sidebar';
import type { NavPage } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

export default function Layout({ children, activePage, onNavigate }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      <Sidebar
        active={activePage}
        onNavigate={onNavigate}
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
      />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1440px] mx-auto px-6 py-6">{children}</div>
      </main>
    </div>
  );
}
