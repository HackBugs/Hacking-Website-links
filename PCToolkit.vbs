' HackBugs PC Advanced Toolkit v3 - Colorful & Visible Menu
' Updated: Option 17 = CMD/PowerShell choose | Option 38 = Color Picker | Option 39 = Power Actions (Restart/Shutdown/Sleep/Hibernate)
' Mumbai Edition - Feb 2026

Option Explicit
Dim WShell, FSO, choice, subchoice, cmd, title
Set WShell = CreateObject("WScript.Shell")
Set FSO    = CreateObject("Scripting.FileSystemObject")

title = "HackBugs PC Advanced Toolkit v3 (2026) - Mumbai"

Do
    choice = InputBox( _
        "=== BASIC TOOLS ===" & vbCrLf & _
        "1  Defender (General)" & vbCrLf & _
        "2  Disk Cleanup" & vbCrLf & _
        "3  System Info" & vbCrLf & _
        "4  Event Viewer" & vbCrLf & _
        "5  Services" & vbCrLf & _
        "6  Device Manager" & vbCrLf & _
        "7  Task Manager" & vbCrLf & _
        "8  Power & Sleep (modern)" & vbCrLf & _
        "9  Windows Update" & vbCrLf & _
        "10 Storage Sense" & vbCrLf & _
        "" & vbCrLf & _
        "=== SETTINGS ===" & vbCrLf & _
        "11 Network" & vbCrLf & _
        "12 Display" & vbCrLf & _
        "13 Sound" & vbCrLf & _
        "14 Apps & Features" & vbCrLf & _
        "15 Startup Apps" & vbCrLf & _
        "16 Power Options (classic + fallback)" & vbCrLf & _
        "17 CMD / PowerShell (choose)" & vbCrLf & _
        "18 Env Variables" & vbCrLf & _
        "19 Control Panel" & vbCrLf & _
        "" & vbCrLf & _
        "=== ADVANCED ===" & vbCrLf & _
        "20 DISM Check" & vbCrLf & _
        "21 Firewall Adv" & vbCrLf & _
        "22 Local Users (Pro)" & vbCrLf & _
        "23 Win Features" & vbCrLf & _
        "24 Certificates" & vbCrLf & _
        "25 GodMode" & vbCrLf & _
        "26 Comp Management" & vbCrLf & _
        "27 Registry" & vbCrLf & _
        "28 Group Policy (Pro)" & vbCrLf & _
        "29 BitLocker" & vbCrLf & _
        "30 Credentials" & vbCrLf & _
        "31 Date & Time" & vbCrLf & _
        "32 Virus & Threat" & vbCrLf & _
        "33 Sound Classic" & vbCrLf & _
        "34 Perf Monitor" & vbCrLf & _
        "35 Resource Mon" & vbCrLf & _
        "36 Notepad (Norm/Admin)" & vbCrLf & _
        "37 Open Browser (choose)" & vbCrLf & _
        "38 Color Picker (choose)" & vbCrLf & _
        "39 Power Actions (Restart/Shutdown/Sleep)" & vbCrLf & _
        "" & vbCrLf & _
        "Enter 1-39 or Cancel:", title, "")

    If choice = "" Then Exit Do

    cmd = ""

    Select Case Trim(choice)
        Case "1"    
            cmd = "%ProgramFiles%\Windows Defender\MSASCui.exe"
            If Not FSO.FileExists(WShell.ExpandEnvironmentStrings(cmd)) Then cmd = "windowsdefender://"
            If Not FSO.FileExists(WShell.ExpandEnvironmentStrings(cmd)) Then cmd = "ms-settings:windowsdefender"

        Case "2"    cmd = "cleanmgr"
        Case "3"    cmd = "msinfo32"
        Case "4"    cmd = "eventvwr.msc"
        Case "5"    cmd = "services.msc"
        Case "6"    cmd = "devmgmt.msc"
        Case "7"    cmd = "taskmgr"
        Case "8"    cmd = "ms-settings:powersleep"

        Case "9"    cmd = "ms-settings:windowsupdate"
        Case "10"   cmd = "ms-settings:storagesense"
        Case "11"   cmd = "ms-settings:network"
        Case "12"   cmd = "ms-settings:display"
        Case "13"   cmd = "ms-settings:sound"
        Case "14"   cmd = "ms-settings:appsfeatures"
        Case "15"   cmd = "ms-settings:startupapps"

        Case "16"   
            cmd = "powercfg.cpl"
            On Error Resume Next
            WShell.Run cmd, 1, False
            If Err.Number <> 0 Then
                cmd = "ms-settings:powersleep"
                WShell.Run cmd, 1, False
                MsgBox "Classic Power Options failed." & vbCrLf & vbCrLf & _
                       "Opened modern Power & sleep instead." & vbCrLf & vbCrLf & _
                       "Tip: Run in admin CMD: powercfg -restoredefaultschemes", vbExclamation, title
            End If
            On Error GoTo 0
            cmd = ""

        Case "17"   
            subchoice = InputBox("Terminal Options:" & vbCrLf & vbCrLf & _
                                 "1 = Command Prompt (normal)" & vbCrLf & _
                                 "2 = Command Prompt as Admin" & vbCrLf & _
                                 "3 = PowerShell (normal)" & vbCrLf & _
                                 "4 = PowerShell as Admin" & vbCrLf & vbCrLf & _
                                 "Enter 1-4:", title, "1")
            
            If subchoice = "" Then 
                cmd = ""
            Else
                Select Case Trim(subchoice)
                    Case "1"   cmd = "cmd.exe"
                    Case "2"   cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process cmd -Verb RunAs"""
                    Case "3"   cmd = "powershell.exe"
                    Case "4"   cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process powershell -Verb RunAs"""
                    Case Else  MsgBox "Invalid (1-4 only).", vbExclamation, title : cmd = ""
                End Select
            End If

        Case "18"   cmd = "rundll32.exe sysdm.cpl,EditEnvironmentVariables"
        Case "19"   cmd = "control"

        Case "20"   
            WShell.Run "cmd.exe /k ""echo DISM Health... && DISM /Online /Cleanup-Image /CheckHealth && DISM /Online /Cleanup-Image /ScanHealth && DISM /Online /Cleanup-Image /RestoreHealth && pause"" ", 1, False
            cmd = ""

        Case "21"   cmd = "wf.msc"
        Case "22"   cmd = "lusrmgr.msc"
        Case "23"   cmd = "optionalfeatures"
        Case "24"   cmd = "certmgr.msc"
        Case "25"   cmd = "explorer.exe shell:::{ED7BA470-8E54-465E-825C-99712043E01C}"
        Case "26"   cmd = "compmgmt.msc"
        Case "27"   cmd = "regedit"
        Case "28"   cmd = "gpedit.msc"
        Case "29"   
            cmd = "control.exe /name Microsoft.BitLockerDriveEncryption"
            On Error Resume Next
            WShell.Run cmd, 1, False
            If Err.Number <> 0 Then
                cmd = "ms-settings:devicencryption"
                WShell.Run cmd, 1, False
                MsgBox "BitLocker GUI not opened (Home?)" & vbCrLf & "Opened Device Encryption instead." & vbCrLf & _
                       "Tip: Search 'Manage BitLocker' or cmd: manage-bde -status", vbInformation, title
            End If
            On Error GoTo 0
            cmd = ""

        Case "30"   cmd = "control keymgr.dll"
        Case "31"   cmd = "timedate.cpl"

        Case "32"   
            Dim tCommand
            tCommand = WShell.ExpandEnvironmentStrings("%ProgramFiles%\Windows Defender\MSASCui.exe")
            If Not (FSO.FileExists(tCommand)) Then tCommand = "windowsdefender://Threatsettings"
            CreateObject("Shell.Application").ShellExecute(tCommand)
            cmd = ""

        Case "33"   cmd = "mmsys.cpl"
        Case "34"   cmd = "perfmon.msc"
        Case "35"   cmd = "resmon"

        Case "36"   
            subchoice = InputBox("Notepad:" & vbCrLf & "1 = Normal" & vbCrLf & "2 = As Admin", title, "1")
            If subchoice = "1" Then cmd = "notepad"
            If subchoice = "2" Then cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process notepad -Verb runas"""
            If subchoice <> "1" And subchoice <> "2" Then cmd = ""

        Case "37"   
            Dim browserChoice
            browserChoice = InputBox("Choose Browser:" & vbCrLf & vbCrLf & _
                                     "1 = Microsoft Edge" & vbCrLf & _
                                     "2 = Google Chrome" & vbCrLf & _
                                     "3 = Mozilla Firefox" & vbCrLf & _
                                     "4 = Opera" & vbCrLf & _
                                     "5 = Brave" & vbCrLf & vbCrLf & _
                                     "Enter 1-5:", title, "1")
            
            If browserChoice = "" Then 
                cmd = ""
            Else
                Select Case Trim(browserChoice)
                    Case "1"   cmd = "msedge.exe"
                    Case "2"   
                        Dim chromePath : chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
                        If FSO.FileExists(chromePath) Then cmd = """" & chromePath & """" Else MsgBox "Chrome not found at:" & vbCrLf & chromePath, vbExclamation, title : cmd = ""
                    Case "3"   cmd = WShell.ExpandEnvironmentStrings("%ProgramFiles%\Mozilla Firefox\firefox.exe") : If Not FSO.FileExists(cmd) Then cmd = "firefox.exe"
                    Case "4"   cmd = WShell.ExpandEnvironmentStrings("%ProgramFiles%\Opera\opera.exe") : If Not FSO.FileExists(cmd) Then cmd = "opera.exe"
                    Case "5"   cmd = WShell.ExpandEnvironmentStrings("%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe") : If Not FSO.FileExists(cmd) Then cmd = "brave.exe"
                    Case Else  MsgBox "Invalid (1-5 only).", vbExclamation, title : cmd = ""
                End Select
            End If

        Case "38"   
            subchoice = InputBox("Color Picker Options:" & vbCrLf & vbCrLf & _
                                 "1 = PowerToys Color Picker (best - Win+Shift+C)" & vbCrLf & _
                                 "2 = Snipping Tool Color Picker (Win+Shift+S → eyedropper)" & vbCrLf & _
                                 "3 = Colors Settings page (theme/accent)" & vbCrLf & vbCrLf & _
                                 "Enter 1-3:", title, "1")
            
            If subchoice = "" Then 
                cmd = ""
            Else
                Select Case Trim(subchoice)
                    Case "1"   
                        MsgBox "Best way: Press Win + Shift + C" & vbCrLf & vbCrLf & _
                               "If PowerToys not installed → get from Microsoft Store or winget install Microsoft.PowerToys", vbInformation, title
                        cmd = ""

                    Case "2"   
                        cmd = "snippingtool.exe"
                        MsgBox "Press Win + Shift + S → click eyedropper icon on toolbar", vbInformation, title

                    Case "3"   cmd = "ms-settings:colors"

                    Case Else  MsgBox "Invalid (1-3 only).", vbExclamation, title : cmd = ""
                End Select
            End If

        Case "39"   ' Power Actions: Restart / Shutdown / Sleep / Hibernate
            subchoice = InputBox("Power Actions:" & vbCrLf & vbCrLf & _
                                 "1 = Restart (normal)" & vbCrLf & _
                                 "2 = Restart (force - no warning)" & vbCrLf & _
                                 "3 = Shut Down (normal)" & vbCrLf & _
                                 "4 = Shut Down (force - no warning)" & vbCrLf & _
                                 "5 = Sleep" & vbCrLf & _
                                 "6 = Hibernate (if enabled)" & vbCrLf & vbCrLf & _
                                 "Enter 1-6 (or Cancel):", title, "1")
            
            If subchoice = "" Then 
                cmd = ""
            Else
                Select Case Trim(subchoice)
                    Case "1"   cmd = "shutdown /r /t 0"                  ' Restart normal
                    Case "2"   cmd = "shutdown /r /f /t 0"               ' Restart force
                    Case "3"   cmd = "shutdown /s /t 0"                  ' Shutdown normal
                    Case "4"   cmd = "shutdown /s /f /t 0"               ' Shutdown force
                    Case "5"   cmd = "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"   ' Sleep
                    Case "6"   cmd = "rundll32.exe powrprof.dll,SetSuspendState 1,1,0"   ' Hibernate
                    Case Else  MsgBox "Invalid choice (1-6 only).", vbExclamation, title : cmd = ""
                End Select
            End If

        Case Else
            MsgBox "Choose 1 to 39 only!", vbExclamation, title
            cmd = ""
    End Select

    If cmd <> "" Then
        On Error Resume Next
        WShell.Run cmd, 1, False
        If Err.Number <> 0 Then
            MsgBox "Action failed!" & vbCrLf & vbCrLf & _
                   "Command: " & cmd & vbCrLf & _
                   "Error: " & Err.Description & vbCrLf & vbCrLf & _
                   "Tip: Run as admin if needed. For sleep/hibernate check power settings.", vbCritical, title
        Else
            ' No success msg for power actions (since PC will shut down/restart/sleep)
        End If
        On Error GoTo 0
    End If

Loop While True

Set WShell = Nothing
Set FSO    = Nothing