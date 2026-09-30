"""
Jan Seva Document Tool PRO  (v2)
Install:  pip install customtkinter pillow opencv-python numpy pymupdf
Optional: pip install pdf2docx   (PDF -> Word)
Run:      python JanSeva_Pro.py

PRO features are marked with a star. While PRO_LOCK = False they are all unlocked.
When you start selling, set PRO_LOCK = True and change LICENSE_SECRET (see JanSeva_Keygen.py).
"""
import os, io, csv, json, time, sys, subprocess, hmac, hashlib, uuid, re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
import cv2, numpy as np
import pymupdf as fitz
from PIL import Image, ImageTk, ImageDraw, ImageFont

APP = "Jan Seva Document Tool PRO"
SHOP_NAME = "Jan Seva Kendra"                 # used in the default watermark text
PRO_LOCK = False                              # True = PRO features need a license key
LICENSE_SECRET = "CHANGE-THIS-SECRET-BEFORE-SELLING"   # must match JanSeva_Keygen.py

HOME = os.path.expanduser("~")
PRESET_FILE = os.path.join(HOME, "JanSeva_Pro_presets.json")
RATES_FILE = os.path.join(HOME, "JanSeva_Pro_rates.json")
LICENSE_FILE = os.path.join(HOME, "JanSeva_Pro_license.txt")
LOG_FILE = os.path.join(HOME, "JanSeva_Pro_log.csv")
LOG_HEAD = ["Date", "Time", "Customer", "Action", "File", "Size KB", "Service", "Amount"]

# ---------------- card / photo sizes (mm) ----------------
# Aadhaar PVC, PAN, Voter ID (PVC), Driving Licence, RC smart card, ABHA, e-Shram, Ayushman,
# bank cards: all follow ISO/IEC 7810 ID-1 = 85.60 x 53.98 mm (UIDAI quotes Aadhaar PVC as 86 x 54).
CARD = {"w_mm": 85.60, "h_mm": 53.98}
DEFAULT_PRESETS = {
    "Aadhaar (85.6x54)": CARD, "PAN Card": CARD, "Voter ID": CARD,
    "ABHA Card": CARD, "E-Shram": CARD, "Ayushman Bharat": CARD,
    "RC / Driving Licence": CARD, "APAAR ID": CARD, "Labour Card": CARD,
    "Bank / ATM Card": CARD,
    "PVC Portrait (54x85)": {"w_mm": 53.98, "h_mm": 85.60},
    "Passport Photo (35x45)": {"w_mm": 35.0, "h_mm": 45.0},
    "Passport Photo 2x2 inch (51x51)": {"w_mm": 50.8, "h_mm": 50.8},
    "Stamp Photo (25x35)": {"w_mm": 25.0, "h_mm": 35.0},
    "Stamp Photo Small (20x25)": {"w_mm": 20.0, "h_mm": 25.0},
    "Signature (40x20)": {"w_mm": 40.0, "h_mm": 20.0},
    "Photo 3R (89x127)": {"w_mm": 88.9, "h_mm": 127.0},
    "Photo 4x6 inch": {"w_mm": 101.6, "h_mm": 152.4},
    "Photo 5x7 inch": {"w_mm": 127.0, "h_mm": 177.8},
    "A6 (105x148)": {"w_mm": 105.0, "h_mm": 148.0},
    "A5 Document": {"w_mm": 148.0, "h_mm": 210.0},
    "A4 Full Page": {"w_mm": 210.0, "h_mm": 297.0},
}
QUICK = [("Aadhaar", "Aadhaar (85.6x54)"), ("PAN", "PAN Card"), ("Voter ID", "Voter ID"),
         ("DL / RC", "RC / Driving Licence"), ("Ayushman", "Ayushman Bharat"),
         ("Passport Photo", "Passport Photo (35x45)"), ("Stamp Photo", "Stamp Photo (25x35)"),
         ("A4 Page", "A4 Full Page")]

# Online-form presets: (width px, height px, min KB, max KB). 0 = no limit.
# Typical values only - ALWAYS check the current notification of the exam / portal.
FORM_PRESETS = {
    "Custom": (200, 230, 20, 50),
    "SSC Photo (276x354, 20-50 KB)": (276, 354, 20, 50),
    "SSC Signature (315x157, 10-20 KB)": (315, 157, 10, 20),
    "Bank Exam Photo (200x230, 20-50 KB)": (200, 230, 20, 50),
    "Bank Exam Signature (140x60, 10-20 KB)": (140, 60, 10, 20),
    "Bank Exam Left Thumb (240x240, 20-50 KB)": (240, 240, 20, 50),
    "Bank Exam Declaration (800x400, 50-100 KB)": (800, 400, 50, 100),
    "Passport Photo 35x45 mm (413x531)": (413, 531, 0, 0),
    "Passport Seva Photo (630x810)": (630, 810, 10, 200),
    "Square 2x2 inch (600x600)": (600, 600, 0, 0),
}
DEFAULT_RATES = {"Aadhaar Print": 20, "PAN Print": 20, "Passport Photo (6 pcs)": 30, "A4 Print B/W": 5,
                 "A4 Print Colour": 10, "Scan": 10, "PDF / Photo Compress": 20, "Lamination": 20,
                 "Form Filling": 100, "Other": 0}
A4 = (210, 297)


# ---------------- helpers ----------------
def mm_px(mm, dpi=300): return int(round(mm / 25.4 * dpi))


def is_card_preset(s):
    a, b = sorted((s["w_mm"], s["h_mm"]))
    return abs(a - 53.98) < 1.5 and abs(b - 85.6) < 1.5


def order_points(pts):
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")


def four_point_warp(img, pts):
    p = order_points(pts); tl, tr, br, bl = p
    W = max(1, int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))))
    H = max(1, int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))))
    dst = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], dtype="float32")
    return cv2.warpPerspective(img, cv2.getPerspectiveTransform(p, dst), (W, H))


def full_rect(img):
    h, w = img.shape[:2]
    return np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)


def auto_corners(img):
    h, w = img.shape[:2]
    sc = min(1.0, 1200 / max(h, w))
    small = cv2.resize(img, None, fx=sc, fy=sc) if sc < 1 else img.copy()
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    edges = cv2.dilate(cv2.Canny(gray, 50, 150), np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best, ba, a0 = None, 0, small.shape[0] * small.shape[1]
    for c in cnts:
        ap = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        a = cv2.contourArea(c)
        if len(ap) == 4 and a > 0.15 * a0 and a > ba:
            best, ba = ap.reshape(4, 2).astype(np.float32), a
    return best / sc if best is not None else full_rect(img)


def find_cards(img, max_cards=2):
    """ID PDF page (white background): find card-shaped blocks, front first."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = (g < 245).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    a0, res = img.shape[0] * img.shape[1], []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        r = max(w, h) / max(1, min(w, h))
        if w * h > 0.02 * a0 and 1.3 < r < 1.9:
            res.append((x, y, w, h))
    res = sorted(res, key=lambda b: b[2] * b[3], reverse=True)[:max_cards]
    res = sorted(res, key=lambda b: (b[1] // 200, b[0]))
    return [img[y:y + h, x:x + w] for x, y, w, h in res]


def enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(out, (0, 0), 2)
    return cv2.addWeighted(out, 1.5, blur, -0.5, 0)


def auto_contrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def f_gray(i): return cv2.cvtColor(cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def f_bw(i):
    g = cv2.GaussianBlur(cv2.cvtColor(i, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    bs = max(31, (min(g.shape) // 40) | 1)
    t = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bs, 15)
    return cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)


FILTERS = {"Brighten": lambda i: cv2.convertScaleAbs(i, alpha=1.1, beta=25),
           "Darken": lambda i: cv2.convertScaleAbs(i, alpha=0.9, beta=-20),
           "Grayscale": f_gray, "Black & White Scan": f_bw, "Auto Contrast": auto_contrast}


def white_bg(img):
    """Replace background with white (GrabCut). Works best on plain-background portraits."""
    h, w = img.shape[:2]
    sc = min(1.0, 700 / max(h, w))
    sm = cv2.resize(img, None, fx=sc, fy=sc) if sc < 1 else img.copy()
    mask = np.zeros(sm.shape[:2], np.uint8)
    rect = (int(sm.shape[1] * .04), int(sm.shape[0] * .03), int(sm.shape[1] * .92), int(sm.shape[0] * .96))
    cv2.grabCut(sm, mask, rect, np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.GaussianBlur(cv2.resize(m, (w, h)), (0, 0), 2)[..., None] / 255.0
    return (img * m + 255 * (1 - m)).astype(np.uint8)


def cover_crop(img, aspect):
    h, w = img.shape[:2]
    if w / h > aspect:
        nw = int(h * aspect); x = (w - nw) // 2; return img[:, x:x + nw]
    nh = int(w / aspect); y = (h - nh) // 2; return img[y:y + nh, :]


def face_crop(img, aspect):
    """Crop around the detected face so the head fills ~70% of the frame. Returns None if no face."""
    try:
        cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        h, w = img.shape[:2]; sc = min(1.0, 900 / max(h, w))
        g = cv2.cvtColor(cv2.resize(img, None, fx=sc, fy=sc) if sc < 1 else img, cv2.COLOR_BGR2GRAY)
        fs = cas.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if len(fs) == 0: return None
        x, y, fw, fh = [v / sc for v in max(fs, key=lambda f: f[2] * f[3])]
        ch = fh * 1.9; cw = ch * aspect
        if cw > w: cw = w; ch = cw / aspect
        if ch > h: ch = h; cw = ch * aspect
        left = min(max(0, x + fw / 2 - cw / 2), w - cw)
        top = min(max(0, (y - 0.3 * fh) - 0.06 * ch), h - ch)
        return img[int(top):int(top + ch), int(left):int(left + cw)]
    except Exception:
        return None


def to_pil(bgr): return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def get_font(size):
    for n in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try: return ImageFont.truetype(n, size)
        except Exception: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


def watermark(img, text):
    base = to_pil(img).convert("RGBA")
    size = max(18, base.width // 18); font = get_font(size)
    bb = ImageDraw.Draw(base).textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0] + 30, bb[3] - bb[1] + 30
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((15, 15 - bb[1]), text, font=font, fill=(110, 110, 110, 95))
    tile = tile.rotate(28, expand=True, resample=Image.BICUBIC)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sx, sy = int(tile.width * 1.1), int(tile.height * 1.6)
    for yy in range(-tile.height, base.height + tile.height, sy):
        for xx in range(-tile.width, base.width + tile.width, sx):
            layer.alpha_composite(tile, (max(0, xx), max(0, yy))) if xx >= 0 and yy >= 0 else None
    out = Image.alpha_composite(base, layer).convert("RGB")
    return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)


def jpeg_under(im, kb, allow_scale=True):
    """Smallest-loss JPEG of at most `kb` KB. allow_scale=False keeps pixel size (used for forms)."""
    scale = 1.0
    while True:
        t = im if scale == 1 else im.resize((max(50, int(im.width * scale)), max(50, int(im.height * scale))), Image.LANCZOS)
        lo, hi, best = 10, 95, None
        while lo <= hi:
            q = (lo + hi) // 2; buf = io.BytesIO(); t.save(buf, "JPEG", quality=q)
            if buf.tell() <= kb * 1024: best, lo = buf.getvalue(), q + 1
            else: hi = q - 1
        if best: return best
        if not allow_scale or scale < 0.15:
            buf = io.BytesIO(); t.save(buf, "JPEG", quality=10); return buf.getvalue()
        scale *= 0.85


def pad_jpeg(data, target_bytes):
    """Make a JPEG bigger with harmless comment segments (for portals with a MINIMUM size)."""
    need = target_bytes - len(data)
    if need <= 0: return data
    pos = 2
    if data[2:4] == b"\xff\xe0": pos = 4 + int.from_bytes(data[4:6], "big")
    filler = b""
    while need > 0:
        n = min(65533, need - 4) if need > 4 else 1
        filler += b"\xff\xfe" + (n + 2).to_bytes(2, "big") + b"\x00" * n
        need -= n + 4
    return data[:pos] + filler + data[pos:]


def open_path(p):
    try:
        if sys.platform.startswith("win"): os.startfile(p)
        elif sys.platform == "darwin": subprocess.run(["open", p])
        else: subprocess.run(["xdg-open", p])
    except Exception: pass


def print_file(p):
    try:
        if sys.platform.startswith("win"): os.startfile(p, "print")
        else: subprocess.run(["lp", p])
    except Exception as e: messagebox.showerror(APP, f"Could not print: {e}")


def ensure_log_format():
    """Upgrade an old log file (without Service/Amount columns)."""
    try:
        if not os.path.exists(LOG_FILE): return
        with open(LOG_FILE, newline="", encoding="utf8") as f: rows = list(csv.reader(f))
        if rows and "Amount" not in rows[0]:
            rows = [LOG_HEAD] + [r + ["", ""] for r in rows[1:]]
            with open(LOG_FILE, "w", newline="", encoding="utf8") as f: csv.writer(f).writerows(rows)
    except Exception: pass


def log(action, path, size_kb, customer="", service="", amount=""):
    ensure_log_format()
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        if new: w.writerow(LOG_HEAD)
        w.writerow([time.strftime("%d-%m-%Y"), time.strftime("%H:%M:%S"), customer, action, path, size_kb, service, amount])


def machine_id():
    h = f"{uuid.getnode():012X}"
    return "-".join(h[i:i + 4] for i in range(0, 12, 4))


def license_key(mid):
    d = hmac.new(LICENSE_SECRET.encode(), mid.encode(), hashlib.sha256).hexdigest()[:16].upper()
    return "-".join(d[i:i + 4] for i in range(0, 16, 4))


def parse_pages(txt, n):
    out = []
    for part in txt.replace(" ", "").split(","):
        if not part: continue
        if "-" in part:
            a, b = part.split("-", 1); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return [p - 1 for p in out if 1 <= p <= n]


# ---------------- application ----------------
class ProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light"); ctk.set_default_color_theme("blue")
        self.title(APP); self.geometry("1280x820"); self.minsize(1000, 680)
        self.items, self.idx, self.drag_i = [], -1, None
        self.presets = self.load_presets(); self.rates = self.load_rates()
        self.tk_prev = None; self.tk_sheet = None; self.tk_form = None
        self.off = (0, 0); self.sc = 1.0
        self.mask_on = False; self.mask_start = None; self.mask_id = None
        self.licensed = self.check_license()
        self.build()

    # ---------- data ----------
    def load_presets(self):
        p = dict(DEFAULT_PRESETS)
        try:
            with open(PRESET_FILE, encoding="utf8") as f: p.update(json.load(f))
        except Exception: pass
        return p

    def save_presets(self):
        with open(PRESET_FILE, "w", encoding="utf8") as f: json.dump(self.presets, f, indent=2)

    def load_rates(self):
        try:
            with open(RATES_FILE, encoding="utf8") as f: return json.load(f)
        except Exception: return dict(DEFAULT_RATES)

    def save_rates(self):
        with open(RATES_FILE, "w", encoding="utf8") as f: json.dump(self.rates, f, indent=2)

    @property
    def cur(self): return self.items[self.idx] if 0 <= self.idx < len(self.items) else None

    def say(self, msg): self.status.configure(text=msg)

    def targets(self): return list(self.items) if self.apply_all.get() else ([self.cur] if self.cur else [])

    # ---------- license ----------
    def check_license(self):
        try:
            with open(LICENSE_FILE, encoding="utf8") as f: return f.read().strip().upper() == license_key(machine_id())
        except Exception: return False

    def pro_ok(self, feature):
        if not PRO_LOCK or self.licensed: return True
        messagebox.showinfo(APP, f"'{feature}' is a PRO feature.\n\nClick 'Activate PRO' in the left panel and enter your license key.\n\nYour Machine ID:\n{machine_id()}")
        return False

    def activate(self):
        if PRO_LOCK is False: return messagebox.showinfo(APP, "PRO features are unlocked in this build.")
        key = simpledialog.askstring(APP, f"Machine ID: {machine_id()}\n\nEnter license key:")
        if key and key.strip().upper() == license_key(machine_id()):
            with open(LICENSE_FILE, "w", encoding="utf8") as f: f.write(key.strip().upper())
            self.licensed = True; self.lic_lbl.configure(text="PRO: Active")
            messagebox.showinfo(APP, "PRO activated. Thank you!")
        elif key: messagebox.showerror(APP, "Invalid license key.")

    # ---------- UI ----------
    def build(self):
        side = ctk.CTkFrame(self, width=250, corner_radius=0); side.pack(side="left", fill="y")
        ctk.CTkLabel(side, text="JAN SEVA PRO", font=("Segoe UI", 22, "bold")).pack(pady=(14, 0))
        ctk.CTkLabel(side, text="Document list", text_color="gray").pack()
        ctk.CTkButton(side, text="📂  Open Photo / PDF", height=42, command=self.open_files).pack(fill="x", padx=12, pady=10)
        self.lb = tk.Listbox(side, font=("Segoe UI", 10), activestyle="none", exportselection=False, relief="flat", bd=0)
        self.lb.pack(fill="both", expand=True, padx=12); self.lb.bind("<<ListboxSelect>>", self.on_select)
        row = ctk.CTkFrame(side, fg_color="transparent"); row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Remove", width=100, fg_color="#c0392b", hover_color="#992d22", command=self.remove).pack(side="left")
        ctk.CTkButton(row, text="Clear All", width=100, fg_color="gray", command=self.clear).pack(side="right")
        ctk.CTkLabel(side, text="Customer name (for log)").pack(anchor="w", padx=12)
        self.cust = ctk.CTkEntry(side); self.cust.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(side, text="Service  /  Amount (₹)").pack(anchor="w", padx=12)
        r = ctk.CTkFrame(side, fg_color="transparent"); r.pack(fill="x", padx=12)
        self.svc = ctk.CTkComboBox(r, values=list(self.rates), width=135, command=self.on_service); self.svc.set(list(self.rates)[0])
        self.svc.pack(side="left"); self.amt = ctk.CTkEntry(r, width=70); self.amt.pack(side="right")
        self.on_service(self.svc.get())
        r2 = ctk.CTkFrame(side, fg_color="transparent"); r2.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(r2, text="💰 Save Payment", width=120, fg_color="#27ae60", hover_color="#1e8449", command=self.save_payment).pack(side="left")
        ctk.CTkButton(r2, text="Save Rate", width=80, fg_color="gray", command=self.save_rate).pack(side="right")
        self.lic_lbl = ctk.CTkLabel(side, text=("PRO: Active" if (self.licensed or not PRO_LOCK) else "FREE version"), text_color="gray")
        self.lic_lbl.pack()
        if PRO_LOCK: ctk.CTkButton(side, text="🔑 Activate PRO", fg_color="gray", command=self.activate).pack(fill="x", padx=12, pady=(2, 12))
        else: ctk.CTkLabel(side, text="(all PRO tools unlocked)", text_color="gray").pack(pady=(0, 12))

        main = ctk.CTkFrame(self, fg_color="transparent"); main.pack(side="right", fill="both", expand=True)
        self.tabs = ctk.CTkTabview(main); self.tabs.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        self.T = ["✂ Crop / Scan", "🖨 Print Sheet", "🗜 KB Compress", "🎓 Form Photo", "📄 PDF Tools", "📋 Log & Report"]
        for t in self.T: self.tabs.add(t)
        self.status = ctk.CTkLabel(main, anchor="w", text="Step 1: Click 'Open Photo / PDF' on the left.", font=("Segoe UI", 13))
        self.status.pack(fill="x", padx=14, pady=6)
        self.tab_crop(self.tabs.tab(self.T[0])); self.tab_sheet(self.tabs.tab(self.T[1])); self.tab_comp(self.tabs.tab(self.T[2]))
        self.tab_form(self.tabs.tab(self.T[3])); self.tab_pdf(self.tabs.tab(self.T[4])); self.tab_log(self.tabs.tab(self.T[5]))

    def btn(self, parent, text, cmd, **kw):
        b = ctk.CTkButton(parent, text=text, command=cmd, height=34, **kw); b.pack(side="left", padx=3, pady=3); return b

    def tab_crop(self, t):
        q = ctk.CTkFrame(t, fg_color="transparent"); q.pack(fill="x")
        ctk.CTkLabel(q, text="One click:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(4, 2))
        for label, name in QUICK:
            if name in self.presets: self.btn(q, label, lambda n=name: self.quick(n), width=88, fg_color="#2980b9", hover_color="#1f618d")
        r1 = ctk.CTkFrame(t, fg_color="transparent"); r1.pack(fill="x")
        ctk.CTkLabel(r1, text="Size Preset:").pack(side="left", padx=(4, 0))
        self.pre = ctk.CTkComboBox(r1, values=list(self.presets), width=230, state="readonly", command=self.on_preset)
        self.pre.set(list(self.presets)[0]); self.pre.pack(side="left", padx=3)
        self.btn(r1, "+ New Preset", self.new_preset, width=110, fg_color="gray")
        self.apply_all = ctk.CTkCheckBox(r1, text="Apply to all documents"); self.apply_all.pack(side="left", padx=10)
        self.btn(r1, "⚡ Auto Crop + Size (All)", lambda: self.run_preset(self.pre.get(), True), width=190, fg_color="#27ae60", hover_color="#1e8449")
        r2 = ctk.CTkFrame(t, fg_color="transparent"); r2.pack(fill="x")
        self.btn(r2, "1. Find Corners", self.detect, width=120)
        self.btn(r2, "2. Straighten + Fit Size", self.apply_crop, width=170)
        self.btn(r2, "⟲", lambda: self.rotate(cv2.ROTATE_90_COUNTERCLOCKWISE), width=40, fg_color="gray")
        self.btn(r2, "⟳", lambda: self.rotate(cv2.ROTATE_90_CLOCKWISE), width=40, fg_color="gray")
        self.btn(r2, "✨ Sharpen", self.do_enhance, width=100, fg_color="gray")
        self.btn(r2, "✍ Signature", self.add_sign, width=100, fg_color="gray")
        self.btn(r2, "↩ Undo", self.undo, width=70, fg_color="#e67e22", hover_color="#ca6f1e")
        self.btn(r2, "Reset", self.reset, width=70, fg_color="#e67e22", hover_color="#ca6f1e")
        r3 = ctk.CTkFrame(t, fg_color="transparent"); r3.pack(fill="x")
        self.btn(r3, "🪪 ID PDF: Split Front + Back", self.split_id, width=210, fg_color="#8e44ad", hover_color="#71368a")
        self.flt = ctk.CTkComboBox(r3, values=list(FILTERS), width=160, state="readonly"); self.flt.set("Black & White Scan"); self.flt.pack(side="left", padx=3)
        self.btn(r3, "⭐ Apply Filter", self.apply_filter, width=110, fg_color="#16a085", hover_color="#117a65")
        self.mask_btn = self.btn(r3, "⭐ Mask Box: OFF", self.toggle_mask, width=140, fg_color="#16a085", hover_color="#117a65")
        self.btn(r3, "⭐ Mask Aadhaar No.", self.auto_mask, width=150, fg_color="#16a085", hover_color="#117a65")
        self.btn(r3, "⭐ Watermark", self.do_watermark, width=110, fg_color="#16a085", hover_color="#117a65")
        self.btn(r3, "⭐ White BG", self.do_white_bg, width=100, fg_color="#16a085", hover_color="#117a65")
        self.cv = tk.Canvas(t, bg="#2b2b2b", highlightthickness=0); self.cv.pack(fill="both", expand=True, pady=4)
        self.cv.bind("<Button-1>", self.on_press); self.cv.bind("<B1-Motion>", self.on_drag)
        self.cv.bind("<ButtonRelease-1>", self.on_release); self.cv.bind("<Configure>", lambda e: self.show())

    def tab_sheet(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x")
        ctk.CTkLabel(f, text="Copies (per document):").pack(side="left", padx=4)
        self.copies = ctk.CTkEntry(f, width=50); self.copies.insert(0, "1"); self.copies.pack(side="left")
        for n in (1, 2, 4, 6, 8, 12):
            ctk.CTkButton(f, text=str(n), width=34, fg_color="gray", command=lambda n=n: (self.copies.delete(0, "end"), self.copies.insert(0, str(n)))).pack(side="left", padx=2)
        ctk.CTkLabel(f, text="Gap mm:").pack(side="left", padx=(12, 2))
        self.gap = ctk.CTkEntry(f, width=50); self.gap.insert(0, "4"); self.gap.pack(side="left")
        self.border = ctk.CTkCheckBox(f, text="Cutting line"); self.border.select(); self.border.pack(side="left", padx=12)
        f2 = ctk.CTkFrame(t, fg_color="transparent"); f2.pack(fill="x", pady=4)
        self.which = ctk.CTkSegmentedButton(f2, values=["All documents", "Selected only"]); self.which.set("All documents"); self.which.pack(side="left", padx=6)
        self.layout_mode = ctk.CTkSegmentedButton(f2, values=["Card layout", "Full A4 page"]); self.layout_mode.set("Card layout"); self.layout_mode.pack(side="left", padx=6)
        g = ctk.CTkFrame(t, fg_color="transparent"); g.pack(fill="x", pady=6)
        self.btn(g, "👁 Preview", self.sheet_preview, width=100, fg_color="gray")
        self.btn(g, "💾 PDF", lambda: self.sheet_export("pdf"), width=80)
        self.btn(g, "💾 JPG", lambda: self.sheet_export("jpg"), width=80)
        self.btn(g, "💾 PNG", lambda: self.sheet_export("png"), width=80)
        self.btn(g, "🖨 Print Now", self.sheet_print, width=130, fg_color="#27ae60", hover_color="#1e8449")
        ctk.CTkLabel(t, text="Tip: keep Aadhaar front + back both in the list - they print together on one A4 page. 'Full A4 page' prints certificates / forms one per page.", text_color="gray").pack(anchor="w", padx=6)
        self.sv = tk.Canvas(t, bg="#ddd", highlightthickness=0); self.sv.pack(fill="both", expand=True, pady=4)

    def tab_comp(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x", pady=6)
        ctk.CTkLabel(f, text="Maximum size (KB):", font=("Segoe UI", 14)).pack(side="left", padx=4)
        self.kb = ctk.CTkEntry(f, width=90); self.kb.insert(0, "50"); self.kb.pack(side="left")
        for k in (20, 50, 100, 200, 500, 1024):
            ctk.CTkButton(f, text=f"{k} KB" if k < 1024 else "1 MB", width=62, fg_color="gray", command=lambda k=k: (self.kb.delete(0, "end"), self.kb.insert(0, str(k)))).pack(side="left", padx=2)
        g = ctk.CTkFrame(t, fg_color="transparent"); g.pack(fill="x")
        self.btn(g, "Selected document → JPG (exact KB)", self.comp_image, width=280)
        self.btn(g, "All documents → one PDF (exact KB)", self.comp_pdf_items, width=270)
        self.btn(g, "Pick a PDF → make it smaller", self.comp_pdf_file, width=230, fg_color="gray")
        ctk.CTkLabel(t, text="Quality is adjusted automatically to fit the KB limit - no need to try again and again.", text_color="gray").pack(anchor="w", padx=6, pady=8)

    def tab_form(self, t):
        ctk.CTkLabel(t, text="Online form photo / signature: exact pixels + KB range.  Sizes below are typical - always check the current notification.", text_color="gray").pack(anchor="w", padx=6)
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x", pady=4)
        ctk.CTkLabel(f, text="Preset:").pack(side="left", padx=4)
        self.fp = ctk.CTkComboBox(f, values=list(FORM_PRESETS), width=330, state="readonly", command=self.on_form_preset); self.fp.set("Custom"); self.fp.pack(side="left")
        f2 = ctk.CTkFrame(t, fg_color="transparent"); f2.pack(fill="x", pady=4)
        self.fe = {}
        for key, lab, val in (("w", "Width px", 200), ("h", "Height px", 230), ("mn", "Min KB", 20), ("mx", "Max KB (0 = no limit)", 50)):
            ctk.CTkLabel(f2, text=lab).pack(side="left", padx=(8, 2))
            e = ctk.CTkEntry(f2, width=70); e.insert(0, str(val)); e.pack(side="left"); self.fe[key] = e
        f3 = ctk.CTkFrame(t, fg_color="transparent"); f3.pack(fill="x", pady=4)
        self.f_face = ctk.CTkCheckBox(f3, text="⭐ Smart face crop (photos)"); self.f_face.pack(side="left", padx=8)
        self.f_white = ctk.CTkCheckBox(f3, text="⭐ White background"); self.f_white.pack(side="left", padx=8)
        self.btn(f3, "Make JPG from selected document", self.form_make, width=260, fg_color="#27ae60", hover_color="#1e8449")
        self.form_info = ctk.CTkLabel(t, text="", anchor="w", font=("Segoe UI", 13)); self.form_info.pack(fill="x", padx=8)
        self.fv = tk.Canvas(t, bg="#ddd", highlightthickness=0); self.fv.pack(fill="both", expand=True, pady=4)

    def tab_pdf(self, t):
        items = [("PDF Merge (many PDFs → one)", self.pdf_merge, 0), ("Photos → PDF", self.imgs_to_pdf, 0),
                 ("PDF → Photos (JPG)", self.pdf_to_imgs, 0), ("PDF → Word", self.pdf_to_word, 0),
                 ("PDF Print Now", self.pick_print, 0),
                 ("⭐ Unlock PDF (remove password)", self.pdf_unlock, 1), ("⭐ Protect PDF (add password)", self.pdf_protect, 1),
                 ("⭐ Split PDF (one file per page)", self.pdf_split, 1), ("⭐ Extract Pages (e.g. 1-3,5)", self.pdf_extract, 1),
                 ("⭐ Save All Documents as Files", self.save_all_files, 1)]
        g = ctk.CTkFrame(t, fg_color="transparent"); g.pack(pady=10)
        for i, (txt, fn, pro) in enumerate(items):
            ctk.CTkButton(g, text=txt, height=46, width=320, command=fn, fg_color=("#16a085" if pro else None)).grid(row=i // 2, column=i % 2, padx=8, pady=6)

    def tab_log(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x")
        self.btn(f, "Refresh", self.refresh_log, width=80)
        self.btn(f, "⭐ Today's Report", lambda: self.report("day"), width=140, fg_color="#16a085", hover_color="#117a65")
        self.btn(f, "⭐ This Month", lambda: self.report("month"), width=120, fg_color="#16a085", hover_color="#117a65")
        self.btn(f, "Open CSV (Excel)", lambda: open_path(LOG_FILE), width=150, fg_color="gray")
        self.logbox = ctk.CTkTextbox(t, font=("Consolas", 12)); self.logbox.pack(fill="both", expand=True, pady=6); self.refresh_log()

    # ---------- log / payments / reports ----------
    def refresh_log(self):
        self.logbox.delete("1.0", "end")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, encoding="utf8") as f: self.logbox.insert("end", "".join(f.readlines()[-200:][::-1]))
        else: self.logbox.insert("end", "Nothing exported yet.")

    def on_service(self, name):
        self.amt.delete(0, "end"); self.amt.insert(0, str(self.rates.get(name, 0)))

    def save_rate(self):
        try: self.rates[self.svc.get().strip()] = float(self.amt.get())
        except Exception: return messagebox.showerror(APP, "Enter a valid amount.")
        self.save_rates(); self.svc.configure(values=list(self.rates)); self.say("Rate saved.")

    def save_payment(self):
        try: a = float(self.amt.get())
        except Exception: return messagebox.showerror(APP, "Enter a valid amount.")
        log("Payment", "", "", self.cust.get(), self.svc.get(), a)
        self.say(f"Saved: ₹{a:g} for {self.svc.get()} ({self.cust.get() or 'no name'})"); self.refresh_log()

    def report(self, period):
        if not self.pro_ok("Reports"): return
        ensure_log_format()
        if not os.path.exists(LOG_FILE): return self.say("No data yet.")
        now = time.localtime(); rows = []
        with open(LOG_FILE, newline="", encoding="utf8") as f:
            for r in csv.DictReader(f):
                try: d = time.strptime(r["Date"], "%d-%m-%Y")
                except Exception: continue
                if (period == "day" and d[:3] == now[:3]) or (period == "month" and d[:2] == now[:2]): rows.append(r)
        pays = [r for r in rows if r["Action"] == "Payment"]
        tot, by = 0.0, {}
        for r in pays:
            try: a = float(r["Amount"])
            except Exception: continue
            tot += a; by[r["Service"]] = by.get(r["Service"], 0) + a
        title = time.strftime("Today: %d-%m-%Y") if period == "day" else time.strftime("Month: %B %Y")
        lines = [f"===== {title} =====", f"Total collection : ₹{tot:g}", f"Payments entered : {len(pays)}",
                 f"Customers        : {len({r['Customer'] for r in pays if r['Customer']})}",
                 f"Files exported   : {len([r for r in rows if r['Action'] not in ('Payment',)])}", "", "By service:"]
        lines += [f"  {k:<28} ₹{v:g}" for k, v in sorted(by.items(), key=lambda x: -x[1])]
        self.logbox.delete("1.0", "end"); self.logbox.insert("end", "\n".join(lines))

    # ---------- items ----------
    def new_item(self, name, img, pdf=False):
        return {"name": name, "orig": img.copy(), "img": img, "corners": auto_corners(img), "preset": None, "hist": [], "pdf": pdf, "prefit": None}

    def add_item(self, name, img, pdf=False):
        self.items.append(self.new_item(name, img, pdf)); self.lb.insert("end", name); self.select(len(self.items) - 1)

    def rebuild_list(self):
        self.lb.delete(0, "end")
        for c in self.items: self.lb.insert("end", c["name"])

    def select(self, i):
        self.idx = i; self.lb.selection_clear(0, "end"); self.lb.selection_set(i); self.show()

    def on_select(self, _):
        s = self.lb.curselection()
        if s: self.idx = s[0]; self.show()

    def remove(self):
        if self.cur is None: return
        del self.items[self.idx]; self.lb.delete(self.idx); self.idx = min(self.idx, len(self.items) - 1)
        if self.idx >= 0: self.select(self.idx)
        else: self.cv.delete("all")

    def clear(self):
        self.items.clear(); self.lb.delete(0, "end"); self.idx = -1; self.cv.delete("all")

    def open_pdf(self, p):
        base = os.path.basename(p)
        try:
            doc = fitz.open(p)
            if doc.needs_pass:
                pw = simpledialog.askstring(APP, f"Password for {base}\n(Aadhaar PDF: first 4 letters of name in CAPITALS + birth year)", show="*")
                if not pw or not doc.authenticate(pw): messagebox.showerror(APP, "Wrong password."); return None
            return doc
        except Exception as e:
            messagebox.showerror(APP, f"Could not open PDF: {e}"); return None

    def open_files(self):
        ps = filedialog.askopenfilenames(filetypes=[("Photo / PDF", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.pdf")])
        for p in ps:
            base = os.path.basename(p)
            if p.lower().endswith(".pdf"):
                doc = self.open_pdf(p)
                if doc is None: continue
                for n, pg in enumerate(doc):
                    pix = pg.get_pixmap(dpi=300)
                    arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
                    self.add_item(f"{base} p{n + 1}", bgr, pdf=True)
            else:
                img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
                if img is None: messagebox.showerror(APP, f"Could not open {base}."); continue
                self.add_item(base, img)
        if ps: self.say("Step 2: click a document type (Aadhaar, PAN, ...) - it is cropped and set to the exact size automatically.")

    # ---------- crop tab ----------
    def push(self, c=None):
        c = c or self.cur; c["hist"].append((c["img"].copy(), c["corners"].copy(), c["preset"])); c["hist"] = c["hist"][-10:]

    def edit(self, c):
        self.push(c); c["prefit"] = None

    def show(self):
        c = self.cur
        if c is None: return
        self.cv.update_idletasks()
        W, H = max(300, self.cv.winfo_width()), max(300, self.cv.winfo_height())
        pil = to_pil(c["img"]); pil.thumbnail((W - 20, H - 20), Image.LANCZOS)
        self.tk_prev = ImageTk.PhotoImage(pil); self.cv.delete("all")
        x, y = (W - pil.width) // 2, (H - pil.height) // 2
        self.cv.create_image(x, y, anchor="nw", image=self.tk_prev)
        self.off, self.sc = (x, y), pil.width / c["img"].shape[1]
        if self.mask_on: return
        pts = [(x + p[0] * self.sc, y + p[1] * self.sc) for p in order_points(c["corners"])]
        for a, b in zip(pts, pts[1:] + pts[:1]): self.cv.create_line(*a, *b, fill="#2ecc71", width=2)
        for p in c["corners"]:
            cx, cy = x + p[0] * self.sc, y + p[1] * self.sc
            self.cv.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="red", outline="white", width=2)

    def nearest(self, x, y):
        if self.cur is None: return None
        best, bd = None, 20
        for i, p in enumerate(self.cur["corners"]):
            d = ((x - self.off[0] - p[0] * self.sc) ** 2 + (y - self.off[1] - p[1] * self.sc) ** 2) ** .5
            if d < bd: best, bd = i, d
        return best

    def on_press(self, e):
        if self.mask_on: self.mask_start = (e.x, e.y); self.mask_id = None
        else: self.drag_i = self.nearest(e.x, e.y)

    def on_drag(self, e):
        if self.mask_on:
            if self.mask_start:
                if self.mask_id: self.cv.delete(self.mask_id)
                self.mask_id = self.cv.create_rectangle(*self.mask_start, e.x, e.y, outline="yellow", width=2, dash=(4, 2))
            return
        c = self.cur
        if c is None or self.drag_i is None: return
        h, w = c["img"].shape[:2]; c["prefit"] = None
        c["corners"][self.drag_i] = [max(0, min(w - 1, (e.x - self.off[0]) / self.sc)), max(0, min(h - 1, (e.y - self.off[1]) / self.sc))]
        self.show()

    def on_release(self, e):
        if not (self.mask_on and self.mask_start and self.cur is not None): return
        x0, y0 = self.mask_start; self.mask_start = None; c = self.cur
        h, w = c["img"].shape[:2]
        ix = lambda x: int(max(0, min(w - 1, (x - self.off[0]) / self.sc)))
        iy = lambda y: int(max(0, min(h - 1, (y - self.off[1]) / self.sc)))
        a, b, cc, d = min(ix(x0), ix(e.x)), min(iy(y0), iy(e.y)), max(ix(x0), ix(e.x)), max(iy(y0), iy(e.y))
        if cc - a > 3 and d - b > 3:
            self.edit(c); cv2.rectangle(c["img"], (a, b), (cc, d), (0, 0, 0), -1)
        self.show()

    def detect(self):
        c = self.cur
        if c: c["prefit"] = None; c["corners"] = auto_corners(c["img"]); self.show(); self.say("Corners found. Drag the red dots to fix them, then click '2. Straighten + Fit Size'.")

    def fit_preset(self, img, name):
        s = self.presets[name]; tw, th = mm_px(s["w_mm"]), mm_px(s["h_mm"])
        if (img.shape[1] > img.shape[0]) != (tw > th): img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        if abs((img.shape[1] / img.shape[0]) / (tw / th) - 1) > 0.12: img = cover_crop(img, tw / th)   # avoid stretching
        return cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA if img.shape[1] > tw else cv2.INTER_CUBIC)

    def process(self, c, name):
        """Straighten + fit one document to a preset (keeps the high-res version so the preset can be changed later)."""
        self.push(c)
        warped = c["prefit"] if (c["preset"] is not None and c["prefit"] is not None) else four_point_warp(c["img"], c["corners"])
        c["prefit"] = warped; c["img"] = self.fit_preset(warped, name); c["preset"] = name; c["corners"] = full_rect(c["img"])

    def auto_fit(self, c, name):
        """Returns the list of items that replace `c` (an ID PDF page can become Front + Back)."""
        if c["pdf"] and c["preset"] is None and is_card_preset(self.presets[name]):
            cards = find_cards(c["img"])
            if cards:
                out = []
                for i, cr in enumerate(cards):
                    n = self.new_item(f"{c['name']} {'Front' if i == 0 else 'Back'}", cr)
                    self.process(n, name); out.append(n)
                return out
        if c["preset"] is None and not c["hist"]: c["corners"] = auto_corners(c["img"]) if c["pdf"] else c["corners"]
        self.process(c, name); return [c]

    def run_preset(self, name, everything=False):
        if not self.items: return self.say("Open a photo / PDF first, then click the document type.")
        if name not in self.presets: return
        tg = {id(x) for x in (self.items if everything else self.targets())}
        if not tg: return
        keep, new = self.cur, []
        for it in self.items: new.extend(self.auto_fit(it, name) if id(it) in tg else [it])
        self.items = new; self.rebuild_list()
        pos = next((i for i, x in enumerate(self.items) if x is keep), 0)
        self.select(pos)
        n = len(tg)
        self.say(f"Done: {name}  -  exact {self.presets[name]['w_mm']:g} x {self.presets[name]['h_mm']:g} mm"
                 + (f"  ({n} documents)" if n > 1 else "") + ".  Now go to 'Print Sheet'.")

    def quick(self, name): self.pre.set(name); self.run_preset(name)

    def on_preset(self, name): self.run_preset(name)

    def apply_crop(self):
        if self.cur: self.run_preset(self.pre.get())

    def rotate(self, code):
        for c in self.targets():
            self.edit(c); c["img"] = cv2.rotate(c["img"], code); c["corners"] = full_rect(c["img"])
        self.show()

    def do_enhance(self):
        for c in self.targets(): self.edit(c); c["img"] = enhance(c["img"])
        self.show(); self.say("Sharpened.")

    def undo(self):
        c = self.cur
        if c and c["hist"]: c["img"], c["corners"], c["preset"] = c["hist"].pop(); c["prefit"] = None; self.show()

    def reset(self):
        c = self.cur
        if c: self.push(c); c["img"] = c["orig"].copy(); c["corners"] = auto_corners(c["img"]); c["preset"] = None; c["prefit"] = None; self.show()

    def add_sign(self):
        c = self.cur
        if c is None: return
        p = filedialog.askopenfilename(title="Signature image (PNG)", filetypes=[("Image", "*.png *.jpg *.jpeg")])
        if not p: return
        self.edit(c); base = to_pil(c["img"]).convert("RGBA"); sg = Image.open(p).convert("RGBA")
        sg.thumbnail((int(base.width * .28), int(base.height * .18)))
        base.alpha_composite(sg, (base.width - sg.width - 20, base.height - sg.height - 20))
        c["img"] = cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR); self.show()

    def new_preset(self):
        n = simpledialog.askstring(APP, "Preset name:")
        if not n: return
        try:
            w = float(simpledialog.askstring(APP, "Width in mm:")); h = float(simpledialog.askstring(APP, "Height in mm:"))
        except Exception: return messagebox.showerror(APP, "Enter valid numbers.")
        self.presets[n] = {"w_mm": w, "h_mm": h}; self.save_presets()
        self.pre.configure(values=list(self.presets)); self.pre.set(n)

    def split_id(self):
        c = self.cur
        if c is None: return self.say("Open the ID PDF first.")
        cards = find_cards(c["img"])
        if not cards: return self.say("No card found - use manual corners.")
        name = self.pre.get(); base = c["name"]; new = []
        for i, cr in enumerate(cards):
            n = self.new_item(f"{base} {'Front' if i == 0 else 'Back'}", cr); self.process(n, name); new.append(n)
        self.items[self.idx:self.idx + 1] = new; self.rebuild_list(); self.select(self.idx)
        self.say(f"{len(cards)} card(s) separated (Front/Back) and set to '{name}'.")

    # ---------- PRO tools on the crop tab ----------
    def apply_filter(self):
        if not self.pro_ok("Scan filters") or not self.targets(): return
        fn = FILTERS[self.flt.get()]
        for c in self.targets(): self.edit(c); c["img"] = fn(c["img"])
        self.show(); self.say(f"Filter applied: {self.flt.get()}.")

    def toggle_mask(self):
        if not self.mask_on and not self.pro_ok("Mask box"): return
        self.mask_on = not self.mask_on
        self.mask_btn.configure(text="⭐ Mask Box: ON" if self.mask_on else "⭐ Mask Box: OFF", fg_color="#c0392b" if self.mask_on else "#16a085")
        self.show(); self.say("Drag a box on the image to hide that area (black). Click the button again to finish." if self.mask_on else "Mask mode off.")

    def auto_mask(self):
        if not self.pro_ok("Mask Aadhaar number") or self.cur is None: return
        c = self.cur; h, w = c["img"].shape[:2]
        if h > w: return self.say("Aadhaar number masking works on the front side (landscape card). Rotate first.")
        self.edit(c)
        cv2.rectangle(c["img"], (int(w * .27), int(h * .79)), (int(w * .585), int(h * .93)), (0, 0, 0), -1)
        self.show(); self.say("First 8 digits masked (approximate position). CHECK the image - use Undo or 'Mask Box' to adjust.")

    def do_watermark(self):
        if not self.pro_ok("Watermark") or not self.targets(): return
        txt = simpledialog.askstring(APP, "Watermark text:", initialvalue=f"{SHOP_NAME} - Only for KYC")
        if not txt: return
        for c in self.targets(): self.edit(c); c["img"] = watermark(c["img"], txt)
        self.show(); self.say("Watermark added.")

    def do_white_bg(self):
        if not self.pro_ok("White background") or not self.targets(): return
        self.say("Working...  please wait"); self.update_idletasks()
        for c in self.targets(): self.edit(c); c["img"] = white_bg(c["img"])
        self.show(); self.say("Background made white. Check the edges; use Undo if it looks wrong.")

    # ---------- sheet ----------
    def sel_items(self):
        its = self.items if self.which.get() == "All documents" else ([self.cur] if self.cur else [])
        full = self.layout_mode.get() == "Full A4 page"; out = []
        for c in its:
            im = to_pil(c["img"])
            if full:
                bw, bh = mm_px(A4[0] - 20), mm_px(A4[1] - 20); r = min(bw / im.width, bh / im.height)
                im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
            else:
                name = c["preset"] or self.pre.get(); s = self.presets[name]
                box = (mm_px(s["w_mm"]), mm_px(s["h_mm"]))
                if c["preset"]: im = im.resize(box, Image.LANCZOS)
                else: im.thumbnail(box, Image.LANCZOS)
            out.append(im)
        return out

    def build_pages(self):
        try: n = max(1, int(self.copies.get())); gap = mm_px(float(self.gap.get()))
        except Exception: n, gap = 1, mm_px(4)
        ims = [i for i in self.sel_items() for _ in range(n)]
        if not ims: return []
        AW, AH, M = mm_px(A4[0]), mm_px(A4[1]), mm_px(10)
        pages, y, rowh = [], M, 0

        def flush(pg, rws):
            d = ImageDraw.Draw(pg)
            for ry, row in rws:
                tw = sum(i.width for i in row) + gap * (len(row) - 1); x = (AW - tw) // 2
                for i in row:
                    pg.paste(i, (x, ry))
                    if self.border.get(): d.rectangle([x - 1, ry - 1, x + i.width, ry + i.height], outline=(150, 150, 150))
                    x += i.width + gap
        cur_row, cw, pg_rows = [], 0, []

        def new_row():
            nonlocal cur_row, cw, y, rowh
            if cur_row: pg_rows.append((y, cur_row)); y += rowh + gap
            cur_row, cw, rowh = [], 0, 0
        for im in ims:
            if cur_row and cw + gap + im.width > AW - 2 * M: new_row()
            if y + im.height > AH - M and (pg_rows or not cur_row) and pg_rows:
                pg = Image.new("RGB", (AW, AH), "white"); flush(pg, pg_rows); pages.append(pg); pg_rows.clear(); y = M
            cw += im.width + (gap if cur_row else 0); cur_row.append(im); rowh = max(rowh, im.height)
        new_row(); pg = Image.new("RGB", (AW, AH), "white"); flush(pg, pg_rows); pages.append(pg)
        return pages

    def sheet_preview(self):
        pages = self.build_pages()
        if not pages: return self.say("No documents.")
        self.sv.update_idletasks(); H = max(300, self.sv.winfo_height() - 10)
        p = pages[0].copy(); p.thumbnail((2000, H)); self.tk_sheet = ImageTk.PhotoImage(p)
        self.sv.delete("all"); self.sv.create_image(self.sv.winfo_width() // 2, 5, anchor="n", image=self.tk_sheet)
        self.say(f"A4 preview (total {len(pages)} page).")

    def save_pages(self, pages, out, target_kb=None):
        ext = os.path.splitext(out)[1].lower()
        if ext == ".pdf":
            if target_kb:
                doc = fitz.open()
                for pg in pages:
                    data = jpeg_under(pg, max(5, target_kb / len(pages)))
                    page = doc.new_page(width=595, height=842); page.insert_image(page.rect, stream=data)
                doc.save(out, deflate=True); doc.close()
            else: pages[0].save(out, "PDF", resolution=300.0, save_all=True, append_images=pages[1:])
        else:
            for i, pg in enumerate(pages):
                o = out if i == 0 else out.replace(ext, f"_{i + 1}{ext}")
                if ext == ".png": pg.save(o, "PNG")
                elif target_kb: open(o, "wb").write(jpeg_under(pg, target_kb))
                else: pg.save(o, "JPEG", quality=95, dpi=(300, 300))
        log("Export", out, os.path.getsize(out) // 1024, self.cust.get())

    def sheet_export(self, fmt):
        pages = self.build_pages()
        if not pages: return self.say("No documents.")
        out = filedialog.asksaveasfilename(defaultextension="." + fmt, initialfile=f"A4_Sheet.{fmt}")
        if out: self.save_pages(pages, out); self.say("Saved: " + out); open_path(out)

    def sheet_print(self):
        pages = self.build_pages()
        if not pages: return self.say("No documents.")
        tmp = os.path.join(HOME, "JanSeva_print_tmp.pdf"); self.save_pages(pages, tmp); print_file(tmp)

    # ---------- compress ----------
    def kbval(self):
        try: return max(5, int(float(self.kb.get())))
        except Exception: messagebox.showerror(APP, "Enter a valid KB value."); return None

    def comp_image(self):
        k = self.kbval()
        if not k or self.cur is None: return
        out = filedialog.asksaveasfilename(defaultextension=".jpg", initialfile=f"{k}KB.jpg")
        if out: open(out, "wb").write(jpeg_under(to_pil(self.cur["img"]), k)); log("Compress", out, os.path.getsize(out) // 1024, self.cust.get()); self.say(f"Saved: {out} ({os.path.getsize(out) // 1024} KB)")

    def comp_pdf_items(self):
        k = self.kbval()
        if not k or not self.items: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{k}KB.pdf")
        if out: self.save_pages([to_pil(c["img"]) for c in self.items], out, k); self.say(f"Saved: {out} ({os.path.getsize(out) // 1024} KB)")

    def comp_pdf_file(self):
        k = self.kbval(); p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not k or not p: return
        doc = self.open_pdf(p)
        if doc is None: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{k}KB.pdf")
        if not out: return
        pages = []
        for pg in doc:
            pix = pg.get_pixmap(dpi=150); pages.append(Image.frombytes("RGB", (pix.w, pix.h), pix.samples))
        self.save_pages(pages, out, k); self.say(f"Saved: {out} ({os.path.getsize(out) // 1024} KB)")

    # ---------- form photo ----------
    def on_form_preset(self, name):
        w, h, mn, mx = FORM_PRESETS[name]
        for k, v in zip(("w", "h", "mn", "mx"), (w, h, mn, mx)): self.fe[k].delete(0, "end"); self.fe[k].insert(0, str(v))

    def form_make(self):
        c = self.cur
        if c is None: return self.say("Open a photo / signature first.")
        try: W, H, mn, mx = (int(float(self.fe[k].get())) for k in ("w", "h", "mn", "mx"))
        except Exception: return messagebox.showerror(APP, "Enter valid numbers.")
        if W < 20 or H < 20: return messagebox.showerror(APP, "Width / height too small.")
        if (self.f_face.get() or self.f_white.get()) and not self.pro_ok("Smart face crop / White background"): return
        src = c["img"]; note = ""
        crop = None
        if self.f_face.get():
            crop = face_crop(src, W / H)
            if crop is None: note = "  (no face found - centre crop used)"
        if crop is None: crop = cover_crop(src, W / H)
        if self.f_white.get(): crop = white_bg(crop)
        pil = to_pil(crop).resize((W, H), Image.LANCZOS)
        if mx > 0: data = jpeg_under(pil, mx * 0.97, allow_scale=False)
        else:
            buf = io.BytesIO(); pil.save(buf, "JPEG", quality=95, dpi=(300, 300)); data = buf.getvalue()
        if mn > 0 and len(data) < mn * 1024: data = pad_jpeg(data, int((mn + (mx if mx > 0 else mn * 1.5)) / 2 * 1024))
        kb = len(data) / 1024
        ok = (mx <= 0 or kb <= mx) and kb >= mn
        self.form_info.configure(text=f"Result: {W} x {H} px, {kb:.1f} KB  -  " + ("within limits" if ok else "NOT within limits, adjust values") + note)
        pv = Image.open(io.BytesIO(data)); pv.thumbnail((500, max(200, self.fv.winfo_height() - 10))); self.tk_form = ImageTk.PhotoImage(pv)
        self.fv.delete("all"); self.fv.create_image(self.fv.winfo_width() // 2, 5, anchor="n", image=self.tk_form)
        out = filedialog.asksaveasfilename(defaultextension=".jpg", initialfile=f"{W}x{H}.jpg")
        if out:
            with open(out, "wb") as f: f.write(data)
            log("FormPhoto", out, len(data) // 1024, self.cust.get()); self.say(f"Saved: {out} ({kb:.1f} KB)")

    # ---------- pdf tools ----------
    def pdf_merge(self):
        ps = filedialog.askopenfilenames(title="Pick PDFs (in order)", filetypes=[("PDF", "*.pdf")])
        if len(ps) < 2: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Merged.pdf")
        if not out: return
        m = fitz.open()
        for p in ps:
            d = self.open_pdf(p)
            if d is not None: m.insert_pdf(d)
        m.save(out); log("Merge", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("Merged: " + out)

    def imgs_to_pdf(self):
        ps = filedialog.askopenfilenames(filetypes=[("Photos", "*.jpg *.jpeg *.png *.webp *.bmp")])
        out = ps and filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Photos.pdf")
        if not out: return
        ims = [Image.open(p).convert("RGB") for p in ps]; ims[0].save(out, "PDF", resolution=200.0, save_all=True, append_images=ims[1:])
        log("Photos->PDF", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("PDF created: " + out)

    def pdf_to_imgs(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        doc = p and self.open_pdf(p)
        d = doc and filedialog.askdirectory()
        if not d: return
        for n, pg in enumerate(doc): pg.get_pixmap(dpi=200).save(os.path.join(d, f"page_{n + 1}.jpg"))
        self.say("Photos saved: " + d); open_path(d)

    def pdf_to_word(self):
        try: from pdf2docx import Converter
        except ImportError: return messagebox.showinfo(APP, "Install first:  pip install pdf2docx")
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        out = p and filedialog.asksaveasfilename(defaultextension=".docx")
        if out: c = Converter(p); c.convert(out); c.close(); self.say("Word file created: " + out); open_path(out)

    def pick_print(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: print_file(p)

    def pdf_unlock(self):
        if not self.pro_ok("Unlock PDF"): return
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        doc = p and self.open_pdf(p)
        if not doc: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=os.path.splitext(os.path.basename(p))[0] + "_unlocked.pdf")
        if out: doc.save(out, encryption=fitz.PDF_ENCRYPT_NONE); log("Unlock PDF", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("Password removed: " + out)

    def pdf_protect(self):
        if not self.pro_ok("Protect PDF"): return
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        doc = p and self.open_pdf(p)
        if not doc: return
        pw = simpledialog.askstring(APP, "New password:", show="*")
        if not pw: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=os.path.splitext(os.path.basename(p))[0] + "_protected.pdf")
        if out: doc.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=pw, owner_pw=pw); log("Protect PDF", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("Password added: " + out)

    def pdf_split(self):
        if not self.pro_ok("Split PDF"): return
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        doc = p and self.open_pdf(p)
        d = doc and filedialog.askdirectory()
        if not d: return
        base = os.path.splitext(os.path.basename(p))[0]
        for i in range(len(doc)):
            n = fitz.open(); n.insert_pdf(doc, from_page=i, to_page=i); n.save(os.path.join(d, f"{base}_page{i + 1}.pdf")); n.close()
        self.say(f"Split into {len(doc)} files: {d}"); open_path(d)

    def pdf_extract(self):
        if not self.pro_ok("Extract pages"): return
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        doc = p and self.open_pdf(p)
        if not doc: return
        txt = simpledialog.askstring(APP, f"Pages to keep (PDF has {len(doc)} pages), e.g. 1-3,5:")
        try: pages = parse_pages(txt or "", len(doc))
        except Exception: pages = []
        if not pages: return messagebox.showerror(APP, "No valid pages.")
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Extracted.pdf")
        if out: doc.select(pages); doc.save(out); log("Extract pages", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("Saved: " + out)

    def save_all_files(self):
        if not self.pro_ok("Save all documents") or not self.items: return
        d = filedialog.askdirectory(title="Where to create the customer folder?")
        if not d: return
        folder = os.path.join(d, f"{re.sub(r'[^A-Za-z0-9 _-]', '', self.cust.get()).strip() or 'Customer'}_{time.strftime('%d-%m-%Y')}")
        os.makedirs(folder, exist_ok=True)
        for c in self.items:
            fn = os.path.join(folder, re.sub(r"[^\w\-. ]", "_", os.path.splitext(c["name"])[0]) + ".jpg")
            to_pil(c["img"]).save(fn, "JPEG", quality=95, dpi=(300, 300)); log("SaveFile", fn, os.path.getsize(fn) // 1024, self.cust.get())
        self.say(f"{len(self.items)} files saved in: {folder}"); open_path(folder)


if __name__ == "__main__":
    ProApp().mainloop()
