#pragma once

static const BYTE VCP_INPUT_SOURCE = 0x60;

static const struct { DWORD v; const wchar_t* shortName; const wchar_t* fullName; } kInputs[] = {
    { 0x01, L"VGA-1",  L"VGA 1"           }, { 0x02, L"VGA-2",  L"VGA 2"           },
    { 0x03, L"DVI-1",  L"DVI 1"           }, { 0x04, L"DVI-2",  L"DVI 2"           },
    { 0x0F, L"DP-1",   L"DisplayPort 1"   }, { 0x10, L"DP-2",   L"DisplayPort 2"   },
    { 0x11, L"HDMI-1", L"HDMI 1"          }, { 0x12, L"HDMI-2", L"HDMI 2"          },
    { 0x1B, L"USB-C",  L"USB-C (model dependent)" },
};
static const int NINPUTS = sizeof(kInputs) / sizeof(kInputs[0]);

struct Mon { int num; HMONITOR h; RECT rc; };
struct EnumCtx { Mon* out; int n; int cap; };

static BOOL CALLBACK MonProc(HMONITOR hm, HDC, LPRECT, LPARAM lp) {
    EnumCtx* c = (EnumCtx*)lp;
    if (c->n >= c->cap) return FALSE;
    MONITORINFOEXW mi; mi.cbSize = sizeof(mi);
    if (!GetMonitorInfoW(hm, (MONITORINFO*)&mi)) return TRUE;
    const wchar_t* p = wcsstr(mi.szDevice, L"DISPLAY");
    Mon& m = c->out[c->n++];
    m.num = p ? _wtoi(p + 7) : c->n;
    m.h = hm;
    m.rc = mi.rcMonitor;
    return TRUE;
}

static int GetMonitors(Mon* out, int cap) {
    EnumCtx c = { out, 0, cap };
    EnumDisplayMonitors(nullptr, nullptr, MonProc, (LPARAM)&c);
    for (int i = 1; i < c.n; i++) {
        Mon t = out[i]; int j = i - 1;
        while (j >= 0 && out[j].num > t.num) { out[j + 1] = out[j]; j--; }
        out[j + 1] = t;
    }
    return c.n;
}

struct Phys {
    PHYSICAL_MONITOR* pm = nullptr;
    DWORD n = 0;
    Phys() = default;
    Phys(const Phys&) = delete;
    Phys& operator=(const Phys&) = delete;
    bool OpenH(HMONITOR h) {
        if (!GetNumberOfPhysicalMonitorsFromHMONITOR(h, &n) || n == 0) return false;
        pm = new (std::nothrow) PHYSICAL_MONITOR[n];
        if (!pm) { n = 0; return false; }
        if (!GetPhysicalMonitorsFromHMONITOR(h, n, pm)) { delete[] pm; pm = nullptr; n = 0; return false; }
        return true;
    }
    bool Open(int num) {
        Mon mons[MAX_MONS]; int c = GetMonitors(mons, MAX_MONS);
        for (int i = 0; i < c; i++) if (mons[i].num == num) return OpenH(mons[i].h);
        return false;
    }
    HANDLE H() const { return pm[0].hPhysicalMonitor; }
    void Name(wchar_t* out, int cap) const { wcsncpy_s(out, cap, pm[0].szPhysicalMonitorDescription, _TRUNCATE); }
    ~Phys() { if (pm) { DestroyPhysicalMonitors(n, pm); delete[] pm; } }
};

static bool DdcSetInput(int mon, DWORD value) {
    Phys p; if (!p.Open(mon)) return false;
    for (int i = 0; i < 3; i++) {
        if (SetVCPFeature(p.H(), VCP_INPUT_SOURCE, value)) return true;
        Sleep(120);
    }
    return false;
}

static bool DdcGetInput(int mon, DWORD* value) {
    Phys p; if (!p.Open(mon)) return false;
    for (int i = 0; i < 3; i++) {
        DWORD cur = 0, max = 0;
        if (GetVCPFeatureAndVCPFeatureReply(p.H(), VCP_INPUT_SOURCE, nullptr, &cur, &max)) {
            *value = cur & 0xFF;
            return true;
        }
        Sleep(120);
    }
    return false;
}

static const wchar_t* InputShortName(DWORD v) {
    for (int i = 0; i < NINPUTS; i++) if (kInputs[i].v == v) return kInputs[i].shortName;
    return nullptr;
}

static bool MonitorExists(int num) {
    Mon m[MAX_MONS]; int n = GetMonitors(m, MAX_MONS);
    for (int i = 0; i < n; i++) if (m[i].num == num) return true;
    return false;
}
