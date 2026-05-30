import {
  LayoutDashboard,
  Search,
  Bell,
  Globe,
  Shield,
  ShieldCheck,
  Info,
  Award,
  FileText,
  Presentation,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { NavPage } from '../types';

interface SidebarProps {
  active: NavPage;
  onNavigate: (page: NavPage) => void;
  collapsed: boolean;
  onToggle: () => void;
}

const navItems: { page: NavPage; label: string; icon: React.ReactNode }[] = [
  { page: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { page: 'findings', label: 'Findings', icon: <Search size={18} /> },
  { page: 'alerts', label: 'Alerts', icon: <Bell size={18} /> },
  { page: 'entities', label: 'Entities', icon: <Globe size={18} /> },
  { page: 'compliance', label: 'Compliance', icon: <ShieldCheck size={18} /> },
  { page: 'reports', label: 'Reports', icon: <FileText size={18} /> },
  { page: 'presentation', label: 'Presentation', icon: <Presentation size={18} /> },
  { page: 'about', label: 'About', icon: <Info size={18} /> },
  { page: 'hackathon', label: 'Hackathon', icon: <Award size={18} /> },
];

export default function Sidebar({ active, onNavigate, collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={`h-screen bg-surface-100 border-r border-border flex flex-col transition-all duration-300 ease-in-out ${
        collapsed ? 'w-[60px]' : 'w-[220px]'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-border shrink-0">
        <div className="w-8 h-8 rounded-lg bg-accent-cyan/20 flex items-center justify-center shrink-0">
          <Shield size={16} className="text-accent-cyan" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold text-text-primary tracking-tight leading-tight">
              SentinelWatch
            </h1>
            <p className="text-[10px] text-text-muted font-medium tracking-wider uppercase">
              Security Platform
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 px-2 py-4 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={`nav-item group ${active === item.page ? 'active' : ''}`}
            title={collapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!collapsed && (
              <span className="truncate text-sm">{item.label}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border p-2">
        <button
          onClick={onToggle}
          className="nav-item w-full justify-center text-text-muted hover:text-text-primary"
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          {!collapsed && <span className="text-xs">Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
