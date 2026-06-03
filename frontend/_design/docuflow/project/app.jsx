// ============================================================
// DocuFlow — App Shell (Header + Sidebar + Routing)
// ============================================================
function App() {
  const [route, setRoute] = useState('eingang');
  const [collapsed, setCollapsed] = useState(false);
  const { toasts, push, dismiss } = useToasts();

  // shared app state (so inbox actions reflect in dashboard counts)
  const [docs, setDocs] = useState(DOCUMENTS);
  const [log, setLog] = useState(ACTIVITY_LOG);

  const NAV = [
    { section: 'Verarbeitung', items: [
      { key: 'eingang', label: 'Eingang', icon: 'inbox' },
      { key: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
      { key: 'templates', label: 'Templates', icon: 'wand-2' },
    ] },
    { section: 'System', items: [
      { key: 'regeln', label: 'Sortier-Regeln', icon: 'list-filter' },
      { key: 'einstellungen', label: 'Einstellungen', icon: 'settings' },
      { key: 'ocr', label: 'OCR-Debug', icon: 'bug' },
    ] },
  ];

  const inboxCount = docs.filter((d) => d.status === 'neu').length;

  function screen() {
    switch (route) {
      case 'eingang': return <InboxScreen docs={docs} setDocs={setDocs} toast={push} />;
      case 'dashboard': return <DashboardScreen docs={docs} log={log} setLog={setLog} toast={push} />;
      case 'templates': return <TemplatesScreen toast={push} />;
      case 'regeln': return <RulesScreen toast={push} />;
      case 'einstellungen': return <SettingsScreen toast={push} />;
      case 'ocr': return <OcrDebugScreen toast={push} />;
      default: return null;
    }
  }

  return (
    <div className="flex flex-col h-full" style={{ background: C.page }}>
      {/* Header */}
      <header className="flex items-center justify-between px-3 shrink-0" style={{ height: 56, background: C.surface, borderBottom: `1px solid ${C.border}` }}>
        <div className="flex items-center gap-2">
          <button onClick={() => setCollapsed((c) => !c)} title="Sidebar ein-/ausklappen" className="p-2 rounded-lg hover:bg-white/5 transition-colors" style={{ color: C.textSecondary }}>
            <Icon name="menu" size={18} />
          </button>
          <div className="flex items-center gap-2 ml-1">
            <div className="flex items-center justify-center rounded-lg" style={{ width: 28, height: 28, background: rgba(C.accent, 0.15) }}>
              <Icon name="file-text" size={16} style={{ color: C.accent }} />
            </div>
            <span className="text-base font-semibold tracking-tight" style={{ color: C.textPrimary }}>DocuFlow</span>
          </div>
        </div>
        <span className="text-xs font-mono mr-2" style={{ color: C.textMuted }}>v0.1</span>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="shrink-0 flex flex-col py-3 transition-all duration-200" style={{ width: collapsed ? 60 : 220, background: C.surface, borderRight: `1px solid ${C.border}` }}>
          {NAV.map((group, gi) => (
            <div key={group.section} className={clsx(gi > 0 && 'mt-1')}>
              {gi > 0 && <div className="mx-3 my-2" style={{ borderTop: `1px solid ${C.border}` }} />}
              {!collapsed && (
                <div className="px-4 pt-1 pb-1.5 text-[10px] font-bold uppercase tracking-widest" style={{ color: C.textMuted }}>{group.section}</div>
              )}
              <nav className="px-2 flex flex-col gap-0.5">
                {group.items.map((item) => {
                  const on = route === item.key;
                  return (
                    <button
                      key={item.key}
                      onClick={() => setRoute(item.key)}
                      title={collapsed ? item.label : undefined}
                      className={clsx('flex items-center rounded-lg transition-colors w-full', collapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-3 py-2')}
                      style={{ background: on ? C.elevated : 'transparent', color: on ? C.accent : C.textSecondary }}
                      onMouseEnter={(e) => { if (!on) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
                      onMouseLeave={(e) => { if (!on) e.currentTarget.style.background = 'transparent'; }}
                    >
                      <Icon name={item.icon} size={20} className="shrink-0" strokeWidth={on ? 2.2 : 2} />
                      {!collapsed && <span className="text-sm font-medium flex-1 text-left">{item.label}</span>}
                      {!collapsed && item.key === 'eingang' && inboxCount > 0 && (
                        <span className="text-[10px] font-mono font-semibold rounded-full px-1.5 py-0.5" style={{ background: rgba(C.accent, 0.18), color: C.accent }}>{inboxCount}</span>
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          ))}
        </aside>

        {/* Content */}
        <main className="flex-1 min-w-0 overflow-auto" style={{ background: C.page }}>
          <div className="p-6" key={route}>
            {screen()}
          </div>
        </main>
      </div>

      <ToastHost toasts={toasts} onDismiss={dismiss} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
