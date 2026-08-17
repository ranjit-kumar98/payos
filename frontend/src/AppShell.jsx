import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { HomeIcon, CurrencyDollarIcon, ShieldCheckIcon, ClipboardDocumentListIcon, CreditCardIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: HomeIcon },
  { name: 'Transactions', path: '/transactions', icon: CurrencyDollarIcon },
  { name: 'Fraud Monitor', path: '/fraud', icon: ShieldCheckIcon },
  { name: 'Disputes', path: '/disputes', icon: ClipboardDocumentListIcon },
  { name: 'BNPL', path: '/bnpl', icon: CreditCardIcon },
  { name: 'Checkout Demo', path: '/checkout', icon: ShoppingCartIcon },
];

export function AppShell() {
  const location = useLocation();

  const currentNav = navItems.find(item => location.pathname.startsWith(item.path));
  const pageTitle = currentNav ? currentNav.name : '';

  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-60 bg-gray-900 text-white flex flex-col">
        <div className="h-16 flex items-center justify-center font-bold text-xl border-b border-gray-700">
          PayOS
        </div>
        <nav className="flex-1 overflow-y-auto">
          {navItems.map(({ name, path, icon: Icon }) => (
            <NavLink
              key={name}
              to={path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 hover:bg-gray-700 ${
                  isActive ? 'bg-blue-600' : ''
                }`
              }
            >
              <Icon className="h-6 w-6 mr-3" />
              <span>{name}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white shadow flex items-center px-6">
          <h1 className="text-xl font-semibold">{pageTitle}</h1>
        </header>
        <main className="flex-1 overflow-y-auto p-6 bg-gray-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
