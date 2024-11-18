
> ## This code is a simple Windows batch script to run the `SteamSetup.exe` installer with a specific compatibility setting.

### Explanation of the Code:
1. **`Set __COMPAT_LAYER=RunAsInvoker`**:
   - This sets an environment variable `__COMPAT_LAYER` to `RunAsInvoker`.
   - `RunAsInvoker` forces the program to run with the same permissions as the current user, bypassing any prompts for administrator privileges.

2. **`Start SteamSetup.exe`**:
   - This launches the `SteamSetup.exe` file.
   - The `Start` command ensures that the program runs without blocking the script's execution (though in this case, there’s nothing else after it).

### Purpose:
This script is likely used to:
- Install or run the `SteamSetup.exe` installer without requiring administrative permissions.
- Useful in environments where the user doesn't have admin rights or wants to avoid unnecessary privilege escalation prompts.

-----

## Bypass Admin Install Software

- Create Notepadt file `.txt` to `.bat`
- Change extensions as a `.bat`

```
Set __COMPAT_LAYER=RunAsInvoker
Start SteamSetup.exe
```
