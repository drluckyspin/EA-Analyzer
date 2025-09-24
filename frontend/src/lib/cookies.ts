/**
 * Utility functions for managing browser cookies
 */

export const setCookie = (name: string, value: string, days: number = 30): void => {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
};

export const getCookie = (name: string): string | null => {
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === " ") c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
};

export const deleteCookie = (name: string): void => {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
};

/**
 * Save node positions for a specific diagram
 */
export const saveNodePositions = (diagramId: string, positions: Record<string, { x: number; y: number }>): void => {
  const cookieName = `ea-analyzer-positions-${diagramId}`;
  setCookie(cookieName, JSON.stringify(positions), 365); // Save for 1 year
};

/**
 * Load node positions for a specific diagram
 */
export const loadNodePositions = (diagramId: string): Record<string, { x: number; y: number }> | null => {
  const cookieName = `ea-analyzer-positions-${diagramId}`;
  const positionsJson = getCookie(cookieName);
  
  if (!positionsJson) return null;
  
  try {
    return JSON.parse(positionsJson);
  } catch (error) {
    console.warn("Failed to parse saved node positions:", error);
    return null;
  }
};

/**
 * Clear saved positions for a specific diagram
 */
export const clearNodePositions = (diagramId: string): void => {
  const cookieName = `ea-analyzer-positions-${diagramId}`;
  deleteCookie(cookieName);
};
