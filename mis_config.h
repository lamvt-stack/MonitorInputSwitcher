#pragma once

static const wchar_t* kDispNames[] = { L"label", L"icon", L"both" };
static const wchar_t* kPosNames[]  = { L"top", L"bottom" };
static const wchar_t* kTrayNames[] = { L"auto", L"light", L"dark" };

static void InitPaths() {
    GetModuleFileNameW(nullptr, g_paths.exe, MAX_PATH);
    wcscpy_s(g_paths.ini, g_paths.exe);
    wchar_t* slash = wcsrchr(g_paths.ini, L'\\');
    wchar_t* name = slash ? slash + 1 : g_paths.ini;
    wcscpy_s(name, (size_t)(MAX_PATH - (name - g_paths.ini)), L"MonitorInputSwitcher.ini");
}

static int IniInt(const wchar_t* sec, const wchar_t* key, int def) {
    wchar_t t[32];
    GetPrivateProfileStringW(sec, key, L"", t, 32, g_paths.ini);
    return t[0] ? (int)wcstol(t, nullptr, 10) : def;
}

static void WriteInt(const wchar_t* sec, const wchar_t* key, int v) {
    wchar_t t[32]; swprintf_s(t, L"%d", v);
    WritePrivateProfileStringW(sec, key, t, g_paths.ini);
}

static void SaveConfig() {
    DeleteFileW(g_paths.ini);
    HANDLE f = CreateFileW(g_paths.ini, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return;
    WORD bom = 0xFEFF; DWORD wr; WriteFile(f, &bom, 2, &wr, nullptr); CloseHandle(f);

    int count = 0;
    for (int i = 0; i < MAX_BTNS; i++) {
        Btn* b = &g_btns[i];
        if (!b->hwnd) continue;
        RECT r; GetWindowRect(b->hwnd, &r); b->x = r.left; b->y = r.top;
        wchar_t sec[16], t[32];
        swprintf_s(sec, L"Button%d", ++count);
        WritePrivateProfileStringW(sec, L"Label", b->label, g_paths.ini);
        WriteInt(sec, L"Monitor", b->monitor);
        swprintf_s(t, L"0x%02X", b->input);
        WritePrivateProfileStringW(sec, L"Input", t, g_paths.ini);
        WriteInt(sec, L"X", b->x);
        WriteInt(sec, L"Y", b->y);
        swprintf_s(t, L"%02X%02X%02X", GetRValue(b->color), GetGValue(b->color), GetBValue(b->color));
        WritePrivateProfileStringW(sec, L"Color", t, g_paths.ini);
        WriteInt(sec, L"Opacity", b->opacity);
        WritePrivateProfileStringW(sec, L"Display", kDispNames[b->display], g_paths.ini);
        WritePrivateProfileStringW(sec, L"LabelPos", kPosNames[b->lpos], g_paths.ini);
        WritePrivateProfileStringW(sec, L"Icon", b->icon, g_paths.ini);
        WriteInt(sec, L"IconOpacity", b->iconOpacity);
        WriteInt(sec, L"IconSize", b->iconSize);
        WriteInt(sec, L"NoPadding", b->noPad);
    }
    WriteInt(L"General", L"Count", count);
    WriteInt(L"General", L"Locked", g_locked);
    WriteInt(L"General", L"Hidden", g_hidden);
    WritePrivateProfileStringW(L"General", L"TrayIcon", kTrayNames[g_trayPref], g_paths.ini);
}

static bool LoadConfig() {
    int count = IniInt(L"General", L"Count", -1);
    if (count < 0) return false;
    g_locked = IniInt(L"General", L"Locked", 0) != 0;
    g_hidden = IniInt(L"General", L"Hidden", 0) != 0;
    for (int i = 0; i < count && i < MAX_BTNS; i++) {
        Btn* b = &g_btns[i];
        wchar_t sec[16], t[64];
        swprintf_s(sec, L"Button%d", i + 1);
        GetPrivateProfileStringW(sec, L"Label", L"Input", b->label, 32, g_paths.ini);
        if (!b->label[0]) wcscpy_s(b->label, L"Input");
        b->monitor = IniInt(sec, L"Monitor", 1); if (b->monitor < 1) b->monitor = 1;
        GetPrivateProfileStringW(sec, L"Input", L"0x11", t, 64, g_paths.ini);
        b->input = wcstoul(t, nullptr, 0);
        GetPrivateProfileStringW(sec, L"Color", L"2D6CDF", t, 64, g_paths.ini);
        unsigned long c = wcstoul(t, nullptr, 16);
        b->color = RGB((c >> 16) & 255, (c >> 8) & 255, c & 255);
        b->opacity = imax(MIN_OPACITY, imin(100, IniInt(sec, L"Opacity", DEF_OPACITY)));
        GetPrivateProfileStringW(sec, L"Display", L"label", t, 64, g_paths.ini);
        b->display = !_wcsicmp(t, L"both") ? D_BOTH : !_wcsicmp(t, L"icon") ? D_ICON : D_LABEL;
        GetPrivateProfileStringW(sec, L"LabelPos", L"bottom", t, 64, g_paths.ini);
        b->lpos = !_wcsicmp(t, L"top") ? LP_TOP : LP_BOTTOM;
        GetPrivateProfileStringW(sec, L"Icon", L"", b->icon, MAX_PATH, g_paths.ini);
        b->iconOpacity = imax(MIN_ICON_OPACITY, imin(100, IniInt(sec, L"IconOpacity", DEF_ICON_OPACITY)));
        b->iconSize = imax(16, imin(96, IniInt(sec, L"IconSize", DEF_ICON_SIZE)));
        b->noPad = IniInt(sec, L"NoPadding", 0) != 0;

        b->x = IniInt(sec, L"X", INT_MIN);
        b->y = IniInt(sec, L"Y", INT_MIN);
        POINT pt = { b->x + S(30), b->y + S(15) };
        if (b->x == INT_MIN || b->y == INT_MIN || !MonitorFromPoint(pt, MONITOR_DEFAULTTONULL))
            PlaceDefault(b, i);
        CreateBtnWindow(b);
    }
    return true;
}

static const wchar_t* RUN_KEY  = L"Software\\Microsoft\\Windows\\CurrentVersion\\Run";
static const wchar_t* RUN_NAME = L"MonitorInputSwitcher";

static bool GetAutostart() {
    HKEY k; bool r = false;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, RUN_KEY, 0, KEY_QUERY_VALUE, &k) == ERROR_SUCCESS) {
        r = RegQueryValueExW(k, RUN_NAME, nullptr, nullptr, nullptr, nullptr) == ERROR_SUCCESS;
        RegCloseKey(k);
    }
    return r;
}

static void SetAutostart(bool on) {
    HKEY k;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, RUN_KEY, 0, KEY_SET_VALUE, &k) != ERROR_SUCCESS) return;
    if (on) {
        wchar_t v[MAX_PATH + 4]; swprintf_s(v, L"\"%s\"", g_paths.exe);
        RegSetValueExW(k, RUN_NAME, 0, REG_SZ, (const BYTE*)v, (DWORD)((wcslen(v) + 1) * sizeof(wchar_t)));
    } else RegDeleteValueW(k, RUN_NAME);
    RegCloseKey(k);
}

static void LoadTrayPref() {
    wchar_t t[16];
    GetPrivateProfileStringW(L"General", L"TrayIcon", L"auto", t, 16, g_paths.ini);
    g_trayPref = !_wcsicmp(t, L"light") ? TRAY_LIGHT : !_wcsicmp(t, L"dark") ? TRAY_DARK : TRAY_AUTO;
}

static bool FindButton(const wchar_t* key, int* mon, DWORD* input) {
    int count = IniInt(L"General", L"Count", 0);
    wchar_t* e; long idx = wcstol(key, &e, 10);
    bool numeric = key[0] && !*e;
    for (int pass = 0; pass < 2; pass++)
        for (int i = 1; i <= count; i++) {
            wchar_t sec[16], lab[32], t[64];
            swprintf_s(sec, L"Button%d", i);
            GetPrivateProfileStringW(sec, L"Label", L"", lab, 32, g_paths.ini);
            bool hit = pass == 0 ? _wcsicmp(lab, key) == 0 : (numeric && idx == i);
            if (!hit) continue;
            *mon = IniInt(sec, L"Monitor", 1);
            GetPrivateProfileStringW(sec, L"Input", L"0x11", t, 64, g_paths.ini);
            *input = wcstoul(t, nullptr, 0);
            return true;
        }
    return false;
}
