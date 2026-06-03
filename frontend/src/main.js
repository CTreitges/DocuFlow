// IBM Plex (self-hosted, offline-tauglich) — die Gewichte, die das Design nutzt.
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-sans/700.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/600.css';

import './app.css';
import { mount } from 'svelte';
import App from './App.svelte';

const target = document.getElementById('app');
target.innerHTML = ''; // Boot-Platzhalter entfernen
const app = mount(App, { target });

export default app;
