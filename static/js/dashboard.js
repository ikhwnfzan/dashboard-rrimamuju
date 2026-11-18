let DATA = {};
const PAGE_STATE = {};
const DEFAULT_PAGE_SIZE = 10;

// Flat minimalist SVG icons (16x16, 1.8px stroke)
const FLAT_ICONS = {
  overview: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
  info_board: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>',
  data_pegawai: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  arsip_sdm: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>',
  dialog: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>',
  jadwal_siaran: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/><circle cx="12" cy="12" r="2"/><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/><path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/></svg>',
  program_siaran: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>',
  konten: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>',
  jadwal_tmb: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20h.01"/><path d="M7 20v-4"/><path d="M12 20v-8"/><path d="M17 20V8"/><path d="M22 4v16"/></svg>',
  master_barang: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
  master_persediaan: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>',
  persediaan_masuk: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>',
  persediaan_keluar: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>',
  master_ruangan: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>',
  bmn_area: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
  manage_users: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>',
  manage_modules: '<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  sun: '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>',
  moon: '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>'
};

const MODULE_NAV_CONFIG = [
  { key: 'overview', label: 'Overview', group: 'Utama', always: true },
  { key: 'info_board', label: 'Info Board', group: 'Utama' },
  { key: 'data_pegawai', label: 'Data Pegawai', group: 'SDM' },
  { key: 'arsip_sdm', label: 'Arsip SDM', group: 'SDM' },
  { key: 'dialog', label: 'Dialog', group: 'Siaran & Perencanaan' },
  { key: 'jadwal_siaran', label: 'Jadwal Siaran', group: 'Siaran & Perencanaan' },
  { key: 'program_siaran', label: 'Program Siaran', group: 'Siaran & Perencanaan' },
  { key: 'konten', label: 'Content Planner', group: 'KMB' },
  { key: 'jadwal_tmb', label: 'Jadwal TMB', group: 'TMB' },
  { key: 'master_barang', label: 'Master Barang', group: 'BMN' },
  { key: 'master_persediaan', label: 'Master Persediaan', group: 'BMN' },
  { key: 'persediaan_masuk', label: 'Persediaan Masuk', group: 'BMN' },
  { key: 'persediaan_keluar', label: 'Persediaan Keluar', group: 'BMN' },
  { key: 'master_ruangan', label: 'Master Ruangan', group: 'BMN' },
  { key: 'bmn_area', label: 'BMN AREA', group: 'BMN' },
  { key: 'manage_users', label: 'Manage User', group: 'Admin' },
  { key: 'manage_modules', label: 'Manage Module', group: 'Admin' },
];

// =========================================================
// TOAST NOTIFICATION SYSTEM
// =========================================================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const isErr = type === 'error';
  const toast = document.createElement('div');
  toast.className = `pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl shadow-xl border text-xs font-semibold transition-all duration-300 transform translate-y-2 opacity-0 ${
    isErr
      ? 'bg-rose-50 dark:bg-rose-950/95 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200'
      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100'
  }`;

  const iconSvg = isErr
    ? '<svg class="w-4 h-4 text-rose-600 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>'
    : '<svg class="w-4 h-4 text-teal-600 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

  toast.innerHTML = `
    ${iconSvg}
    <div class="flex-1 leading-snug">${message}</div>
    <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">✕</button>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =========================================================
// REUSABLE TABLE PAGINATION HELPER
// =========================================================
function paginateArray(tableKey, rows, pagContainerId, rerenderFnName) {
  if (!PAGE_STATE[tableKey]) {
    PAGE_STATE[tableKey] = { page: 1, size: DEFAULT_PAGE_SIZE };
  }
  const st = PAGE_STATE[tableKey];
  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / st.size));
  if (st.page > totalPages) st.page = totalPages;
  if (st.page < 1) st.page = 1;

  const startIdx = (st.page - 1) * st.size;
  const pageSlice = rows.slice(startIdx, startIdx + st.size);

  const box = document.getElementById(pagContainerId);
  if (box) {
    const fromNum = total === 0 ? 0 : startIdx + 1;
    const toNum = Math.min(startIdx + st.size, total);
    box.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
        <div class="flex items-center gap-2">
          <span>Menampilkan <strong>${fromNum}–${toNum}</strong> dari <strong>${total}</strong> data</span>
          <select onchange="changePageSize('${tableKey}', this.value, ${rerenderFnName})"
            class="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
            ${[10, 25, 50, 100].map(sz => `<option value="${sz}" ${st.size === sz ? 'selected' : ''}>${sz} / hal</option>`).join('')}
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <button onclick="setTablePage('${tableKey}', ${st.page - 1}, ${rerenderFnName})" ${st.page <= 1 ? 'disabled' : ''}
            class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 font-bold disabled:opacity-40 hover:bg-slate-200 dark:hover:bg-slate-800 transition">
            ← Prev
          </button>
          <span class="px-2 font-bold text-slate-700 dark:text-slate-200">Hal ${st.page} / ${totalPages}</span>
          <button onclick="setTablePage('${tableKey}', ${st.page + 1}, ${rerenderFnName})" ${st.page >= totalPages ? 'disabled' : ''}
            class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 font-bold disabled:opacity-40 hover:bg-slate-200 dark:hover:bg-slate-800 transition">
            Next →
          </button>
        </div>
      </div>
    `;
  }
  return pageSlice;
}

function setTablePage(tableKey, newPage, fn) {
  PAGE_STATE[tableKey] = PAGE_STATE[tableKey] || { page: 1, size: DEFAULT_PAGE_SIZE };
  PAGE_STATE[tableKey].page = newPage;
  if (typeof fn === 'function') fn();
}

function changePageSize(tableKey, newSize, fn) {
  PAGE_STATE[tableKey] = { page: 1, size: Number(newSize) || DEFAULT_PAGE_SIZE };
  if (typeof fn === 'function') fn();
}

// =========================================================
// PERMISSIONS & THEME
// =========================================================
function permLevel(modKey) {
  if ((USER.roles || []).some(r => r.toLowerCase() === 'admin')) return 'full';
  return (DATA.user?.permissions || USER.permissions || {})[modKey] || 'none';
}

function canView(modKey) {
  return ['view', 'update', 'full'].includes(permLevel(modKey));
}

function canUpdate(modKey) {
  return ['update', 'full'].includes(permLevel(modKey));
}

function canFull(modKey) {
  return permLevel(modKey) === 'full';
}

function initTheme() {
  applyTheme(localStorage.getItem('rri_theme') || 'light');
}
function applyTheme(mode) {
  document.documentElement.classList.toggle('dark', mode === 'dark');
  document.getElementById('themeIcon').innerHTML = mode === 'dark' ? FLAT_ICONS.sun : FLAT_ICONS.moon;
  document.getElementById('themeLabel').textContent = mode === 'dark' ? 'Light' : 'Dark';
  localStorage.setItem('rri_theme', mode);
}
function toggleTheme() {
  applyTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark');
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('-translate-x-full');
}

function openUserProfile() {
  const menu = document.getElementById('userMenu');
  if (menu) menu.classList.add('hidden');
  switchModule('user_profile');
}

async function loadDashboard() {
  const res = await fetch('/api/board');
  DATA = await res.json();
  buildRoleSidebar();
  populateNipDatalist();
  applyActionButtonVisibility();
  renderAllModules();
}

function populateNipDatalist() {
  const dl = document.getElementById('pegawaiNipDatalist');
  if (dl) {
    dl.innerHTML = (DATA.employees || []).map(e =>
      `<option value="${e['NIP / NIPPK'] || e.nip_clean}">${e['Nama Pegawai']} — ${e.Posisi || e.Jabatan || ''}</option>`
    ).join('');
  }
}

function buildRoleSidebar() {
  const visibleItems = MODULE_NAV_CONFIG.filter(item => item.always || canView(item.key));
  document.getElementById('statAccessibleMods').textContent = visibleItems.length - 1;

  const groups = {};
  visibleItems.forEach(item => {
    groups[item.group] = groups[item.group] || [];
    groups[item.group].push(item);
  });

  document.getElementById('dynamicSidebarMenu').innerHTML = Object.entries(groups).map(([grp, items]) => `
    <div class="space-y-1">
      <p class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">${grp}</p>
      ${items.map(i => `
        <button onclick="switchModule('${i.key}')" data-mod="${i.key}"
          class="nav-pill ${i.key === 'overview' ? 'active' : ''} w-full flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800/70 transition">
          <span class="flex items-center gap-2.5 truncate">${FLAT_ICONS[i.key] || ''}<span class="truncate">${i.label}</span></span>
        </button>
      `).join('')}
    </div>
  `).join('');
}

function renderUserProfilePermissions() {
  const box = document.getElementById('profilePermissionsGrid');
  if (!box) return;
  const mods = MODULE_NAV_CONFIG.filter(m => !m.always);
  box.innerHTML = mods.map(m => {
    const lvl = permLevel(m.key);
    const badgeClass = lvl === 'full'
      ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
      : lvl === 'update'
        ? 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
        : lvl === 'view'
          ? 'bg-sky-50 dark:bg-sky-950 text-sky-700 dark:text-sky-300'
          : 'bg-slate-100 dark:bg-slate-800 text-slate-400';

    return `
      <div class="flex items-center justify-between p-3 rounded-2xl border border-slate-200/70 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 text-xs">
        <span class="font-bold truncate pr-2">${m.label}</span>
        <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${badgeClass}">${lvl}</span>
      </div>
    `;
  }).join('');
}

function applyActionButtonVisibility() {
  const toggle = (id, show) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden', !show);
  };
  toggle('btnAddInfoOverview', canFull('info_board'));
  toggle('btnAddInfoBoard', canFull('info_board'));
  toggle('btnAddPegawai', canFull('data_pegawai'));
  toggle('btnAddArsipSdm', canFull('arsip_sdm'));
  toggle('btnAddDialog', canFull('dialog'));
  toggle('btnAddSiaran', canFull('jadwal_siaran'));
  toggle('btnAddProgramSiaran', canFull('program_siaran'));
  toggle('btnAddKonten', canFull('konten'));
  toggle('btnAddTmb', canFull('jadwal_tmb'));
  toggle('btnAddBarang', canFull('master_barang'));
  toggle('btnAddPersediaan', canFull('master_persediaan'));
  toggle('btnAddStokMasuk', canFull('persediaan_masuk'));
  toggle('btnAddStokKeluar', canFull('persediaan_keluar'));
  toggle('btnAddRuangan', canFull('master_ruangan'));
}

function switchModule(modKey) {
  // Top header title always displays "Dashboard Pegawai"; each section displays its true module title
  document.querySelectorAll('.nav-pill').forEach(b => b.classList.toggle('active', b.dataset.mod === modKey));
  document.querySelectorAll('.mod-section').forEach(s => s.classList.add('hidden'));
  const target = document.getElementById(`mod-${modKey}`);
  if (target) target.classList.remove('hidden');
  if (window.innerWidth < 1024) document.getElementById('sidebar').classList.add('-translate-x-full');
}

function renderAllModules() {
  document.getElementById('syncStatusLabel').textContent = DATA.status_msg || '-';
  document.getElementById('syncTimeLabel').textContent = DATA.server_time || '';
  document.getElementById('statInfoCount').textContent = (DATA.info_board || []).length;

  renderInfoBoard();
  if (canView('data_pegawai')) renderDataPegawai();
  if (canView('arsip_sdm')) renderArsipSdm();
  if (canView('dialog')) renderDialogModule();
  if (canView('jadwal_siaran')) renderJadwalSiaran();
  if (canView('program_siaran')) renderProgramSiaran();
  if (canView('konten')) renderKonten();
  if (canView('jadwal_tmb')) renderJadwalTmb();
  if (canView('master_barang')) renderMasterBarang();
  if (canView('master_persediaan')) renderMasterPersediaan();
  if (canView('persediaan_masuk')) renderPersediaanMasuk();
  if (canView('persediaan_keluar')) renderPersediaanKeluar();
  if (canView('master_ruangan')) renderMasterRuangan();
  if (canFull('manage_users')) renderManageUsers();
  if (canFull('manage_modules')) renderManageModules();
}

// =========================================================
// DELETE RECORD WITH TOAST FEEDBACK
// =========================================================
async function deleteRecord(targetKey, rowNum, label = 'data ini') {
  if (!rowNum) {
    showToast('Nomor baris tidak ditemukan.', 'error');
    return;
  }
  if (!confirm(`Hapus ${label}?`)) return;

  const res = await fetch(`/api/delete/${targetKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_num: rowNum })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) await loadDashboard();
}

// =========================================================
// MODULE RENDERERS (ALL TABLES PAGINATED)
// =========================================================
function renderInfoBoard() {
  const deletable = canFull('info_board');
  const cards = (DATA.info_board || []).map(i => `
    <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700 space-y-1.5">
      <div class="flex items-center justify-between text-[11px]">
        <span class="font-extrabold px-2 py-0.5 rounded-full ${String(i.Prioritas).toLowerCase() === 'urgent' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300' : 'bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300'}">${i.Prioritas || 'Info'}</span>
        <div class="flex items-center gap-2">
          <span class="text-slate-400">${i.Tanggal || ''} • ${i.Target_Divisi || 'Semua'}</span>
          ${deletable && i._row_num ? `<button onclick="deleteRecord('Info_Board', ${i._row_num}, '${(i.Judul || '').replace(/'/g, '')}')" class="text-rose-500 hover:underline font-bold">Hapus</button>` : ''}
        </div>
      </div>
      <h4 class="font-extrabold text-sm">${i.Judul || ''}</h4>
      <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">${i.Isi || ''}</p>
    </div>
  `).join('') || `<p class="text-xs text-slate-400">Belum ada pengumuman di Info Board.</p>`;

  document.getElementById('overviewInfoList').innerHTML = cards;
  document.getElementById('fullInfoBoardList').innerHTML = cards;
}

function renderDataPegawai() {
  const q = (document.getElementById('searchPegawai')?.value || '').toLowerCase();
  const editable = canUpdate('data_pegawai');
  const deletable = canFull('data_pegawai');
  const filtered = (DATA.employees || []).filter(e => Object.values(e).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('pegawai', filtered, 'pagPegawai', 'renderDataPegawai');

  document.getElementById('tbodyPegawai').innerHTML = rows.map(e => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 text-slate-400">${e.No || '-'}</td>
      <td class="py-3 px-3 font-extrabold">${e['Nama Pegawai'] || '-'}</td>
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${e['NIP / NIPPK'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${e['Pangkat/ Golongan'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${e.Jabatan || '-'}</td>
      <td class="py-3 px-3 text-xs font-semibold">${e.Posisi || '-'}</td>
      <td class="py-3 px-3">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${String(e.Status || 'Aktif').toLowerCase() === 'aktif' ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-600' : 'bg-amber-50 dark:bg-amber-950 text-amber-600'}">
          ${e.Status || 'Aktif'}
        </span>
      </td>
      <td class="py-3 px-3 text-right whitespace-nowrap space-x-1">
        ${editable ? `<button onclick='openEmpEdit(${JSON.stringify(e)})' class="text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-teal-600 dark:hover:text-white transition">Edit</button>` : ''}
        ${deletable && e._row_num ? `<button onclick="deleteRecord('DB_Pegawai', ${e._row_num}, '${(e['Nama Pegawai'] || '').replace(/'/g, '')}')" class="text-xs font-bold px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 hover:bg-rose-100 transition">Hapus</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function openEmpEdit(emp) {
  document.getElementById('editEmpRowNum').value = emp._row_num || '';
  document.getElementById('editEmpNo').value = emp.No || '';
  document.getElementById('editEmpNip').value = emp['NIP / NIPPK'] || '';
  document.getElementById('editEmpNama').value = emp['Nama Pegawai'] || '';
  document.getElementById('editEmpPangkat').value = emp['Pangkat/ Golongan'] || '';
  document.getElementById('editEmpJabatan').value = emp.Jabatan || '';
  document.getElementById('editEmpPosisi').value = emp.Posisi || '';
  document.getElementById('editEmpStatus').value = emp.Status || 'Aktif';
  const m = document.getElementById('empEditModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeEmpEditModal() {
  const m = document.getElementById('empEditModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}
async function submitEmpUpdate(e) {
  e.preventDefault();
  const row_num = document.getElementById('editEmpRowNum').value;
  const updates = {
    'No': document.getElementById('editEmpNo').value,
    'NIP / NIPPK': document.getElementById('editEmpNip').value,
    'Nama Pegawai': document.getElementById('editEmpNama').value,
    'Pangkat/ Golongan': document.getElementById('editEmpPangkat').value,
    'Jabatan': document.getElementById('editEmpJabatan').value,
    'Posisi': document.getElementById('editEmpPosisi').value,
    'Status': document.getElementById('editEmpStatus').value,
  };
  const res = await fetch('/api/employees/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_num, updates })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeEmpEditModal();
    await loadDashboard();
  }
}

function renderArsipSdm() {
  const q = (document.getElementById('searchArsipSdm')?.value || '').toLowerCase();
  const filtered = (DATA.arsip_sdm || []).filter(a => Object.values(a).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('arsip_sdm', filtered, 'pagArsipSdm', 'renderArsipSdm');
  document.getElementById('tbodyArsipSdm').innerHTML = rows.map(a => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs font-bold">${a['Nomor Dokumen'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${a['Nama Dokumen'] || '-'}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${a.Tanggal || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-semibold">${a.Jenis || '-'}</span></td>
      <td class="py-3 px-3">${a.Link ? `<a href="${a.Link}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Buka ↗</a>` : '-'}</td>
    </tr>
  `).join('');
}

function renderDialogModule() {
  const q = (document.getElementById('searchDialog')?.value || '').toLowerCase();
  const editable = canUpdate('dialog');
  const filtered = (DATA.dialogs || []).filter(d => Object.values(d).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('dialog', filtered, 'pagDialog', 'renderDialogModule');
  document.getElementById('tbodyDialog').innerHTML = rows.map(d => {
    const topik = d['Topik/ Isu'] || d['Topik'] || '-';
    const bestcut = d.Bestcut || '';
    const bestcutCell = bestcut.startsWith('http')
      ? `<a href="${bestcut}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Bestcut ↗</a>`
      : `<span class="text-xs text-slate-400">${bestcut || '-'}</span>`;

    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3 text-xs font-bold whitespace-nowrap">${d.Tanggal || '-'}</td>
        <td class="py-3 px-3 text-xs font-bold text-sky-600">${d.Program || '-'}</td>
        <td class="py-3 px-3 text-xs font-semibold max-w-xs">${topik}</td>
        <td class="py-3 px-3 text-xs">${d.Narasumber || '-'}</td>
        <td class="py-3 px-3 text-xs">${d['KET. Kehadiran'] || '-'}</td>
        <td class="py-3 px-3 text-xs font-bold">${d['Keterlaksanaan'] || '-'}</td>
        <td class="py-3 px-3 whitespace-nowrap">${bestcutCell}</td>
        <td class="py-3 px-3">
          ${editable && d._row_num ? `<button onclick='openDialogEdit(${JSON.stringify(d)})' class="text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-teal-600 dark:hover:text-white transition">Update</button>` : '-'}
        </td>
      </tr>
    `;
  }).join('');
}

function renderJadwalSiaran() {
  const rows = paginateArray('siaran', DATA.siaran || [], 'pagSiaran', 'renderJadwalSiaran');
  document.getElementById('tbodySiaran').innerHTML = rows.map(s => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-bold">${s.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-xs">${s.Shift || '-'}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${s.Programa || '-'}</td>
      <td class="py-3 px-3 font-semibold">${s.Penyiar || '-'}</td>
      <td class="py-3 px-3">${s.Operator || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600">${s.Status || '-'}</span></td>
    </tr>
  `).join('');
}

function renderProgramSiaran() {
  const rows = paginateArray('program_siaran', DATA.program_siaran || [], 'pagProgramSiaran', 'renderProgramSiaran');
  document.getElementById('tbodyProgramSiaran').innerHTML = rows.map(p => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${p['Kode Program'] || '-'}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${p.Programa || '-'}</td>
      <td class="py-3 px-3 font-extrabold">${p['Nama Program'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Hari || '-'}</td>
      <td class="py-3 px-3 text-xs font-semibold">${p.Jam || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Format || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Produser || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600">${p.Status || 'Aktif'}</span></td>
    </tr>
  `).join('');
}

function renderKonten() {
  document.getElementById('gridKonten').innerHTML = (DATA.content_planner || []).map(p => `
    <div class="bg-white dark:bg-[#111827] rounded-3xl border border-slate-200/80 dark:border-slate-800 p-5 space-y-2 hover:bg-slate-200/40 dark:hover:bg-slate-800/40 transition">
      <div class="flex justify-between text-xs font-bold">
        <span class="text-teal-600">${p.Akun || p.Platform}</span>
        <span class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800">${p.Status || '-'}</span>
      </div>
      <h4 class="font-extrabold text-sm">${p.Judul_Konten || '-'}</h4>
      <p class="text-xs text-slate-400">${p.Tanggal_Tayang || ''} • ${p.Jenis || ''} • PIC: ${p.PIC || '-'}</p>
      ${p.Link_Asset ? `<a href="${p.Link_Asset}" target="_blank" class="inline-block text-xs font-bold text-sky-600 hover:underline pt-1">Lihat Asset ↗</a>` : ''}
    </div>
  `).join('');
}

function renderJadwalTmb() {
  const rows = paginateArray('jadwal_tmb', DATA.jadwal_tmb || [], 'pagTmb', 'renderJadwalTmb');
  document.getElementById('tbodyTmb').innerHTML = rows.map(t => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-bold">${t.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-xs">${t.Shift || '-'}</td>
      <td class="py-3 px-3 font-bold text-indigo-600">${t.Lokasi_Pemancar || '-'}</td>
      <td class="py-3 px-3 font-semibold">${t.Teknisi_TMB || '-'}</td>
      <td class="py-3 px-3 text-xs">${t.Tugas || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600">${t.Status || '-'}</span></td>
    </tr>
  `).join('');
}

function renderMasterBarang() {
  const q = (document.getElementById('searchBarang')?.value || '').toLowerCase();
  const filtered = (DATA.assets || []).filter(a => Object.values(a).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('barang', filtered, 'pagBarang', 'renderMasterBarang');
  document.getElementById('tbodyBarang').innerHTML = rows.map(a => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-bold">${a['Kode Ruang'] || '-'} <span class="block text-[10px] text-slate-400">${a['Nama Ruangan'] || ''}</span></td>
      <td class="py-3 px-3 font-mono text-slate-500">${a['Nomor Kode Barang'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${a['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3">${a['Merk/ Model'] || '-'}</td>
      <td class="py-3 px-3">${a.Tahun || '-'}</td>
      <td class="py-3 px-3 font-bold">${a.NUP || '-'}</td>
      <td class="py-3 px-3 font-bold ${String(a.Kondisi).toLowerCase() === 'baik' ? 'text-emerald-600' : 'text-rose-500'}">${a.Kondisi || '-'}</td>
      <td class="py-3 px-3 text-amber-600">${a['Tindak Lanjut'] || '-'}</td>
    </tr>
  `).join('');
}

function renderMasterPersediaan() {
  const rows = paginateArray('persediaan', DATA.stock_master || [], 'pagPersediaan', 'renderMasterPersediaan');
  document.getElementById('tbodyPersediaan').innerHTML = rows.map(s => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-400">${s['Kode Barang'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${s['Nama Barang']}</td>
      <td class="py-3 px-3 text-slate-400">${s.Unit || '-'}</td>
      <td class="py-3 px-3 text-right">${s['Stok Awal']}</td>
      <td class="py-3 px-3 text-right text-emerald-600 font-bold">+${s['Barang Masuk']}</td>
      <td class="py-3 px-3 text-right text-amber-600 font-bold">-${s['Barang Keluar']}</td>
      <td class="py-3 px-3 text-right font-extrabold">${s['Stok Akhir']}</td>
    </tr>
  `).join('');
}

function renderPersediaanMasuk() {
  const q = (document.getElementById('searchStokIn')?.value || '').toLowerCase();
  const filtered = (DATA.stock_in || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('stok_in', filtered, 'pagStokIn', 'renderPersediaanMasuk');
  document.getElementById('tbodyStokIn').innerHTML = rows.map(r => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 whitespace-nowrap">${r.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-slate-500">${r['Penanggung Jawab'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${r['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3 text-right font-bold text-emerald-600">+${r['Jumlah Masuk'] || 0}</td>
      <td class="py-3 px-3">${r.Unit || '-'}</td>
      <td class="py-3 px-3 text-right font-bold">${r.Pcs || r['Jumlah Masuk'] || 0}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${r.Keterangan || '-'}</td>
    </tr>
  `).join('');
}

function renderPersediaanKeluar() {
  const q = (document.getElementById('searchStokOut')?.value || '').toLowerCase();
  const filtered = (DATA.stock_out || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('stok_out', filtered, 'pagStokOut', 'renderPersediaanKeluar');
  document.getElementById('tbodyStokOut').innerHTML = rows.map(r => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 whitespace-nowrap">${r.Tanggal || '-'}</td>
      <td class="py-3 px-3 font-bold">${r['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3 text-slate-500">${r.Bidang || '-'}</td>
      <td class="py-3 px-3 font-semibold">${r['Penerima Barang'] || '-'}</td>
      <td class="py-3 px-3 text-right font-bold text-amber-600">-${r['Jumlah Keluar'] || 0}</td>
      <td class="py-3 px-3">${r.Unit || '-'}</td>
      <td class="py-3 px-3 text-right font-bold">${r.Pcs || r['Jumlah Keluar'] || 0}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${r.Keterangan || '-'}</td>
    </tr>
  `).join('');
}

// BMN: MASTER RUANGAN AS PAGINATED TABLE WITH NIP/NIPPPK LOOKUP
function renderMasterRuangan() {
  const q = (document.getElementById('searchRuangan')?.value || '').toLowerCase();
  const deletable = canFull('master_ruangan');
  const employeesByNip = new Map((DATA.employees || []).map(e => [
    String(e['NIP / NIPPK'] || '').replace(/\D/g, ''), e
  ]).filter(([nip]) => nip));
  const filtered = (DATA.rooms || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('ruangan', filtered, 'pagRuangan', 'renderMasterRuangan');

  document.getElementById('tbodyRuangan').innerHTML = rows.map(r => {
    const nip = String(r.pj_nip || r['Penanggungjawab Ruangan'] || '').replace(/\D/g, '');
    const employee = employeesByNip.get(nip);
    const rowNum = r._row_num ?? r.row_num ?? ((DATA.rooms || []).indexOf(r) + 2);
    return `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3">
        <span class="px-2.5 py-0.5 rounded-lg bg-slate-900 dark:bg-slate-700 text-white text-xs font-extrabold">${r['Nomor Ruangan'] || '-'}</span>
      </td>
      <td class="py-3 px-3 font-extrabold">${r['Nama Ruangan'] || '-'}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${r.Lokasi || '-'}</td>
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${r['Penanggungjawab Ruangan'] || '-'}</td>
      <td class="py-3 px-3 font-bold text-teal-700 dark:text-teal-300">${employee?.['Nama Pegawai'] || r.pj_nama || r.Nama || '-'}</td>
      <td class="py-3 px-3 text-xs font-semibold">${employee?.Posisi || '-'}</td>
      <td class="py-3 px-3 text-right">
        ${deletable && rowNum > 1 ? `<button onclick="deleteRecord('DB_Ruangan', ${rowNum}, '${(r['Nama Ruangan'] || '').replace(/'/g, '')}')" class="text-xs font-bold px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 hover:bg-rose-100 transition">Hapus</button>` : '-'}
      </td>
    </tr>
  `;
  }).join('');
}

// Admin: Manage Users & Module Matrix
function renderManageUsers() {
  const rows = paginateArray('users', DATA.users_list || [], 'pagUsers', 'renderManageUsers');
  document.getElementById('tbodyUsers').innerHTML = rows.map(u => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs font-bold">${u.NIP}</td>
      <td class="py-3 px-3 font-extrabold">${u.Nama}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${u.Posisi}</td>
      <td class="py-3 px-3">
        <div class="flex flex-wrap gap-1">
          ${(u.roles_list || []).map(r => `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300">${r}</span>`).join('')}
        </div>
      </td>
      <td class="py-3 px-3 text-right">
        <button onclick='openUserModal(${JSON.stringify(u)})' class="text-xs font-bold px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-teal-600 dark:hover:text-white transition">
          Edit Roles / Pass
        </button>
      </td>
    </tr>
  `).join('');
}

function openUserModal(existingUser = null) {
  document.getElementById('usrNip').value = existingUser ? existingUser.nip_clean : '';
  document.getElementById('usrPassword').value = '';
  const activeRoles = existingUser ? (existingUser.roles_list || []) : [];

  document.getElementById('roleCheckboxes').innerHTML = (DATA.all_roles || []).map(r => `
    <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
      <input type="checkbox" name="roleChk" value="${r}" ${activeRoles.includes(r) ? 'checked' : ''} class="rounded text-teal-600" />
      <span>${r}</span>
    </label>
  `).join('');

  const m = document.getElementById('userModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}

function closeUserModal() {
  const m = document.getElementById('userModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}

async function submitUserForm(e) {
  e.preventDefault();
  const nip = document.getElementById('usrNip').value;
  const password = document.getElementById('usrPassword').value;
  const roles = Array.from(document.querySelectorAll('input[name="roleChk"]:checked')).map(c => c.value);

  const res = await fetch('/api/admin/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nip, password, roles })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeUserModal();
    await loadDashboard();
  }
}

function renderManageModules() {
  const roles = (DATA.all_roles || []).filter(r => r !== 'Admin');
  const modules = (DATA.all_modules || []).filter(m => !['manage_users', 'manage_modules'].includes(m.key));
  const matrix = DATA.role_matrix || {};

  document.getElementById('matrixHeaderRow').innerHTML =
    `<th class="py-3 px-3 sticky left-0 bg-slate-50 dark:bg-slate-800">Role</th>` +
    modules.map(m => `<th class="py-3 px-2 whitespace-nowrap">${m.label}</th>`).join('');

  document.getElementById('matrixBodyRows').innerHTML = roles.map(role => `
    <tr class="hover:bg-slate-200/50 dark:hover:bg-slate-800/40 transition">
      <td class="py-2.5 px-3 font-extrabold whitespace-nowrap sticky left-0 bg-white dark:bg-[#111827]">${role}</td>
      ${modules.map(m => {
        const cur = (matrix[role] || {})[m.key] || 'none';
        return `
          <td class="py-2 px-2">
            <select onchange="updateRoleModule('${role}', '${m.key}', this.value)"
              class="text-[11px] font-bold px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition">
              <option value="none" ${cur === 'none' ? 'selected' : ''}>None</option>
              <option value="view" ${cur === 'view' ? 'selected' : ''}>View</option>
              <option value="update" ${cur === 'update' ? 'selected' : ''}>Update</option>
              <option value="full" ${cur === 'full' ? 'selected' : ''}>Full</option>
            </select>
          </td>
        `;
      }).join('')}
    </tr>
  `).join('');
}

async function updateRoleModule(role, module_key, level) {
  const res = await fetch('/api/admin/role-modules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, module_key, level })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
}

// Dialog Update (with Bestcut)
function openDialogEdit(rowObj) {
  document.getElementById('editDialogRowNum').value = rowObj._row_num;
  document.getElementById('editDialogTopik').value = rowObj['Topik/ Isu'] || rowObj['Topik'] || '';
  document.getElementById('editDialogNarasumber').value = rowObj['Narasumber'] || '';
  document.getElementById('editDialogKehadiran').value = rowObj['KET. Kehadiran'] || '';
  document.getElementById('editDialogStatus').value = rowObj['Keterlaksanaan'] || '';
  document.getElementById('editDialogFlyer').value = rowObj['Flyer'] || '';
  document.getElementById('editDialogBestcut').value = rowObj['Bestcut'] || '';
  const m = document.getElementById('dialogEditModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeDialogEditModal() {
  const m = document.getElementById('dialogEditModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}
async function submitDialogUpdate(e) {
  e.preventDefault();
  const row_num = document.getElementById('editDialogRowNum').value;
  const updates = {
    'Topik/ Isu': document.getElementById('editDialogTopik').value,
    'Narasumber': document.getElementById('editDialogNarasumber').value,
    'KET. Kehadiran': document.getElementById('editDialogKehadiran').value,
    'Keterlaksanaan': document.getElementById('editDialogStatus').value,
    'Flyer': document.getElementById('editDialogFlyer').value,
    'Bestcut': document.getElementById('editDialogBestcut').value,
  };
  const res = await fetch('/api/dialog/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_num, updates })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeDialogEditModal();
    await loadDashboard();
  }
}

// Generic Add Modal (with NIP/NIPPPK auto-lookup for Penanggung Jawab Ruangan)
const SCHEMAS = {
  Info_Board: { title: 'Posting Info Board', fields: ['Tanggal', 'Prioritas', 'Judul', 'Isi', 'Target_Divisi', 'Lampiran'] },
  DB_Pegawai: { title: 'Tambah Data Pegawai', fields: ['No', 'Nama Pegawai', 'NIP / NIPPK', 'Pangkat/ Golongan', 'Jabatan', 'Status', 'Posisi'] },
  Arsip_SDM: { title: 'Tambah Arsip SDM', fields: ['Nomor Dokumen', 'Nama Dokumen', 'Tanggal', 'Jenis', 'Link'] },
  Agenda_Setting: { title: 'Tambah Agenda Dialog', fields: ['Tanggal', 'Program', 'Topik/ Isu', 'Narasumber', 'Jabatan/ Instansi', 'KET. Kehadiran', 'PIC Narasumber', 'Flyer', 'Bestcut', 'Keterlaksanaan', 'Kendala'] },
  Siaran: { title: 'Tambah Jadwal Siaran', fields: ['Tanggal', 'Shift', 'Programa', 'Penyiar', 'Operator', 'Status'] },
  DB_Program: { title: 'Tambah Program Siaran', fields: ['Kode Program', 'Programa', 'Nama Program', 'Hari', 'Jam', 'Format', 'Produser', 'Status'] },
  Planner: { title: 'Tambah Konten (Planner)', fields: ['Tanggal_Tayang', 'Platform', 'Akun', 'Judul_Konten', 'Jenis', 'Divisi', 'PIC', 'Status', 'Link_Asset'] },
  Jadwal_TMB: { title: 'Tambah Jadwal TMB', fields: ['Tanggal', 'Shift', 'Lokasi_Pemancar', 'Teknisi_TMB', 'Tugas', 'Status'] },
  DB_Aset: { title: 'Tambah Master Barang', fields: ['Kode Ruang', 'Nomor Kode Barang', 'Nama Barang', 'Merk/ Model', 'Tahun', 'NUP', 'Kondisi', 'Tindak Lanjut', 'Keterangan'] },
  DB_Ruangan: { title: 'Tambah Master Ruangan', fields: ['Nomor Ruangan', 'Nama Ruangan', 'Lokasi', 'Penanggungjawab Ruangan', 'Nama', 'Jabatan'] },
  DB_Stok_Master: { title: 'Tambah Master Persediaan', fields: ['Kode Barang', 'Nama Barang', 'Unit', 'Stok Awal', 'Keterangan'] },
  DB_Stok_Masuk: { title: 'Catat Persediaan Masuk', fields: ['Tanggal', 'Penanggung Jawab', 'Nama Barang', 'Jumlah Masuk', 'Unit', 'Pcs', 'Keterangan'] },
  DB_Stok_Keluar: { title: 'Catat Persediaan Keluar', fields: ['Tanggal', 'Nama Barang', 'Bidang', 'Penerima Barang', 'Jumlah Keluar', 'Unit', 'Pcs', 'Keterangan'] },
};

function handleRoomNipLookup(nipInputEl) {
  const clean = String(nipInputEl.value || '').replace(/NIPPPK\.|NIP\.|\s+/g, '');
  if (!clean) return;
  const emp = (DATA.employees || []).find(e => e.nip_clean === clean);
  if (emp) {
    const form = nipInputEl.closest('form');
    const namaInput = form.querySelector('input[name="Nama"]');
    const jabInput = form.querySelector('input[name="Jabatan"]');
    if (namaInput) namaInput.value = emp['Nama Pegawai'] || '';
    if (jabInput) jabInput.value = emp.Jabatan || emp.Posisi || '';
  }
}

function openAddModal(key) {
  const s = SCHEMAS[key];
  if (!s) return;
  document.getElementById('genericModalTitle').textContent = s.title;
  const form = document.getElementById('genericAddForm');
  form.dataset.targetKey = key;
  form.innerHTML = s.fields.map(f => {
    const isRoomNip = (key === 'DB_Ruangan' && f === 'Penanggungjawab Ruangan');
    const extraAttrs = isRoomNip
      ? 'list="pegawaiNipDatalist" oninput="handleRoomNipLookup(this)" onchange="handleRoomNipLookup(this)"'
      : '';
    return `
      <div>
        <label class="block font-bold mb-1">${f}${isRoomNip ? ' <span class="text-teal-600 font-normal">(Auto-Lookup Pegawai)</span>' : ''}</label>
        <input type="text" name="${f}" ${extraAttrs} placeholder="Isi ${f}..."
          class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
      </div>
    `;
  }).join('') + `<button type="submit" class="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold">Simpan</button>`;
  const m = document.getElementById('genericAddModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeGenericModal() {
  const m = document.getElementById('genericAddModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}
async function submitGenericRecord(e) {
  e.preventDefault();
  const key = e.target.dataset.targetKey;
  const payload = Object.fromEntries(new FormData(e.target).entries());
  const res = await fetch(`/api/add/${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeGenericModal();
    await loadDashboard();
  }
}

function openInitModal() {
  const m = document.getElementById('initModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeInitModal() {
  const m = document.getElementById('initModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}
async function runInitData() {
  const btn = document.getElementById('btnRunInit');
  btn.disabled = true;
  const include_samples = document.getElementById('initIncludeSamples').checked;
  const res = await fetch('/api/init-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ include_samples })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  btn.disabled = false;
  if (out.ok) {
    closeInitModal();
    await loadDashboard();
  }
}

async function refreshAll() {
  await fetch('/api/refresh', { method: 'POST' });
  await loadDashboard();
  showToast('Data berhasil disinkronkan dengan Google Sheets.', 'success');
}

async function logoutUser() {
  await fetch('/api/logout', { method: 'POST' });
  window.location.href = '/';
}

initTheme();
loadDashboard();
