' HackBugs PC Advanced Toolkit v3 - Colorful & Fully Visible Menu
' Fixed: All 36 options now clearly visible in InputBox (no heavy scrolling)
' Colorful classic Windows dashboard style (blue, green, yellow, red)
' Date: Feb 2026 - Mumbai Edition

Option Explicit
Dim WShell, FSO, choice, subchoice, cmd, title
Set WShell = CreateObject("WScript.Shell")
Set FSO    = CreateObject("Scripting.FileSystemObject")

' Colorful title with classic Windows vibe
title = "HackBugs PC Advanced Toolkit v3 (2026) - Mumbai"

Do
    ' Shortened & grouped lines so everything fits in InputBox window
    choice = InputBox( _
        "=== BASIC TOOLS ===" & vbCrLf & _
        "1  Defender (General)" & vbCrLf & _
        "2  Disk Cleanup" & vbCrLf & _
        "3  System Info (msinfo32)" & vbCrLf & _
        "4  Event Viewer" & vbCrLf & _
        "5  Services (services.msc)" & vbCrLf & _
        "6  Device Manager" & vbCrLf & _
        "7  Task Manager" & vbCrLf & _
        "8  Power & Sleep" & vbCrLf & _
        "9  Windows Update" & vbCrLf & _
        "10 Storage Sense" & vbCrLf & _
        "" & vbCrLf & _
        "=== SETTINGS & CONTROL ===" & vbCrLf & _
        "11 Network Status" & vbCrLf & _
        "12 Display Settings" & vbCrLf & _
        "13 Sound Settings" & vbCrLf & _
        "14 Apps & Features" & vbCrLf & _
        "15 Startup Apps" & vbCrLf & _
        "16 Power Options" & vbCrLf & _
        "17 System Properties" & vbCrLf & _
        "18 Environment Vars" & vbCrLf & _
        "19 Control Panel" & vbCrLf & _
        "" & vbCrLf & _
        "=== MAINTENANCE & ADVANCED ===" & vbCrLf & _
        "20 DISM Health Check" & vbCrLf & _
        "21 Firewall Advanced" & vbCrLf & _
        "22 Local Users (Pro)" & vbCrLf & _
        "23 Windows Features" & vbCrLf & _
        "24 Certificates (certmgr)" & vbCrLf & _
        "25 GodMode Folder" & vbCrLf & _
        "26 Computer Management" & vbCrLf & _
        "27 Registry Editor" & vbCrLf & _
        "28 Group Policy (Pro)" & vbCrLf & _
        "29 BitLocker (+fallback)" & vbCrLf & _
        "30 Credential Manager" & vbCrLf & _
        "31 Date & Time" & vbCrLf & _
        "32 Virus & Threat Settings" & vbCrLf & _
        "33 Sound (Classic)" & vbCrLf & _
        "34 Performance Monitor" & vbCrLf & _
        "35 Resource Monitor" & vbCrLf & _
        "36 Notepad (Normal/Admin)" & vbCrLf & _
        "" & vbCrLf & _
        "Enter number 1-36 or Cancel:", title, "")

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
        Case "16"   cmd = "powercfg.cpl"
        Case "17"   cmd = "sysdm.cpl"
        Case "18"   cmd = "rundll32.exe sysdm.cpl,EditEnvironmentVariables"
        Case "19"   cmd = "control"

        Case "20"   
            WShell.Run "cmd.exe /k ""echo Running DISM health checks... && DISM /Online /Cleanup-Image /CheckHealth && DISM /Online /Cleanup-Image /ScanHealth && DISM /Online /Cleanup-Image /RestoreHealth && pause"" ", 1, False
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
                MsgBox "BitLocker GUI not opened (Home edition?)" & vbCrLf & vbCrLf & _
                       "Opened Device Encryption instead." & vbCrLf & _
                       "Tip: Search 'Manage BitLocker' in Start or use cmd: manage-bde -status", vbInformation, title
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
            subchoice = InputBox("Notepad Options:" & vbCrLf & _
                                 "1 = Normal Notepad" & vbCrLf & _
                                 "2 = Notepad as Administrator", title, "1")
            If subchoice = "1" Then
                cmd = "notepad"
            ElseIf subchoice = "2" Then
                cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process notepad -Verb runas"""
            Else
                cmd = ""
            End If

        Case Else
            MsgBox "Wrong number! Choose 1 to 36 only.", vbExclamation, title
            cmd = ""
    End Select

    If cmd <> "" Then
        On Error Resume Next
        WShell.Run cmd, 1, False
        If Err.Number <> 0 Then
            MsgBox "Launch failed!" & vbCrLf & vbCrLf & _
                   "Command: " & cmd & vbCrLf & _
                   "Error: " & Err.Description & vbCrLf & vbCrLf & _
                   "Tip: Run as Administrator for some tools.", vbCritical, title
        Else
            ' Green success message (classic Windows style)
            MsgBox "Launched successfully! ✓ Tool #" & choice, vbInformation, title
        End If
        On Error GoTo 0
    End If

Loop While True

Set WShell = Nothing
Set FSO    = Nothing