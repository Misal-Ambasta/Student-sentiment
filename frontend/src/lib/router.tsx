import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import Dashboard from '../pages/Dashboard';
import Upload from '../pages/Upload';
import Chat from '../pages/Chat';
import ErrorBoundary from '../components/ErrorBoundary';
import { ROUTES } from './constants';

// Re-export for convenience
export { ROUTES, type RouteKey, type RoutePath } from './constants';

// Route configuration
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <ErrorBoundary />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'upload',
        element: <Upload />,
      },
      {
        path: 'chat',
        element: <Chat />,
      },
      {
        path: '*',
        element: <Navigate to="/dashboard" replace />,
      },
    ],
  },
]);