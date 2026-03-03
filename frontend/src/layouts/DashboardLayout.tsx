import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Phone,
  Database,
  FileSpreadsheet,
  Settings,
  LogOut,
  Menu,
  ChevronLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth-store';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/calls', icon: Phone, label: 'Calls' },
  { to: '/extraction', icon: Database, label: 'Extraction' },
  { to: '/exports', icon: FileSpreadsheet, label: 'Exports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-sidebar-accent">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-white font-bold text-sm">
          VA
        </div>
        {!collapsed && <span className="text-white font-semibold text-sm">Voice Agent</span>}
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent',
                collapsed && 'justify-center',
              )
            }
          >
            <item.icon size={20} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User section */}
      <div className="border-t border-sidebar-accent p-4">
        {!collapsed && user && (
          <div className="mb-3">
            <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
            <p className="text-xs text-gray-400 truncate">{user.email}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-full',
            collapsed && 'justify-center',
          )}
        >
          <LogOut size={18} />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden lg:flex flex-col bg-sidebar transition-all duration-300',
          collapsed ? 'w-[68px]' : 'w-60',
        )}
      >
        {sidebarContent}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute top-4 -right-3 z-50 hidden lg:flex h-6 w-6 items-center justify-center rounded-full border bg-white shadow-sm hover:bg-gray-100"
          style={{ left: collapsed ? 56 : 228 }}
        >
          <ChevronLeft size={14} className={cn(collapsed && 'rotate-180')} />
        </button>
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-60 bg-sidebar h-full">
            {sidebarContent}
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center h-14 px-4 border-b bg-white lg:px-6">
          <button onClick={() => setMobileOpen(true)} className="lg:hidden mr-3">
            <Menu size={22} />
          </button>
          <div className="flex-1" />
          <div className="text-sm text-gray-500">{user?.email}</div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
