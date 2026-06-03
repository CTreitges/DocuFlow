// Globaler UI-Zustand (Svelte-5-Runes): Routing, Sidebar, Toasts.

export const ui = $state({
  route: 'eingang',
  collapsed: false,
  toasts: [],
});

let counter = 0;

export function setRoute(route) {
  ui.route = route;
}

export function toggleSidebar() {
  ui.collapsed = !ui.collapsed;
}

// kind: 'success' | 'info' | 'error' | 'warning'
export function toast(kind, title, body) {
  // Nur den 'Demo-Daten'-Hinweis entduplizieren (mehrere Views feuern ihn beim
  // Offline-Start). Legitime Wiederholungen (z.B. 'Feld aktualisiert') bleiben.
  if (title === 'Demo-Daten' && ui.toasts.some((t) => t.title === 'Demo-Daten')) return;
  const id = ++counter;
  ui.toasts.push({ id, kind, title, body });
  const ttl = kind === 'error' || kind === 'warning' ? 5000 : 3000;
  setTimeout(() => dismiss(id), ttl);
}

export function dismiss(id) {
  const i = ui.toasts.findIndex((t) => t.id === id);
  if (i >= 0) ui.toasts.splice(i, 1);
}
