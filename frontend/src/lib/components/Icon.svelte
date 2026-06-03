<script>
  // Lucide-Icons (exakt das Set aus components.jsx ICON_MAP).
  import {
    Inbox, LayoutDashboard, Wand2, ListFilter, Settings, Bug, Search, ScanText,
    CircleCheckBig, Zap, ThumbsUp, CircleAlert, Undo2, Pencil, RotateCcw, Ban,
    LayoutTemplate, Check, X, Plus, Trash2, GripVertical, ChevronDown, ChevronRight,
    Folder, FolderOpen, FileText, Menu, RefreshCw, RotateCw, Play, LoaderCircle,
    ArrowRight, TriangleAlert, Box, File, Eye, Database, HardDrive, Server, Cpu,
    FileCode2, FileSearch, CornerDownRight, Square,
  } from '@lucide/svelte';

  const MAP = {
    inbox: Inbox, 'layout-dashboard': LayoutDashboard, 'wand-2': Wand2, 'list-filter': ListFilter,
    settings: Settings, bug: Bug, search: Search, 'scan-text': ScanText, 'check-circle': CircleCheckBig,
    zap: Zap, 'thumbs-up': ThumbsUp, 'alert-circle': CircleAlert, undo: Undo2, pencil: Pencil,
    'rotate-ccw': RotateCcw, ban: Ban, 'layout-template': LayoutTemplate, check: Check, x: X, plus: Plus,
    trash: Trash2, 'grip-vertical': GripVertical, 'chevron-down': ChevronDown, 'chevron-right': ChevronRight,
    folder: Folder, 'folder-open': FolderOpen, 'file-text': FileText, menu: Menu, 'refresh-cw': RefreshCw,
    'rotate-cw': RotateCw, play: Play, loader: LoaderCircle, 'arrow-right': ArrowRight,
    'alert-triangle': TriangleAlert, box: Box, file: File, eye: Eye, database: Database,
    'hard-drive': HardDrive, server: Server, cpu: Cpu, 'file-code': FileCode2, 'file-search': FileSearch,
    'corner-down-right': CornerDownRight, square: Square,
  };

  let { name, size = 20, strokeWidth = 2, color, class: klass = '' } = $props();
  let Cmp = $derived(MAP[name] ?? Square);
</script>

<Cmp {size} {strokeWidth} color={color ?? 'currentColor'} class={klass} />
