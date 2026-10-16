@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Builds both executables from the refactored single-source layout.
rem Prefers MSVC, but falls back to MinGW-w64 if that is the toolchain available on PATH.
rem Needs MonitorInputSwitcher.cpp, mis_monitor.h, mis_config.h, mis_cli.h, app.rc, app.ico,
rem tray-light.ico, and tray-dark.ico.

pushd "%~dp0" || exit /b 1

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSINSTALL="
if exist "%VSWHERE%" (
    for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do set "VSINSTALL=%%I"
)
if defined VSINSTALL if exist "%VSINSTALL%\Common7\Tools\VsDevCmd.bat" (
    call "%VSINSTALL%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul
)

set "MSVC_CL="
for /f "delims=" %%I in ('where cl 2^>nul') do if not defined MSVC_CL set "MSVC_CL=%%I"

set "MSVC_RC="
for /f "delims=" %%I in ('where rc 2^>nul') do if not defined MSVC_RC set "MSVC_RC=%%I"
if not defined MSVC_RC (
    if defined WindowsSdkDir if defined WindowsSdkVersion (
        if exist "%WindowsSdkDir%bin\%WindowsSdkVersion%x64\rc.exe" set "MSVC_RC=%WindowsSdkDir%bin\%WindowsSdkVersion%x64\rc.exe"
    )
)

if defined MSVC_CL if defined MSVC_RC goto :build_msvc

set "MINGW_GXX="
for /f "delims=" %%I in ('where g++ 2^>nul') do if not defined MINGW_GXX set "MINGW_GXX=%%I"
if not defined MINGW_GXX (
    if exist "C:\msys64\mingw64\bin\g++.exe" set "MINGW_GXX=C:\msys64\mingw64\bin\g++.exe"
    if not defined MINGW_GXX if exist "C:\msys64\ucrt64\bin\g++.exe" set "MINGW_GXX=C:\msys64\ucrt64\bin\g++.exe"
)

if defined MINGW_GXX goto :build_mingw

echo No supported C++ toolchain found.
echo Install the Desktop development with C++ workload or MinGW-w64, then rerun this script.
exit /b 1

:build_msvc
del /q app.res app_cli.res gui.obj cli.obj MonitorInputSwitcher.exe mis-cli.exe >nul 2>nul
"!MSVC_RC!" /nologo /fo app.res app.rc || goto :done_fail
"!MSVC_RC!" /nologo /d MIS_CLI /fo app_cli.res app.rc || goto :done_fail
"!MSVC_CL!" /nologo /std:c++17 /O1 /Os /GL /Gw /MT /GS- /EHs-c- /DUNICODE /D_UNICODE /Fo:gui.obj MonitorInputSwitcher.cpp app.res /link /SUBSYSTEM:WINDOWS /OPT:REF /OPT:ICF /OUT:MonitorInputSwitcher.exe || goto :done_fail
"!MSVC_CL!" /nologo /std:c++17 /O1 /Os /GL /Gw /MT /GS- /EHs-c- /DUNICODE /D_UNICODE /DMIS_CLI /Fo:cli.obj MonitorInputSwitcher.cpp app_cli.res /link /SUBSYSTEM:CONSOLE /OPT:REF /OPT:ICF /OUT:mis-cli.exe || goto :done_fail
del /q app.res app_cli.res gui.obj cli.obj >nul 2>nul
echo Built MonitorInputSwitcher.exe and mis-cli.exe with MSVC.
goto :done_ok

:build_mingw
del /q app_res.o app_res_cli.o MonitorInputSwitcher.exe mis-cli.exe >nul 2>nul
for %%I in ("!MINGW_GXX!") do set "MINGW_BIN=%%~dpI"
if defined MINGW_BIN set "PATH=!MINGW_BIN!;%PATH%"
"!MINGW_BIN!windres.exe" app.rc -O coff -o app_res.o || goto :done_fail
"!MINGW_BIN!windres.exe" -DMIS_CLI app.rc -O coff -o app_res_cli.o || goto :done_fail
"!MINGW_GXX!" -std=c++17 -Os -s -municode -mwindows -static -ffunction-sections -fdata-sections -Wl,--gc-sections MonitorInputSwitcher.cpp app_res.o -o MonitorInputSwitcher.exe -ldxva2 -lcomdlg32 -lcomctl32 -lmsimg32 -lgdi32 -luser32 -lshell32 -ladvapi32 || goto :done_fail
"!MINGW_GXX!" -std=c++17 -Os -s -municode -mconsole -static -DMIS_CLI -ffunction-sections -fdata-sections -Wl,--gc-sections MonitorInputSwitcher.cpp app_res_cli.o -o mis-cli.exe -ldxva2 -lcomdlg32 -lcomctl32 -lmsimg32 -lgdi32 -luser32 -lshell32 -ladvapi32 || goto :done_fail
del /q app_res.o app_res_cli.o >nul 2>nul
echo Built MonitorInputSwitcher.exe and mis-cli.exe with MinGW-w64.
goto :done_ok

:done_ok
popd
exit /b 0

:done_fail
set "CODE=%errorlevel%"
popd
exit /b %CODE%
