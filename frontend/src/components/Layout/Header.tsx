import React from 'react';
import { Bell, Search, User, Menu, X } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { cn } from '../../lib/utils';
import Button from '../UI/Button';

const Header: React.FC = () => {
  const { sidebarOpen, setSidebarOpen, user } = useAppStore();

  return (
    <div className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200/50 bg-white/95 backdrop-blur-xl px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8 w-full">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="sm"
        className="lg:hidden hover:bg-gray-100 rounded-xl transition-all duration-200"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <Menu className="h-6 w-6" />
        )}
      </Button>

      {/* Separator */}
      <div className="h-6 w-px bg-gray-200/50 lg:hidden" />

      {/* Search */}
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <form className="relative flex flex-1 max-w-md" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">
            Search
          </label>
          <div className="relative w-full">
            <Search className="pointer-events-none absolute inset-y-0 left-3 h-full w-5 text-gray-400" />
            <input
              id="search-field"
              className="block h-10 w-full rounded-xl border border-gray-200 bg-gray-50/50 py-0 pl-10 pr-4 text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 sm:text-sm transition-all duration-200"
              placeholder="Search documents, chats..."
              type="search"
              name="search"
            />
          </div>
        </form>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-x-3 lg:gap-x-4">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="sm"
          className="relative hover:bg-gray-100 rounded-xl transition-all duration-200 p-2"
          aria-label="View notifications"
        >
          <Bell className="h-5 w-5 text-gray-600" />
          {/* Notification badge */}
          <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-gradient-to-r from-red-500 to-pink-500 text-xs text-white flex items-center justify-center font-medium shadow-lg animate-pulse">
            3
          </span>
        </Button>

        {/* Separator */}
        <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-200/50" />

        {/* Profile dropdown */}
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            className="flex items-center gap-x-3 hover:bg-gray-100 rounded-xl transition-all duration-200 p-2"
            aria-label="Open user menu"
          >
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
              <User className="h-4 w-4 text-white" />
            </div>
            <span className="hidden lg:flex lg:items-center">
              <span className="text-sm font-semibold leading-6 text-gray-900">
                {user?.name || 'User'}
              </span>
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Header;