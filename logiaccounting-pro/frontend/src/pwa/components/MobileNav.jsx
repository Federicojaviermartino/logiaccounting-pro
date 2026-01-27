/**
 * MobileNav - Bottom tab navigation for mobile
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  FolderKanban,
  Package,
  MoreHorizontal,
  Plus,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Home' },
  { path: '/invoices', icon: FileText, label: 'Invoices' },
  { path: '/projects', icon: FolderKanban, label: 'Projects' },
  { path: '/inventory', icon: Package, label: 'Inventory' },
  { path: '/more', icon: MoreHorizontal, label: 'More' },
];

export default function MobileNav({ onFabClick }) {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200
                    safe-area-pb md:hidden">
      <div className="flex items-center justify-around h-16 relative">
        {NAV_ITEMS.map((item, index) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path ||
                          (item.path !== '/' && location.pathname.startsWith(item.path));

          // Insert FAB in the middle
          if (index === 2) {
            return (
              <React.Fragment key={item.path}>
                {/* FAB */}
                <button
                  onClick={onFabClick}
                  className="absolute -top-6 left-1/2 -translate-x-1/2 w-14 h-14
                             bg-gradient-to-r from-blue-600 to-purple-600 rounded-full
                             shadow-lg flex items-center justify-center text-white
                             active:scale-95 transition-transform"
                >
                  <Plus className="w-6 h-6" />
                </button>

                {/* Nav item */}
                <NavLink
                  to={item.path}
                  className={`flex flex-col items-center justify-center w-16 h-full
                             ${isActive ? 'text-blue-600' : 'text-gray-500'}`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-xs mt-1">{item.label}</span>
                </NavLink>
              </React.Fragment>
            );
          }

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center w-16 h-full
                         ${isActive ? 'text-blue-600' : 'text-gray-500'}`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs mt-1">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
