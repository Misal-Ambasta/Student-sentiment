// Route constants
export const ROUTES = {
  DASHBOARD: '/dashboard',
  UPLOAD: '/upload',
  CHAT: '/chat',
} as const;

export type RouteKey = keyof typeof ROUTES;
export type RoutePath = typeof ROUTES[RouteKey];