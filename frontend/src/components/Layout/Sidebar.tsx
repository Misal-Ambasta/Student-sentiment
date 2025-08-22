import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  MessageSquare, 
  Menu,
  X,
  BarChart3,
  Settings,
  HelpCircle,
  FileText,
  Users
} from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { ROUTES } from '../../lib/constants';
import { cn } from '../../lib/utils';

const navigation = [
  {
    name: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: LayoutDashboard,
    description: 'Analytics overview'
  },
  {
    name: 'Upload Data',
    href: ROUTES.UPLOAD,
    icon: Upload,
    description: 'Upload survey files'
  },
  {
    name: 'Chat Assistant',
    href: ROUTES.CHAT,
    icon: MessageSquare,
    description: 'RAG-powered insights'
  },
  {
    name: 'Documents',
    href: '/documents',
    icon: FileText,
    description: 'Document management'
  },
  {
    name: 'Users',
    href: '/users',
    icon: Users,
    description: 'User management'
  },
];

const secondaryNavigation = [
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    description: 'Detailed reports'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'App configuration'
  },
  {
    name: 'Help',
    href: '/help',
    icon: HelpCircle,
    description: 'Documentation'
  },
];

const Sidebar: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 flex z-40 lg:hidden"
          role="dialog"
          aria-modal="true"
        >
          <div 
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            aria-hidden="true"
            onClick={() => setSidebarOpen(false)}
          />
          
          {/* Mobile sidebar */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full pt-5 pb-4 bg-white dark:bg-gray-800">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                type="button"
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <span className="sr-only">Close sidebar</span>
                <X className="h-6 w-6 text-white" aria-hidden="true" />
              </button>
            </div>
            
            <SidebarContent />
          </div>
          
          <div className="flex-shrink-0 w-14" aria-hidden="true">
            {/* Dummy element to force sidebar to shrink to fit close icon */}
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className={cn(
        "hidden lg:flex lg:flex-shrink-0 transition-all duration-200 z-40 fixed h-full",
        sidebarOpen ? "lg:w-64" : "lg:w-16"
      )}>
        <div className="flex flex-col w-full">
          <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto bg-white/95 backdrop-blur-xl border-r border-gray-200/50 shadow-xl h-screen">
            <SidebarContent collapsed={!sidebarOpen} />
          </div>
        </div>
      </div>
    </>
  );
};

interface SidebarContentProps {
  collapsed?: boolean;
}

const SidebarContent: React.FC<SidebarContentProps> = ({ collapsed = false }) => {
  const { setSidebarOpen } = useAppStore();

  return (
    <>
      {/* Logo and toggle */}
      <div className="flex items-center flex-shrink-0 px-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-10 w-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
          </div>
          {!collapsed && (
            <div className="ml-4">
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                RAG Student Sense
              </h1>
            </div>
          )}
        </div>
        
        {!collapsed && (
          <button
            type="button"
            className="ml-auto lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <span className="sr-only">Close sidebar</span>
            <X className="h-6 w-6 text-gray-400" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="mt-8 flex-1 px-2 space-y-2">
        {/* Primary navigation */}
        <div className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 relative overflow-hidden",
                    isActive
                      ? "bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 shadow-md border border-blue-100"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 hover:shadow-sm"
                  )
                }
                title={collapsed ? item.name : undefined}
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 rounded-xl" />
                    )}
                    <Icon className={cn(
                      "mr-3 flex-shrink-0 h-5 w-5 transition-colors relative z-10",
                      isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600"
                    )} aria-hidden="true" />
                    {!collapsed && (
                      <div className="flex-1 relative z-10">
                        <div>{item.name}</div>
                        <div className="text-xs text-gray-500">
                          {item.description}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Divider */}
        {!collapsed && (
          <div className="border-t border-gray-200/50 my-4" />
        )}

        {/* Secondary navigation */}
        <div className="space-y-2">
          {secondaryNavigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200",
                    isActive
                      ? "bg-white text-blue-700 shadow-sm border border-blue-100"
                      : "text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm"
                  )
                }
                title={collapsed ? item.name : undefined}
              >
                <Icon className="mr-3 flex-shrink-0 h-4 w-4 text-gray-400 group-hover:text-gray-600" aria-hidden="true" />
                {!collapsed && (
                  <div className="flex-1">
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-500">
                      {item.description}
                    </div>
                  </div>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="flex-shrink-0 px-4 py-4 border-t border-gray-200/50 bg-gray-50/50">
          <div className="text-xs text-gray-500">
            <div className="font-medium">Educational Analytics</div>
            <div>Powered by RAG AI</div>
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;