/**
 * EA Analyzer Theme Configuration
 * 
 * This file centralizes all color definitions used throughout the application.
 * It provides a consistent color system that can be easily maintained and updated.
 */

// ============================================================================
// BRAND COLORS
// ============================================================================

export const brandColors = {
  primary: {
    DEFAULT: 'blue-900',
    foreground: 'white',
  },
  logo: {
    background: 'blue-900',
    icon: 'white',
    text: 'white',
  },
} as const;

// ============================================================================
// NAVIGATION COLORS
// ============================================================================

export const navigationColors = {
  background: 'slate-800',
  border: 'slate-700',
  text: {
    primary: 'white',
    secondary: 'slate-300',
  },
  profile: {
    background: 'slate-700',
    icon: 'white',
    text: 'white',
  },
} as const;

// ============================================================================
// SIDEBAR COLORS
// ============================================================================

export const sidebarColors = {
  background: 'slate-800',
  border: 'slate-600',
  logo: {
    background: 'blue-900',
    icon: 'white',
    text: 'white',
  },
  menu: {
    active: {
      background: 'slate-600',
      text: 'white',
    },
    inactive: {
      text: 'slate-300',
      hover: {
        background: 'slate-600',
        text: 'white',
      },
    },
  },
} as const;

// ============================================================================
// NODE TYPE COLORS
// ============================================================================

export const nodeTypeColors = {
  GridSource: {
    background: 'slate-100',
    border: 'slate-300',
    text: 'slate-800',
  },
  Transformer: {
    background: 'slate-200',
    border: 'slate-400',
    text: 'slate-800',
  },
  Breaker: {
    background: 'slate-300',
    border: 'slate-500',
    text: 'slate-800',
  },
  Busbar: {
    background: 'slate-400',
    border: 'slate-600',
    text: 'slate-100',
  },
  Motor: {
    background: 'slate-500',
    border: 'slate-700',
    text: 'slate-100',
  },
  RelayFunction: {
    background: 'slate-600',
    border: 'slate-800',
    text: 'slate-100',
  },
  Feeder: {
    background: 'slate-700',
    border: 'slate-900',
    text: 'slate-100',
  },
  CapacitorBank: {
    background: 'slate-800',
    border: 'slate-900',
    text: 'slate-100',
  },
  Battery: {
    background: 'slate-900',
    border: 'slate-900',
    text: 'slate-100',
  },
  Load: {
    background: 'slate-50',
    border: 'slate-200',
    text: 'slate-800',
  },
  CurrentTransformer: {
    background: 'slate-100',
    border: 'slate-300',
    text: 'slate-800',
  },
  Meter: {
    background: 'slate-200',
    border: 'slate-400',
    text: 'slate-800',
  },
  PotentialTransformer: {
    background: 'slate-100',
    border: 'slate-300',
    text: 'slate-800',
  },
  SurgeArrester: {
    background: 'slate-300',
    border: 'slate-500',
    text: 'slate-800',
  },
  VB1_vacuum: {
    background: 'slate-300',
    border: 'slate-500',
    text: 'slate-800',
  },
  // Default fallback
  default: {
    background: 'gray-100',
    border: 'gray-300',
    text: 'gray-800',
  },
} as const;

// ============================================================================
// EDGE TYPE COLORS
// ============================================================================

export const edgeTypeColors = {
  CONNECTS_TO: '#3b82f6', // blue-500
  PROTECTS: '#ef4444',    // red-500
  CONTROLS: '#10b981',    // emerald-500
  MONITORS: '#f59e0b',    // amber-500
  SUPPLIES: '#8b5cf6',    // violet-500
  default: '#6b7280',     // gray-500
} as const;

// ============================================================================
// FORM COLORS
// ============================================================================

export const formColors = {
  label: {
    text: 'gray-700',
  },
  select: {
    background: 'white',
    border: 'gray-300',
    text: 'gray-900',
  },
  placeholder: {
    text: 'gray-500',
  },
} as const;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get Tailwind CSS classes for a node type
 */
export const getNodeTypeClasses = (nodeType: string): string => {
  switch (nodeType) {
    case 'GridSource':
      return 'bg-slate-100 border-slate-300 text-slate-800';
    case 'Transformer':
      return 'bg-slate-200 border-slate-400 text-slate-800';
    case 'Breaker':
      return 'bg-slate-300 border-slate-500 text-slate-800';
    case 'Busbar':
      return 'bg-slate-400 border-slate-600 text-slate-100';
    case 'Motor':
      return 'bg-slate-500 border-slate-700 text-slate-100';
    case 'RelayFunction':
      return 'bg-slate-600 border-slate-800 text-slate-100';
    case 'Feeder':
      return 'bg-slate-700 border-slate-900 text-slate-100';
    case 'CapacitorBank':
      return 'bg-slate-800 border-slate-900 text-slate-100';
    case 'Battery':
      return 'bg-slate-900 border-slate-900 text-slate-100';
    case 'Load':
      return 'bg-slate-50 border-slate-200 text-slate-800';
    case 'CurrentTransformer':
      return 'bg-slate-100 border-slate-300 text-slate-800';
    case 'Meter':
      return 'bg-slate-200 border-slate-400 text-slate-800';
    case 'PotentialTransformer':
      return 'bg-slate-100 border-slate-300 text-slate-800';
    case 'SurgeArrester':
      return 'bg-slate-300 border-slate-500 text-slate-800';
    case 'VB1_vacuum':
      return 'bg-slate-300 border-slate-500 text-slate-800';
    default:
      return 'bg-gray-100 border-gray-300 text-gray-800';
  }
};

/**
 * Get color value for an edge type
 */
export const getEdgeTypeColor = (edgeType: string): string => {
  return edgeTypeColors[edgeType as keyof typeof edgeTypeColors] || edgeTypeColors.default;
};

/**
 * Get Tailwind CSS classes for navigation elements
 */
export const getNavigationClasses = {
  background: 'bg-slate-700',
  border: 'border-slate-600',
  text: 'text-white',
  profileBackground: 'bg-slate-600',
  profileIcon: 'text-white',
  profileText: 'text-white',
} as const;

/**
 * Get Tailwind CSS classes for sidebar elements
 */
export const getSidebarClasses = {
  background: 'bg-slate-700',
  border: 'border-slate-600',
  logoBackground: 'bg-blue-600',
  logoIcon: 'text-white',
  logoText: 'text-white',
  menuActive: 'bg-slate-600 text-white',
  menuInactive: 'text-slate-300 hover:bg-slate-600 hover:text-white',
} as const;

/**
 * Get Tailwind CSS classes for form elements
 */
export const getFormClasses = {
  label: 'text-gray-700',
  select: 'bg-white border-gray-300 text-gray-900',
} as const;
