@echo off
title Downloads Organizer
color 0A

cd /d "%~dp0"
set "self=%~nx0"

echo ==========================================
echo       DOWNLOADS FILE ORGANIZER
echo ==========================================
echo.

call :m "Videos" mp4 mkv avi mov wmv flv webm 3gp mpeg mpg m4v
call :m "Photos" jpg jpeg png gif bmp webp heic svg tiff tif ico
call :m "Documents" pdf doc docx rtf odt
call :m "Excel Files" xls xlsx csv ods
call :m "PowerPoint Files" ppt pptx odp
call :m "Txt Files" txt
call :m "Music" mp3 wav aac flac m4a ogg wma opus
call :m "Zip Files" zip rar 7z tar gz bz2 xz
call :m "Apps" exe msi appx msix apk
call :m "Web Files" html htm css js jsx ts tsx php
call :m "Script Files" bat cmd ps1 vbs sh
call :m "Programming Files" py java c cpp h hpp cs go rs
call :m "Database Files" sql db sqlite sqlite3
call :m "Data Files" json xml yaml yml toml
call :m "Disk Image Files" iso img vhd vhdx
call :m "Font Files" ttf otf woff woff2
call :m "Log Files" log
call :m "Backup Files" bak
call :m "Torrent Files" torrent
call :m "Linux Package Files" deb rpm

echo.
echo ==========================================
echo       MOVING OTHER FILES
echo ==========================================
echo.

for %%f in (*) do (
    if /i not "%%~nxf"=="%self%" (
        if /i not "%%~xf"==".crdownload" (
            if /i not "%%~xf"==".part" (
                if /i not "%%~xf"==".tmp" (
                    if not exist "Others" md "Others"
                    if not exist "Others\%%~nxf" (
                        move "%%f" "Others\" >nul
                        echo Moved to Others: %%~nxf
                    )
                )
            )
        )
    )
)

echo.
echo ==========================================
echo       ORGANIZATION COMPLETE
echo ==========================================
echo.
echo Aapka folder successfully organize ho gaya.
echo.
pause
exit /b


:m
set "d=%~1"
shift

:n
if "%~1"=="" exit /b

if exist "*.%~1" (
    if not exist "%d%" md "%d%"

    for %%f in ("*.%~1") do (
        if not exist "%d%\%%~nxf" (
            move "%%f" "%d%\" >nul
            echo Moved: %%~nxf ^> %d%
        )
    )
)

shift
goto n