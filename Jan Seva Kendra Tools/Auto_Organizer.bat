bat
@echo off
for %%a in (".\*") do (
    if "%%~xa" NEQ "" if /I "%%~fa" NEQ "%~f0" (
        if not exist "%%~xa" mkdir "%%~xa"
        move "%%a" "%%~xa\"
    )
)