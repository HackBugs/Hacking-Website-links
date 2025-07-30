```
netstat -sp tcp
netstat -ano | findstr ESTABLISHED
netstat -ano
tasklist | findstr <PID>

nslookup 104.26.7.247
whois 104.26.7.247


net user
net user <username> /delete

taskmgr → Startup tab
wf.msc

"%ProgramFiles%\Windows Defender\MpCmdRun.exe" -Scan -ScanType 2
"%ProgramFiles%\Microsoft Defender\MpCmdRun.exe" -Scan -ScanType 2

dir "%ProgramFiles%\Windows Defender\MpCmdRun.exe"
"%ProgramFiles%\Windows Defender\MpCmdRun.exe" -Scan -ScanType 3 -File "C:\Users\Shahnwaz Aalam\Downloads"
```

> Rescue software generally refers to tools designed for recovering lost or deleted data, repairing damaged systems, or providing remote technical support.
This can include data recovery software, system rescue tools, and remote support solutions.

> AnyDesk is primarily used for remote access to computers and other devices. It allows users to connect to and control another device from a different location,

- https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview
- https://ipinfo.io/
- https://www.abuseipdb.com/

<hr>

> ## 1. **Scammers "Rescue software"** (jaise ki TeamViewer, AnyDesk, Zoho Assist, GoToAssist, UltraViewer, LogMeIn Rescue, etc.) isliye use karte hain kyunki ye **remote access tools** hain — jinse wo aapke laptop ya PC ko **door se control kar sakte hain** — jaise aapka mouse, keyboard, screen sab kuch.

---

### 🔍 **Scammer Rescue Software Use Karne Ka Maksad:**

| 🔢  | Reason                             | Detail                                                                                           |
| --- | ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1️⃣ | **Remote Access paana**            | Aapka mouse, keyboard, desktop screen poora unke control me aajata hai.                          |
| 2️⃣ | **Bank/UPI/Wallet access dekhna**  | Jab aap bank app ya browser open karte ho, to wo sab dekh sakte hain.                            |
| 3️⃣ | **Fake "problem" dikhana**         | Wo aapke screen par fake virus ya warning dikhate hain, jisse darake paisa lein.                 |
| 4️⃣ | **File copy karna/chupke install** | Kuch log software ke zariye aapke system me .bat/.exe files daal kar backdoor create karte hain. |
| 5️⃣ | **Auto payment initiate karna**    | Aapko bolenge OTP daalo ya "verify" karo, lekin wo system se chhupke paisa transfer karte hain.  |

---

### 🔥 **Kaun Kaun Se Software Commonly Use Karte Hain Scammers:**

| Software Name  | Legit Use (Original Purpose) | Scammers Use                        |
| -------------- | ---------------------------- | ----------------------------------- |
| TeamViewer     | IT support, Remote Help      | Scam ke liye use hota hai           |
| AnyDesk        | Remote access & control      | Light weight hai, zyada popular     |
| LogMeIn Rescue | Professional helpdesk tools  | Scammers naam lete hain iska        |
| Zoho Assist    | Business remote access       | Fake tech support me use hota       |
| UltraViewer    | Free TeamViewer alternative  | India/Nepal ke scam calls me common |

---

### 🛑 **Warning Signs:**

* Agar koi **unknown person aapse Remote Access mange**.
* Aapko **OTP dene ko kahe** jab wo aapke screen pe kuch dikha rahe ho.
* Koi bole: *"Hum Microsoft se bol rahe hain"* ya *"Your system is hacked, I will fix it"*.

---

### ✅ **Protection Tips:**

1. Kabhi bhi remote software install mat karo agar **aap personally nahi jaante ho user ko.**
2. Agar kabhi galti se kisi ko access de diya ho:

   * **WiFi off karo** turant.
   * **Remote software uninstall karo**.
   * **Antivirus/Defender se full scan** karo.
   * **Passwords change karo** (Bank, Gmail, etc).
   * **Bank ko inform karo** agar account open kiya tha access ke time.

<hr>

> ## 2. **System me koi suspicious software (jaise scammer use karte hain Rescue software, remote desktop tools, ya unwanted programs)** install hain, to mai aapko **step-by-step CMD ya PowerShell se check karna sikha deta hoon**:

---

### 🔍 **1. Installed Software List Check (CMD ya PowerShell)**

Yeh check karega ki kaunse software install hain:

#### ✅ CMD me:

```cmd
wmic product get name,version
```

> ⚠️ Note: Ye command thoda slow chalega aur sabhi installed programs ki list dega.

---

### 🔍 **2. PowerShell se check (Fast & Reliable)**

PowerShell open karo as Administrator, phir ye command run karo:

```powershell
Get-WmiObject -Class Win32_Product | Select-Object Name, Version
```

Ya faster method:

```powershell
Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion
```

---

### 🔍 **3. Suspicious Remote Software ki List**

Check karo ye software installed hain ya nahi:

| 🛑 Software Name          | 🚨 Use                        |
| ------------------------- | ----------------------------- |
| **AnyDesk**               | Remote control                |
| **TeamViewer**            | Remote control                |
| **UltraViewer**           | Remote support                |
| **AeroAdmin**             | Remote access                 |
| **Ammyy Admin**           | Remote access                 |
| **Remote Utilities**      | Full remote control           |
| **LogMeIn / Rescue**      | Scammers ka common tool       |
| **DWAgent**               | Hidden remote                 |
| **Chrome Remote Desktop** | Google ka remote control tool |
| **VNC Viewer / Server**   | Screen share                  |

Agar list me inme se koi bhi hai **aapne install nahi kiya**, to ho sakta hai **aapke system me unauthorized access ho raha ho.**

---

### 🧽 **4. Remove Suspicious Programs (CMD se)**

Agar koi suspicious software milta hai, usse CMD se uninstall karne ke liye:

```cmd
wmic product where "name like '%AnyDesk%'" call uninstall
```

(Replace `AnyDesk` with the software name you want to remove.)

---

### 🔐 **5. Network Connections Check**

Check karo system pe koi suspicious connection to active nahi:

```cmd
netstat -ano
```

* Isse aapko **active ports and IP addresses** milenge.
* Last column me **PID** hota hai (e.g. 13884), use `tasklist | findstr <PID>` se identify karo ki kaunsa program chal raha hai.

---

### 🛡️ **Bonus Tip: Check Startup Programs**

PowerShell se:

```powershell
Get-CimInstance -ClassName Win32_StartupCommand | Select-Object Name, Command, Location
```
