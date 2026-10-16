#pragma once

static const wchar_t* kUsage = LR"(Monitor Input Switcher - command line

  MonitorInputSwitcher.exe --monitor <n|n,n|all> --input <input>
  MonitorInputSwitcher.exe <n>=<input> [<n>=<input> ...]
  MonitorInputSwitcher.exe --button <label|number>
  MonitorInputSwitcher.exe --get [--monitor <n>]
  MonitorInputSwitcher.exe --list

Options (-x, --x and /x all work; --x=value also works):
  -m, --monitor   Monitor number as shown by Windows "Identify" (default 1).
                  A comma list (1,2) or "all" is accepted when switching.
  -i, --input     vga1 vga2 dvi1 dvi2 dp1 dp2 hdmi1 hdmi2 usbc
                  or a raw VCP 0x60 code: 0x11 (hex) or 17 (decimal)
  -b, --button    Run a button saved in the GUI's config, by label or position
  -g, --get       Print the monitor's current input code, e.g. 0x11
  -l, --list      List monitors: number, name, resolution, current input (tab separated)
  -v, --verbose   Print a line for every switch performed
  -h, --help      This text

Exit codes: 0 ok, 1 monitor rejected the command (DDC/CI), 2 bad arguments,
            3 monitor not found, 4 button not found

Examples:
  MonitorInputSwitcher.exe --monitor 1 --input hdmi1
  MonitorInputSwitcher.exe 1=hdmi1 2=dp1
  MonitorInputSwitcher.exe -m all -i 0x1B
  MonitorInputSwitcher.exe --button "Work PC"
)";

static void InitOut() {
    g_console.out = GetStdHandle(STD_OUTPUT_HANDLE);
    g_console.err = GetStdHandle(STD_ERROR_HANDLE);
    bool noOut = !g_console.out || g_console.out == INVALID_HANDLE_VALUE;
    bool noErr = !g_console.err || g_console.err == INVALID_HANDLE_VALUE;
    if ((noOut || noErr) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        HANDLE c = CreateFileW(L"CONOUT$", GENERIC_WRITE, FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
        if (c == INVALID_HANDLE_VALUE) return;
        g_console.attached = c;
        if (noOut) g_console.out = c;
        if (noErr) g_console.err = c;
    }
}

static void ShutdownOut() {
    if (g_console.attached && g_console.attached != INVALID_HANDLE_VALUE) {
        CloseHandle(g_console.attached);
        g_console.attached = nullptr;
    }
}

static void Emit(HANDLE h, const wchar_t* s) {
    if (!h || h == INVALID_HANDLE_VALUE) return;
    DWORD n, mode;
    if (GetConsoleMode(h, &mode)) WriteConsoleW(h, s, (DWORD)wcslen(s), &n, nullptr);
    else {
        static char buf[8192];
        int len = WideCharToMultiByte(CP_UTF8, 0, s, -1, buf, sizeof(buf), nullptr, nullptr);
        if (len > 1) WriteFile(h, buf, (DWORD)(len - 1), &n, nullptr);
    }
}

static void Out(const wchar_t* fmt, ...) {
    wchar_t b[1024]; va_list ap; va_start(ap, fmt);
    _vsnwprintf_s(b, 1024, _TRUNCATE, fmt, ap); va_end(ap);
    Emit(g_console.out, b);
}

static void Err(const wchar_t* fmt, ...) {
    wchar_t b[1024]; va_list ap; va_start(ap, fmt);
    _vsnwprintf_s(b, 1024, _TRUNCATE, fmt, ap); va_end(ap);
    Emit(g_console.err, b);
}

static bool ParseInput(const wchar_t* s, DWORD* out) {
    static const struct { const wchar_t* name; DWORD v; } names[] = {
        { L"vga", 0x01 }, { L"vga1", 0x01 }, { L"vga2", 0x02 }, { L"dvi", 0x03 }, { L"dvi1", 0x03 }, { L"dvi2", 0x04 },
        { L"dp", 0x0F }, { L"dp1", 0x0F }, { L"displayport", 0x0F }, { L"displayport1", 0x0F },
        { L"dp2", 0x10 }, { L"displayport2", 0x10 },
        { L"hdmi", 0x11 }, { L"hdmi1", 0x11 }, { L"hdmi2", 0x12 }, { L"usbc", 0x1B },
    };
    wchar_t n[32]; int k = 0;
    for (const wchar_t* p = s; *p && k < 31; p++)
        if (*p != L'-' && *p != L'_' && *p != L' ') n[k++] = (wchar_t)towlower(*p);
    n[k] = 0;
    for (size_t i = 0; i < sizeof(names) / sizeof(names[0]); i++)
        if (!wcscmp(n, names[i].name)) { *out = names[i].v; return true; }
    wchar_t* e;
    int base = (s[0] == L'0' && (s[1] == L'x' || s[1] == L'X')) ? 16 : 10;
    unsigned long v = wcstoul(s, &e, base);
    if (s[0] && !*e && v <= 0xFFFF) { *out = v; return true; }
    return false;
}

static int ExpandMonitors(const wchar_t* spec, int* out, int cap) {
    if (!_wcsicmp(spec, L"all")) {
        Mon m[MAX_MONS]; int n = GetMonitors(m, MAX_MONS), c = 0;
        for (int i = 0; i < n && c < cap; i++) out[c++] = m[i].num;
        return c;
    }
    int n = 0;
    const wchar_t* p = spec;
    while (*p) {
        wchar_t* e; long v = wcstol(p, &e, 10);
        if (e == p || v < 1 || n >= cap) return -1;
        out[n++] = (int)v; p = e;
        if (*p == L',' || *p == L';') p++; else if (*p) return -1;
    }
    return n > 0 ? n : -1;
}

static int RunCli(int argc, wchar_t** argv) {
    SetProcessDPIAware();
    InitOut();
    InitPaths();
    if (argc < 2) { Emit(g_console.out, kUsage); return 0; }

    const wchar_t *monArg = nullptr, *inArg = nullptr, *btnArg = nullptr;
    bool get = false, list = false, verbose = false;
    struct CliJob { int mon; DWORD in; } jobs[64];
    int nj = 0, rc = 0;
    auto fail = [&](int code) { if (code > rc) rc = code; };

    for (int i = 1; i < argc; i++) {
        wchar_t* a = argv[i];
        if (a[0] != L'-' && a[0] != L'/') {
            wchar_t* e; long m = wcstol(a, &e, 10); DWORD v = 0;
            if (e == a || *e != L'=' || m < 1 || !ParseInput(e + 1, &v) || nj >= 64) {
                Err(L"error: unrecognised argument '%s'\nRun with --help for usage.\n", a);
                return 2;
            }
            jobs[nj].mon = (int)m; jobs[nj].in = v; nj++;
            continue;
        }
        wchar_t* o = a;
        while (*o == L'-' || *o == L'/') o++;
        const wchar_t* val = nullptr;
        wchar_t* eq = wcschr(o, L'=');
        if (eq) { *eq = 0; val = eq + 1; }
        auto is = [&](const wchar_t* n1, const wchar_t* n2) { return _wcsicmp(o, n1) == 0 || _wcsicmp(o, n2) == 0; };
        auto takeVal = [&]() -> const wchar_t* { if (!val && i + 1 < argc) val = argv[++i]; return val; };

        if (is(L"help", L"h") || !wcscmp(o, L"?")) { Emit(g_console.out, kUsage); return 0; }
        else if (is(L"verbose", L"v")) verbose = true;
        else if (is(L"get", L"g"))     get = true;
        else if (is(L"list", L"l"))    list = true;
        else if (is(L"monitor", L"m")) monArg = takeVal();
        else if (is(L"input", L"i"))   inArg = takeVal();
        else if (is(L"button", L"b"))  btnArg = takeVal();
        else { Err(L"error: unknown option '%s'\nRun with --help for usage.\n", o); return 2; }

        if ((is(L"monitor", L"m") && !monArg) || (is(L"input", L"i") && !inArg) || (is(L"button", L"b") && !btnArg)) {
            Err(L"error: option '%s' needs a value\n", o);
            return 2;
        }
    }

    if (list) {
        Mon m[MAX_MONS]; int n = GetMonitors(m, MAX_MONS);
        for (int i = 0; i < n; i++) {
            wchar_t nm[128] = L"Unknown";
            { Phys p; if (p.OpenH(m[i].h)) p.Name(nm, 128); }
            Out(L"%d\t%s\t%dx%d\t", m[i].num, nm, m[i].rc.right - m[i].rc.left, m[i].rc.bottom - m[i].rc.top);
            DWORD v;
            if (DdcGetInput(m[i].num, &v)) {
                const wchar_t* sn = InputShortName(v);
                if (sn) Out(L"0x%02X (%s)\n", v, sn); else Out(L"0x%02X\n", v);
            } else Out(L"n/a\n");
        }
        return 0;
    }

    int mons[32], nm = 1; mons[0] = 1;
    if (monArg) {
        nm = ExpandMonitors(monArg, mons, 32);
        if (nm < 0) { Err(L"error: invalid monitor '%s'\n", monArg); return 2; }
    }

    if (get) {
        DWORD v;
        if (nm != 1) { Err(L"error: --get needs exactly one monitor\n"); return 2; }
        if (!MonitorExists(mons[0])) { Err(L"error: monitor %d not found\n", mons[0]); return 3; }
        if (!DdcGetInput(mons[0], &v)) { Err(L"error: could not read monitor %d (is DDC/CI enabled in its menu?)\n", mons[0]); return 1; }
        Out(L"0x%02X\n", v);
        return 0;
    }

    if (btnArg) {
        int bm; DWORD bi;
        if (!FindButton(btnArg, &bm, &bi)) { Err(L"error: button '%s' not found in %s\n", btnArg, g_paths.ini); return 4; }
        if (nj < 64) { jobs[nj].mon = bm; jobs[nj].in = bi; nj++; }
    }
    if (inArg) {
        DWORD v;
        if (!ParseInput(inArg, &v)) { Err(L"error: unknown input '%s'\n", inArg); return 2; }
        for (int k = 0; k < nm && nj < 64; k++) { jobs[nj].mon = mons[k]; jobs[nj].in = v; nj++; }
    } else if (monArg && !btnArg && nj == 0) {
        Err(L"error: --monitor needs --input\n");
        return 2;
    }
    if (nj == 0) {
        Err(L"error: nothing to do (use --input, --button or <n>=<input>)\nRun with --help for usage.\n");
        return 2;
    }

    for (int k = 0; k < nj; k++) {
        if (!MonitorExists(jobs[k].mon)) { Err(L"error: monitor %d not found\n", jobs[k].mon); fail(3); continue; }
        if (DdcSetInput(jobs[k].mon, jobs[k].in)) {
            if (verbose) {
                const wchar_t* sn = InputShortName(jobs[k].in);
                if (sn) Out(L"monitor %d -> 0x%02X (%s)\n", jobs[k].mon, jobs[k].in, sn);
                else    Out(L"monitor %d -> 0x%02X\n", jobs[k].mon, jobs[k].in);
            }
        } else {
            Err(L"error: monitor %d did not accept input 0x%02X (is DDC/CI enabled in its menu?)\n", jobs[k].mon, jobs[k].in);
            fail(1);
        }
    }
    return rc;
}
