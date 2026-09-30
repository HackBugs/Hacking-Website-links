@echo off
rem =====================================================================
rem  SMART ORGANIZER 2026 - automatic file organizer for Windows 10/11
rem  Double-click to run. Best viewed in Windows Terminal or CMD.
rem =====================================================================
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title Smart Organizer 2026
mode con: cols=92 lines=46 >nul 2>&1

set "APPDIR=%LOCALAPPDATA%\SmartOrganizer"
if not exist "%APPDIR%" mkdir "%APPDIR%" >nul 2>&1
set "CFG=%APPDIR%\settings.ini"
set "LASTRUN=%APPDIR%\lastrun.txt"
set "HIST=%APPDIR%\history.log"
set "EXF=%TEMP%\so_exclude.txt"
set "DMAP=%TEMP%\so_datemap.txt"
set "SELF=%~nx0"

rem ---- defaults (overridden by saved settings) ----
set "ROOT=%USERPROFILE%\Downloads"
set "SUB=0"
set "THEME=1"
set "MODE=type"
set "QUIET=0"
set "PREVIEW=0"
if exist "%CFG%" for /f "usebackq tokens=1,* delims==" %%A in ("%CFG%") do set "%%A=%%B"

rem ---- ANSI colour setup ----
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RST=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[38;2;148;163;184m"
set "W=%ESC%[38;2;241;245;249m"
set "GR=%ESC%[38;2;74;222;128m"
set "YE=%ESC%[38;2;250;204;21m"
set "RE=%ESC%[38;2;248;113;113m"
call :THEME

rem ---- file type -> folder map ----
call :MAP "PDF Files" pdf
call :MAP "Notepad Files" txt
call :MAP "Word Files" doc docx
call :MAP "Document Files" rtf odt
call :MAP "Excel Files" xls xlsx csv ods
call :MAP "PowerPoint Files" ppt pptx odp
call :MAP "Image Files" jpg jpeg png gif bmp webp tiff svg ico
call :MAP "Music Files" mp3 wav aac flac m4a ogg wma
call :MAP "Video Files" mp4 mkv avi mov wmv flv webm mpeg 3gp
call :MAP "Compressed Files" zip rar 7z tar gz bz2
call :MAP "Application Files" exe msi appx msix
call :MAP "Web Files" html htm css js php jsx tsx
call :MAP "Script Files" bat cmd ps1 sh vbs
call :MAP "Disk Image Files" iso img vhd vhdx
call :MAP "Database Files" sql db sqlite sqlite3
call :MAP "Data Config Files" json xml yaml yml toml
call :MAP "Programming Files" py java c cpp h cs go rs
call :MAP "Log Files" log
call :MAP "Font Files" ttf otf woff woff2
call :MAP "Torrent Files" torrent
call :MAP "Android Application Files" apk
call :MAP "Linux Package Files" deb rpm
call :MAP "Backup Temp Files" bak tmp

if /i "%~1"=="/auto" goto AUTO
goto MAIN

rem =====================================================================
rem  MAIN MENU
rem =====================================================================
:MAIN
call :HEADER
call :SEC "ORGANIZE"
call :ITEM 2 "Organize by file type" "sort into folders by extension"
call :ITEM 3 "Organize by type + date" "type folder, then Year-Month"
call :ITEM 4 "Preview (no changes)" "see what would happen"
call :ITEM 5 "Undo last run" "put every file back"
echo   %AC1%│%RST%
call :SEC "TOOLS"
call :ITEM 1 "Change target folder" "Downloads, Desktop, browse..."
call :ITEM 6 "Scan report" "chart of what is inside"
call :ITEM 7 "Remove empty folders" "tidy up leftovers"
call :ITEM O "Open target folder" "show it in Explorer"
echo   %AC1%│%RST%
call :SEC "AUTOMATE AND SETTINGS"
call :ITEM 8 "Automation" "right-click menu, daily schedule"
call :ITEM 9 "Settings" "subfolders, colour theme"
call :ITEM H "History" "recent runs"
call :ITEM Q "Quit" ""
echo.
<nul set /p "=  %AC2%❯%RST% %W%Press a key%RST% "
choice /c 123456789HOQ /n >nul
goto M%errorlevel%

:M1
call :HEADER
call :SEC "CHOOSE A FOLDER"
call :ITEM 1 "Downloads" "%USERPROFILE%\Downloads"
call :ITEM 2 "Desktop" ""
call :ITEM 3 "Documents" ""
call :ITEM 4 "Pictures" ""
call :ITEM 5 "Browse..." "open a folder picker window"
call :ITEM 6 "Type or paste a path" ""
call :ITEM B "Back" ""
echo.
<nul set /p "=  %AC2%❯%RST% %W%Press a key%RST% "
choice /c 123456B /n >nul
goto F%errorlevel%

:F1
set "NEW=%USERPROFILE%\Downloads"
goto APPLY
:F2
set "NEW="
for /f "usebackq delims=" %%P in (`powershell -nop -c "[Environment]::GetFolderPath('Desktop')"`) do set "NEW=%%P"
goto APPLY
:F3
set "NEW="
for /f "usebackq delims=" %%P in (`powershell -nop -c "[Environment]::GetFolderPath('MyDocuments')"`) do set "NEW=%%P"
goto APPLY
:F4
set "NEW="
for /f "usebackq delims=" %%P in (`powershell -nop -c "[Environment]::GetFolderPath('MyPictures')"`) do set "NEW=%%P"
goto APPLY
:F5
set "NEW="
for /f "usebackq delims=" %%P in (`powershell -nop -sta -c "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Choose the folder to organize'; if($f.ShowDialog() -eq 'OK'){$f.SelectedPath}"`) do set "NEW=%%P"
goto APPLY
:F6
echo.
set "NEW="
set /p "NEW=  Paste folder path: "
goto APPLY
:F7
goto MAIN

:APPLY
if not defined NEW goto MAIN
set "OLD=%ROOT%"
set "ROOT=%NEW%"
call :NORM
if exist "%ROOT%\" goto APPLYOK
set "ROOT=%OLD%"
echo.
echo   %RE%✖ That folder does not exist.%RST%
call :PAUSEKEY
goto MAIN
:APPLYOK
call :SAVECFG
goto MAIN

:M2
set "MODE=type"
goto RUNFLOW
:M3
set "MODE=date"
goto RUNFLOW

:RUNFLOW
set "PREVIEW=0"
set "QUIET=0"
call :SAFE
if errorlevel 1 goto BADROOT
call :HEADER
if "%MODE%"=="date" (set "MODETXT=By type + Year-Month") else (set "MODETXT=By file type")
echo   %W%Ready to organize%RST%   %DIM%mode%RST% %AC2%%MODETXT%%RST%
echo   %DIM%Files are moved, never deleted. You can undo this run.%RST%
echo.
<nul set /p "=  %AC2%❯%RST% %W%Start now? [Y/N]%RST% "
choice /c YN /n >nul
if errorlevel 2 goto MAIN
echo.
call :RUN
call :SUMMARY
call :PAUSEKEY
goto MAIN

:M4
call :HEADER
call :SEC "PREVIEW AS"
call :ITEM 1 "By file type" ""
call :ITEM 2 "By type + date" ""
call :ITEM B "Back" ""
echo.
<nul set /p "=  %AC2%❯%RST% %W%Press a key%RST% "
choice /c 12B /n >nul
if errorlevel 3 goto MAIN
if errorlevel 2 (set "MODE=date") else (set "MODE=type")
set "PREVIEW=1"
set "QUIET=0"
call :SAFE
if errorlevel 1 goto BADROOT
call :HEADER
echo   %YE%PREVIEW%RST% %DIM%- nothing will be moved%RST%
echo.
call :RUN
call :SUMMARY
call :PAUSEKEY
goto MAIN

:M5
call :HEADER
if not exist "%LASTRUN%" goto NOUNDO
set "UCOUNT=0"
for /f "usebackq delims=" %%L in ("%LASTRUN%") do set /a UCOUNT+=1
if %UCOUNT% LSS 1 goto NOUNDO
echo   %W%Undo last run%RST%  %DIM%%UCOUNT% files will go back to where they were%RST%
echo.
<nul set /p "=  %AC2%❯%RST% %W%Restore them? [Y/N]%RST% "
choice /c YN /n >nul
if errorlevel 2 goto MAIN
set "UOK=0"
set "UFAIL=0"
for /f "usebackq tokens=1,2 delims=|" %%A in ("%LASTRUN%") do call :UNDOONE "%%A" "%%B"
del "%LASTRUN%" >nul 2>&1
echo.
echo   %GR%✔ Restored %UOK% files%RST%   %DIM%failed: %UFAIL%%RST%
echo   %DIM%Tip: use Remove empty folders to clear the leftover category folders.%RST%
call :PAUSEKEY
goto MAIN
:NOUNDO
echo   %YE%Nothing to undo yet.%RST%
call :PAUSEKEY
goto MAIN

:M6
set "MODE=type"
set "PREVIEW=1"
set "QUIET=1"
call :SAFE
if errorlevel 1 goto BADROOT
call :HEADER
echo   %W%Scan report%RST%
echo.
call :RUN
call :SUMMARY
call :PAUSEKEY
goto MAIN

:M7
call :SAFE
if errorlevel 1 goto BADROOT
call :HEADER
echo   %W%Remove empty folders%RST% %DIM%inside the target folder%RST%
echo.
<nul set /p "=  %AC2%❯%RST% %W%Continue? [Y/N]%RST% "
choice /c YN /n >nul
if errorlevel 2 goto MAIN
set "RMC=0"
for /f "delims=" %%D in ('dir /ad /b /s "%ROOT%" 2^>nul ^| sort /r') do call :RMD "%%D"
echo.
echo   %GR%✔ Removed %RMC% empty folders%RST%
call :PAUSEKEY
goto MAIN

:M8
call :HEADER
call :SEC "AUTOMATION"
call :ITEM 1 "Add right-click menu" "Organize any folder from Explorer"
call :ITEM 2 "Remove right-click menu" ""
call :ITEM 3 "Schedule daily organize" "runs on the target folder"
call :ITEM 4 "Remove schedule" ""
call :ITEM B "Back" ""
echo.
<nul set /p "=  %AC2%❯%RST% %W%Press a key%RST% "
choice /c 1234B /n >nul
goto AU%errorlevel%

:AU1
reg add "HKCU\Software\Classes\Directory\shell\SmartOrganizer" /ve /d "Organize with Smart Organizer" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\SmartOrganizer\command" /ve /d "\"%~f0\" /auto \"%%1\"" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\SmartOrganizer" /ve /d "Organize this folder" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\SmartOrganizer\command" /ve /d "\"%~f0\" /auto \"%%V\"" /f >nul 2>&1
echo.
echo   %GR%✔ Right-click menu added.%RST% %DIM%Keep this file in the same place.%RST%
call :PAUSEKEY
goto M8
:AU2
reg delete "HKCU\Software\Classes\Directory\shell\SmartOrganizer" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\SmartOrganizer" /f >nul 2>&1
echo.
echo   %GR%✔ Right-click menu removed.%RST%
call :PAUSEKEY
goto M8
:AU3
call :SAFE
if errorlevel 1 goto BADROOT
echo.
set "STIME="
set /p "STIME=  Time to run daily (24h HH:MM) [12:00]: "
if not defined STIME set "STIME=12:00"
echo %STIME%| findstr /r "^[0-2][0-9]:[0-5][0-9]$" >nul
if errorlevel 1 goto AUBADTIME
schtasks /create /tn "SmartOrganizer" /tr "\"%~f0\" /auto \"%ROOT%\"" /sc daily /st %STIME% /f >nul 2>&1
if errorlevel 1 goto AUFAIL
echo   %GR%✔ Scheduled daily at %STIME%%RST%
call :PAUSEKEY
goto M8
:AUBADTIME
echo   %RE%✖ Use the format HH:MM, for example 18:30%RST%
call :PAUSEKEY
goto M8
:AUFAIL
echo   %RE%✖ Could not create the task.%RST%
call :PAUSEKEY
goto M8
:AU4
schtasks /delete /tn "SmartOrganizer" /f >nul 2>&1
echo.
echo   %GR%✔ Schedule removed.%RST%
call :PAUSEKEY
goto M8
:AU5
goto MAIN

:M9
call :HEADER
call :SEC "SETTINGS"
if "%SUB%"=="1" (set "SUBTXT=ON") else (set "SUBTXT=OFF")
call :ITEM 1 "Include subfolders: %SUBTXT%" "also sort files inside subfolders"
call :ITEM 2 "Next colour theme" "Violet, Cyan, Emerald, Sunset"
call :ITEM B "Back" ""
echo.
<nul set /p "=  %AC2%❯%RST% %W%Press a key%RST% "
choice /c 12B /n >nul
if errorlevel 3 goto MAIN
if errorlevel 2 goto SETTHEME
if "%SUB%"=="1" (set "SUB=0") else (set "SUB=1")
call :SAVECFG
goto M9
:SETTHEME
set /a THEME=THEME%%4+1
call :SAVECFG
goto M9

:M10
call :HEADER
echo   %W%Recent runs%RST%
echo.
if not exist "%HIST%" echo   %DIM%No history yet.%RST%
if exist "%HIST%" powershell -nop -c "Get-Content -LiteralPath $env:HIST -Tail 15"
call :PAUSEKEY
goto MAIN

:M11
start "" explorer "%ROOT%"
goto MAIN

:M12
cls
echo.
echo   %AC2%◆%RST% %W%Stay organized. Goodbye!%RST%
echo.
timeout /t 1 /nobreak >nul 2>&1
exit /b 0

:BADROOT
echo.
echo   %RE%✖ That folder is missing or protected (drive root, Windows, Program Files, your profile).%RST%
echo   %DIM%Choose another folder with option 1.%RST%
call :PAUSEKEY
goto MAIN

rem =====================================================================
rem  AUTO MODE  (right-click menu and scheduled task)
rem =====================================================================
:AUTO
set "ROOT=%~2"
set "MODE=type"
set "QUIET=1"
set "PREVIEW=0"
call :NORM
call :HEADER
call :SAFE
if errorlevel 1 goto AUTOBAD
call :RUN
call :SUMMARY
timeout /t 5 /nobreak >nul 2>&1
exit /b 0
:AUTOBAD
echo   %RE%✖ Folder is missing or protected.%RST%
timeout /t 5 /nobreak >nul 2>&1
exit /b 1

rem =====================================================================
rem  ENGINE
rem =====================================================================
:RUN
set "MOVED=0"
set "FAILED=0"
set "SKIPPED=0"
for /f "delims==" %%A in ('set cnt_ 2^>nul') do set "%%A="
> "%EXF%" echo \Other Files\
for /f "tokens=2 delims==" %%C in ('set map_') do >>"%EXF%" echo \%%C\
if not "%PREVIEW%"=="1" type nul > "%LASTRUN%"
if "%MODE%"=="date" call :BUILDDATEMAP
echo   %DIM%Working...%RST%
if "%SUB%"=="1" goto RUNREC
for /f "delims=" %%F in ('dir /b /a-d "%ROOT%" 2^>nul') do call :PROCESS "%ROOT%\%%F"
goto RUNEND
:RUNREC
for /f "delims=" %%F in ('dir /b /a-d /s "%ROOT%" 2^>nul ^| findstr /v /i /l /g:"%EXF%"') do call :PROCESS "%%F"
:RUNEND
if not "%PREVIEW%"=="1" >>"%HIST%" echo %date% %time:~0,8% ^| %MODE% ^| moved %MOVED% ^| failed %FAILED% ^| %ROOT%
exit /b 0

:BUILDDATEMAP
set "ORG_ROOT=%ROOT%"
set "ORG_MAP=%DMAP%"
set "RECURSE="
if "%SUB%"=="1" set "RECURSE=-Recurse"
powershell -nop -c "$l=@(Get-ChildItem -LiteralPath $env:ORG_ROOT -File -Force %RECURSE% -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName + '|' + $_.LastWriteTime.ToString('yyyy-MM') }); [IO.File]::WriteAllLines($env:ORG_MAP,[string[]]$l)" >nul 2>&1
exit /b 0

:PROCESS
set "SRC=%~1"
set "NAME=%~nx1"
set "EXT=%~x1"
if /i "%NAME%"=="%SELF%" goto SKIPIT
if /i "%NAME%"=="desktop.ini" goto SKIPIT
if /i "%NAME%"=="thumbs.db" goto SKIPIT
if /i "%EXT%"==".crdownload" goto SKIPIT
if /i "%EXT%"==".part" goto SKIPIT
if /i "%EXT%"==".download" goto SKIPIT
if /i "%EXT%"==".opdownload" goto SKIPIT
if /i "%EXT%"==".lnk" goto SKIPIT
if /i "%EXT%"==".url" goto SKIPIT
set "CAT=Other Files"
if not "%EXT%"=="" call :GETCAT
set "DEST=%ROOT%\%CAT%"
if not "%MODE%"=="date" goto NODATE
set "DT="
for /f "tokens=2 delims=|" %%D in ('findstr /b /i /l /c:"%SRC%|" "%DMAP%" 2^>nul') do set "DT=%%D"
if not defined DT set "DT=Undated"
set "DEST=%DEST%\%DT%"
:NODATE
if /i "%~dp1"=="%DEST%\" goto SKIPIT
set "FINAL=%DEST%\%NAME%"
set "N=0"
:UNIQ
if not exist "%FINAL%" goto DOMOVE
set /a N+=1
set "FINAL=%DEST%\%~n1 (%N%)%~x1"
goto UNIQ
:DOMOVE
set "K=%CAT: =_%"
if "%PREVIEW%"=="1" goto PREVMOVE
if not exist "%DEST%\" mkdir "%DEST%" >nul 2>&1
move /y "%SRC%" "%FINAL%" >nul 2>&1
if errorlevel 1 goto FAILIT
set /a MOVED+=1
set /a cnt_%K%+=1
for %%S in ("%SRC%") do for %%T in ("%FINAL%") do >>"%LASTRUN%" echo %%~S^|%%~T
if "%QUIET%"=="0" for %%N in ("%NAME%") do echo   %GR%✔%RST% %W%%%~N%RST%  %AC2%➜%RST%  %DIM%%CAT%%RST%
exit /b 0
:PREVMOVE
set /a MOVED+=1
set /a cnt_%K%+=1
if "%QUIET%"=="0" for %%N in ("%NAME%") do echo   %YE%◌%RST% %W%%%~N%RST%  %AC2%➜%RST%  %DIM%%CAT%%RST%
exit /b 0
:FAILIT
set /a FAILED+=1
if "%QUIET%"=="0" for %%N in ("%NAME%") do echo   %RE%✖%RST% %W%%%~N%RST%  %DIM%locked or in use%RST%
exit /b 0
:SKIPIT
set /a SKIPPED+=1
exit /b 0

:GETCAT
set "E=%EXT:~1%"
set "C2="
call set "C2=%%map_%E%%%"
if defined C2 set "CAT=%C2%"
exit /b 0

:UNDOONE
if not exist "%~2" goto UFAILED
if not exist "%~dp1" mkdir "%~dp1" >nul 2>&1
set "TARGET=%~1"
if exist "%TARGET%" set "TARGET=%~dpn1 (restored)%~x1"
move /y "%~2" "%TARGET%" >nul 2>&1
if errorlevel 1 goto UFAILED
set /a UOK+=1
exit /b 0
:UFAILED
set /a UFAIL+=1
exit /b 0

:RMD
rd "%~1" >nul 2>&1 && set /a RMC+=1
exit /b 0

rem =====================================================================
rem  RESULT CHART
rem =====================================================================
:SUMMARY
if "%PREVIEW%"=="1" (set "WORD=Files found") else (set "WORD=Files moved")
echo.
call :SEC "RESULT"
set "MAXC=1"
for /f "tokens=1,2 delims==" %%A in ('set cnt_ 2^>nul') do call :FMAX %%B
if %MOVED% EQU 0 echo   %AC1%│%RST%  %DIM%Nothing to organize. This folder is already tidy.%RST%
for /f "tokens=1,2 delims==" %%A in ('set cnt_ 2^>nul') do call :SHOWROW %%A %%B
echo   %AC1%│%RST%
echo   %AC1%╰─%RST% %W%%WORD%: %MOVED%%RST%   %DIM%skipped: %SKIPPED%   failed: %FAILED%%RST%
exit /b 0

:FMAX
if %~1 GTR %MAXC% set "MAXC=%~1"
exit /b 0

:SHOWROW
set "L=%~1"
set "L=%L:~4%"
set "L=%L:_= %"
set "L=%L%                              "
set "L=%L:~0,27%"
set /a "BLK=%~2*24/MAXC"
if %BLK% LSS 1 set "BLK=1"
call :BAR
echo   %AC1%│%RST%  %W%%L%%RST%%AC2%%BARS%%RST%%DIM%%EMP%%RST% %W%%~2%RST%
exit /b 0

:BAR
set "BARS="
set "EMP="
set /a "F=BLK"
set /a "E=24-BLK"
:BARF
if %F% LEQ 0 goto BARE
set "BARS=%BARS%█"
set /a F-=1
goto BARF
:BARE
if %E% LEQ 0 exit /b 0
set "EMP=%EMP%░"
set /a E-=1
goto BARE

rem =====================================================================
rem  UI HELPERS
rem =====================================================================
:HEADER
cls
call :THEME
echo.
echo   %AC1%╭──────────────────────────────────────────────────────────────╮%RST%
echo   %AC1%│%RST%                                                              %AC1%│%RST%
echo   %AC1%│%RST%    %AC2%◆%RST%  %BOLD%%W%S M A R T   O R G A N I Z E R - H A C K B U G S%RST%                 %DIM%v2026%RST%    %AC1%│%RST%
echo   %AC1%│%RST%       %DIM%Tidy any folder in one click  ·  Undo anytime%RST%          %AC1%│%RST%
echo   %AC1%│%RST%                                                              %AC1%│%RST%
echo   %AC1%╰──────────────────────────────────────────────────────────────╯%RST%
call :UNDOSTATE
echo.
for %%R in ("%ROOT%") do echo   %DIM%TARGET%RST%      %W%%%~R%RST%
if "%SUB%"=="1" (set "SUBTXT=%GR%ON%RST%") else (set "SUBTXT=%DIM%OFF%RST%")
echo   %DIM%SUBFOLDERS%RST%  %SUBTXT%    %DIM%THEME%RST% %AC2%%TN%%RST%    %DIM%UNDO%RST% %UNDOTXT%%RST%
echo.
exit /b 0

:SEC
echo   %AC1%▌%RST% %BOLD%%W%%~1%RST%
exit /b 0

:ITEM
set "LB=%~2                                  "
set "LB=%LB:~0,31%"
echo   %AC1%│%RST%  %AC2%[%~1]%RST%  %W%%LB%%RST%%DIM%%~3%RST%
exit /b 0

:PAUSEKEY
echo.
<nul set /p "=  %DIM%Press any key to go back...%RST%"
pause >nul
exit /b 0

:UNDOSTATE
set "UNDOTXT=%DIM%none"
if not exist "%LASTRUN%" exit /b 0
for %%A in ("%LASTRUN%") do if %%~zA GTR 0 set "UNDOTXT=%GR%ready"
exit /b 0

:THEME
if "%THEME%"=="1" set "AC1=%ESC%[38;2;167;139;250m" & set "AC2=%ESC%[38;2;244;114;182m" & set "TN=Violet"
if "%THEME%"=="2" set "AC1=%ESC%[38;2;34;211;238m" & set "AC2=%ESC%[38;2;96;165;250m" & set "TN=Cyan"
if "%THEME%"=="3" set "AC1=%ESC%[38;2;52;211;153m" & set "AC2=%ESC%[38;2;163;230;53m" & set "TN=Emerald"
if "%THEME%"=="4" set "AC1=%ESC%[38;2;251;146;60m" & set "AC2=%ESC%[38;2;244;63;94m" & set "TN=Sunset"
if not defined AC1 set "AC1=%ESC%[38;2;167;139;250m" & set "AC2=%ESC%[38;2;244;114;182m" & set "TN=Violet"
exit /b 0

:MAP
set "MF=%~1"
:MAPL
shift
if "%~1"=="" exit /b 0
set "map_%~1=%MF%"
goto MAPL

:NORM
set "ROOT=%ROOT:"=%"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
exit /b 0

:SAVECFG
for %%R in ("%ROOT%") do >"%CFG%" echo ROOT=%%~R
>>"%CFG%" echo SUB=%SUB%
>>"%CFG%" echo THEME=%THEME%
exit /b 0

:SAFE
set "SAFEOK=1"
if not exist "%ROOT%\" set "SAFEOK=0"
if "%ROOT:~3%"=="" set "SAFEOK=0"
if /i "%ROOT%"=="%USERPROFILE%" set "SAFEOK=0"
echo "%ROOT%"| findstr /i /c:"\Windows" /c:"Program Files" /c:"ProgramData" /c:"\AppData" >nul && set "SAFEOK=0"
if "%SAFEOK%"=="0" exit /b 1
exit /b 0
