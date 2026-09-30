"""
Jan Seva Document Tool PRO
Install:  pip install customtkinter pillow opencv-python numpy pymupdf
Optional: pip install pdf2docx   (PDF -> Word)
Run:      python JanSeva_Pro.py
"""
import os, io, csv, json, time, sys, subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
import cv2, numpy as np
import pymupdf as fitz
from PIL import Image, ImageTk, ImageDraw

APP = "Jan Seva Document Tool PRO"
HOME = os.path.expanduser("~")
PRESET_FILE = os.path.join(HOME, "JanSeva_Pro_presets.json")
LOG_FILE = os.path.join(HOME, "JanSeva_Pro_log.csv")
CARD = {"w_mm": 85.60, "h_mm": 53.98}
DEFAULT_PRESETS = {
    "Aadhaar (85.6x54)": CARD, "PAN Card": CARD, "Voter ID": CARD,
    "ABHA Card": CARD, "E-Shram": CARD, "Ayushman Bharat": CARD,
    "RC / Driving Licence": CARD, "APAAR ID": CARD,
    "PVC Portrait (54x85)": {"w_mm": 53.98, "h_mm": 85.60},
    "Passport Photo (35x45)": {"w_mm": 35.0, "h_mm": 45.0},
    "Stamp Photo (25x35)": {"w_mm": 25.0, "h_mm": 35.0},
    "Photo 4x6 inch": {"w_mm": 101.6, "h_mm": 152.4},
    "A5 Document": {"w_mm": 148.0, "h_mm": 210.0},
}
A4 = (210, 297)

def mm_px(mm, dpi=300): return int(round(mm / 25.4 * dpi))

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

def to_pil(bgr): return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

def jpeg_under(im, kb):
    """Shrink image to <= kb KB (quality search, then downscale)."""
    scale = 1.0
    while True:
        t = im if scale == 1 else im.resize((max(50, int(im.width * scale)), max(50, int(im.height * scale))), Image.LANCZOS)
        lo, hi, best = 10, 95, None
        while lo <= hi:
            q = (lo + hi) // 2; buf = io.BytesIO(); t.save(buf, "JPEG", quality=q)
            if buf.tell() <= kb * 1024: best, lo = buf.getvalue(), q + 1
            else: hi = q - 1
        if best or scale < 0.15: return best or buf.getvalue()
        scale *= 0.85

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
    except Exception as e: messagebox.showerror(APP, f"Print nahi hua: {e}")

def log(action, path, size_kb, customer=""):
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        if new: w.writerow(["Date", "Time", "Customer", "Action", "File", "Size KB"])
        w.writerow([time.strftime("%d-%m-%Y"), time.strftime("%H:%M:%S"), customer, action, path, size_kb])


class ProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light"); ctk.set_default_color_theme("blue")
        self.title(APP); self.geometry("1280x800"); self.minsize(1000, 650)
        self.items, self.idx, self.drag_i = [], -1, None
        self.presets = self.load_presets()
        self.tk_prev = None; self.off = (0, 0); self.sc = 1.0
        self.build()

    # ---------- data ----------
    def load_presets(self):
        try:
            with open(PRESET_FILE, encoding="utf8") as f: return json.load(f)
        except Exception: return dict(DEFAULT_PRESETS)

    def save_presets(self):
        with open(PRESET_FILE, "w", encoding="utf8") as f: json.dump(self.presets, f, indent=2)

    @property
    def cur(self): return self.items[self.idx] if 0 <= self.idx < len(self.items) else None

    def say(self, msg): self.status.configure(text=msg)

    # ---------- UI ----------
    def build(self):
        side = ctk.CTkFrame(self, width=250, corner_radius=0); side.pack(side="left", fill="y")
        ctk.CTkLabel(side, text="JAN SEVA PRO", font=("Segoe UI", 22, "bold")).pack(pady=(14, 0))
        ctk.CTkLabel(side, text="Documents ki list", text_color="gray").pack()
        ctk.CTkButton(side, text="📂  Photo / PDF Kholein", height=42, command=self.open_files).pack(fill="x", padx=12, pady=10)
        self.lb = tk.Listbox(side, font=("Segoe UI", 10), activestyle="none", exportselection=False, relief="flat", bd=0)
        self.lb.pack(fill="both", expand=True, padx=12); self.lb.bind("<<ListboxSelect>>", self.on_select)
        row = ctk.CTkFrame(side, fg_color="transparent"); row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Hatayein", width=100, fg_color="#c0392b", hover_color="#992d22", command=self.remove).pack(side="left")
        ctk.CTkButton(row, text="Sab Saaf", width=100, fg_color="gray", command=self.clear).pack(side="right")
        ctk.CTkLabel(side, text="Customer ka naam (log ke liye)").pack(anchor="w", padx=12)
        self.cust = ctk.CTkEntry(side); self.cust.pack(fill="x", padx=12, pady=(0, 12))

        main = ctk.CTkFrame(self, fg_color="transparent"); main.pack(side="right", fill="both", expand=True)
        self.tabs = ctk.CTkTabview(main); self.tabs.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        for t in ("✂ Crop / Scan", "🖨 Print Sheet", "🗜 KB Compress", "📄 PDF Tools", "📋 Log"): self.tabs.add(t)
        self.status = ctk.CTkLabel(main, anchor="w", text="Step 1: Left side se 'Photo / PDF Kholein' dabayein.", font=("Segoe UI", 13))
        self.status.pack(fill="x", padx=14, pady=6)
        self.tab_crop(self.tabs.tab("✂ Crop / Scan")); self.tab_sheet(self.tabs.tab("🖨 Print Sheet"))
        self.tab_comp(self.tabs.tab("🗜 KB Compress")); self.tab_pdf(self.tabs.tab("📄 PDF Tools")); self.tab_log(self.tabs.tab("📋 Log"))

    def btn(self, parent, text, cmd, **kw):
        b = ctk.CTkButton(parent, text=text, command=cmd, height=34, **kw); b.pack(side="left", padx=3, pady=3); return b

    def preset_box(self, parent):
        cb = ctk.CTkComboBox(parent, values=list(self.presets), width=210, state="readonly"); cb.set(list(self.presets)[0]); cb.pack(side="left", padx=3)
        return cb

    def tab_crop(self, t):
        r1 = ctk.CTkFrame(t, fg_color="transparent"); r1.pack(fill="x")
        ctk.CTkLabel(r1, text="Size Preset:").pack(side="left", padx=(4, 0)); self.pre = self.preset_box(r1)
        self.btn(r1, "+ Naya Preset", self.new_preset, width=110, fg_color="gray")
        self.btn(r1, "⚡ Auto Crop + Size (Sab)", self.batch_auto, width=190, fg_color="#27ae60", hover_color="#1e8449")
        r2 = ctk.CTkFrame(t, fg_color="transparent"); r2.pack(fill="x")
        self.btn(r2, "1. Corners Dhundo", self.detect, width=130)
        self.btn(r2, "2. Seedha + Size Karo", self.apply_crop, width=160)
        self.btn(r2, "⟲", lambda: self.rotate(cv2.ROTATE_90_COUNTERCLOCKWISE), width=40, fg_color="gray")
        self.btn(r2, "⟳", lambda: self.rotate(cv2.ROTATE_90_CLOCKWISE), width=40, fg_color="gray")
        self.btn(r2, "✨ Face/Text Saaf", self.do_enhance, width=130, fg_color="gray")
        self.btn(r2, "✍ Signature", self.add_sign, width=100, fg_color="gray")
        self.btn(r2, "↩ Undo", self.undo, width=70, fg_color="#e67e22", hover_color="#ca6f1e")
        self.btn(r2, "Reset", self.reset, width=70, fg_color="#e67e22", hover_color="#ca6f1e")
        r3 = ctk.CTkFrame(t, fg_color="transparent"); r3.pack(fill="x")
        self.btn(r3, "🪪 ID PDF: Front + Back Auto Alag", self.split_id, width=250, fg_color="#8e44ad", hover_color="#71368a")
        ctk.CTkLabel(r3, text="(Aadhaar/PAN/ABHA etc. PDF kholkar dabayein)", text_color="gray").pack(side="left")
        self.cv = tk.Canvas(t, bg="#2b2b2b", highlightthickness=0); self.cv.pack(fill="both", expand=True, pady=4)
        self.cv.bind("<Button-1>", lambda e: setattr(self, "drag_i", self.nearest(e.x, e.y)))
        self.cv.bind("<B1-Motion>", self.drag); self.cv.bind("<Configure>", lambda e: self.show())

    def tab_sheet(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x")
        ctk.CTkLabel(f, text="Copies (har document ki):").pack(side="left", padx=4)
        self.copies = ctk.CTkEntry(f, width=50); self.copies.insert(0, "1"); self.copies.pack(side="left")
        ctk.CTkLabel(f, text="Gap mm:").pack(side="left", padx=(12, 2))
        self.gap = ctk.CTkEntry(f, width=50); self.gap.insert(0, "4"); self.gap.pack(side="left")
        self.border = ctk.CTkCheckBox(f, text="Cutting line"); self.border.select(); self.border.pack(side="left", padx=12)
        self.which = ctk.CTkSegmentedButton(f, values=["Sab documents", "Sirf chuna hua"]); self.which.set("Sab documents"); self.which.pack(side="left", padx=6)
        g = ctk.CTkFrame(t, fg_color="transparent"); g.pack(fill="x", pady=6)
        self.btn(g, "👁 Preview", self.sheet_preview, width=100, fg_color="gray")
        self.btn(g, "💾 PDF", lambda: self.sheet_export("pdf"), width=80)
        self.btn(g, "💾 JPG", lambda: self.sheet_export("jpg"), width=80)
        self.btn(g, "💾 PNG", lambda: self.sheet_export("png"), width=80)
        self.btn(g, "🖨 Seedha Print", self.sheet_print, width=130, fg_color="#27ae60", hover_color="#1e8449")
        ctk.CTkLabel(t, text="Tip: Aadhaar front+back dono list me rakhein — ek hi A4 page par ek saath print honge.", text_color="gray").pack(anchor="w", padx=6)
        self.sv = tk.Canvas(t, bg="#ddd", highlightthickness=0); self.sv.pack(fill="both", expand=True, pady=4)

    def tab_comp(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x", pady=6)
        ctk.CTkLabel(f, text="Maximum size (KB):", font=("Segoe UI", 14)).pack(side="left", padx=4)
        self.kb = ctk.CTkEntry(f, width=90); self.kb.insert(0, "50"); self.kb.pack(side="left")
        for k in (20, 50, 100, 200, 500, 1024):
            ctk.CTkButton(f, text=f"{k} KB" if k < 1024 else "1 MB", width=62, fg_color="gray", command=lambda k=k: (self.kb.delete(0, "end"), self.kb.insert(0, str(k)))).pack(side="left", padx=2)
        g = ctk.CTkFrame(t, fg_color="transparent"); g.pack(fill="x")
        self.btn(g, "Chuna hua document → JPG (exact KB)", self.comp_image, width=280)
        self.btn(g, "Sab documents → ek PDF (exact KB)", self.comp_pdf_items, width=270)
        self.btn(g, "Koi PDF chuno → chhota karo", self.comp_pdf_file, width=230, fg_color="gray")
        ctk.CTkLabel(t, text="Exact KB tak apne aap quality adjust hoti hai — baar baar try nahi karna.", text_color="gray").pack(anchor="w", padx=6, pady=8)

    def tab_pdf(self, t):
        for txt, fn in [("PDF Merge (kai PDF → ek)", self.pdf_merge), ("Photos → PDF", self.imgs_to_pdf),
                        ("PDF → Photos (JPG)", self.pdf_to_imgs), ("PDF → Word", self.pdf_to_word),
                        ("PDF Seedha Print", lambda: self.pick_print())]:
            ctk.CTkButton(t, text=txt, height=46, width=320, command=fn).pack(pady=6)

    def tab_log(self, t):
        f = ctk.CTkFrame(t, fg_color="transparent"); f.pack(fill="x")
        self.btn(f, "Refresh", self.refresh_log, width=90); self.btn(f, "CSV Kholein (Excel)", lambda: open_path(LOG_FILE), width=160, fg_color="gray")
        self.logbox = ctk.CTkTextbox(t, font=("Consolas", 12)); self.logbox.pack(fill="both", expand=True, pady=6); self.refresh_log()

    def refresh_log(self):
        self.logbox.delete("1.0", "end")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, encoding="utf8") as f: self.logbox.insert("end", "".join(f.readlines()[-200:][::-1]))
        else: self.logbox.insert("end", "Abhi koi export nahi hua.")

    # ---------- items ----------
    def add_item(self, name, img):
        self.items.append({"name": name, "orig": img.copy(), "img": img, "corners": auto_corners(img), "preset": None, "hist": []})
        self.lb.insert("end", name); self.select(len(self.items) - 1)

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

    def open_files(self):
        ps = filedialog.askopenfilenames(filetypes=[("Photo / PDF", "*.jpg *.jpeg *.png *.webp *.bmp *.pdf")])
        for p in ps:
            base = os.path.basename(p)
            if p.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(p)
                    if doc.needs_pass:
                        pw = simpledialog.askstring(APP, f"{base} ka password (Aadhaar: naam ke 4 akshar + janm varsh):", show="*")
                        if not pw or not doc.authenticate(pw): messagebox.showerror(APP, "Password galat hai."); continue
                    for n, pg in enumerate(doc):
                        pix = pg.get_pixmap(dpi=300)
                        arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)
                        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
                        self.add_item(f"{base} p{n + 1}", bgr)
                except Exception as e: messagebox.showerror(APP, f"PDF nahi khuli: {e}")
            else:
                img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
                if img is None: messagebox.showerror(APP, f"{base} khul nahi payi."); continue
                self.add_item(base, img)
        if ps: self.say("Step 2: '⚡ Auto Crop + Size' dabayein, ya corners mouse se adjust karke '2. Seedha + Size Karo'.")

    # ---------- crop tab ----------
    def push(self):
        c = self.cur; c["hist"].append((c["img"].copy(), c["corners"].copy(), c["preset"])); c["hist"] = c["hist"][-10:]

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

    def drag(self, e):
        c = self.cur
        if c is None or self.drag_i is None: return
        h, w = c["img"].shape[:2]
        c["corners"][self.drag_i] = [max(0, min(w - 1, (e.x - self.off[0]) / self.sc)), max(0, min(h - 1, (e.y - self.off[1]) / self.sc))]
        self.show()

    def detect(self):
        if self.cur: self.cur["corners"] = auto_corners(self.cur["img"]); self.show(); self.say("Corners mil gaye. Lal gol dot ko drag karke theek karein, phir '2. Seedha + Size Karo'.")

    def fit_preset(self, img, name):
        s = self.presets[name]; tw, th = mm_px(s["w_mm"]), mm_px(s["h_mm"])
        if (img.shape[1] > img.shape[0]) != (tw > th): img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        return cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA if img.shape[1] > tw else cv2.INTER_CUBIC)

    def apply_crop(self, silent=False):
        c = self.cur
        if c is None: return
        self.push(); name = self.pre.get()
        c["img"] = self.fit_preset(four_point_warp(c["img"], c["corners"]), name)
        c["preset"] = name; c["corners"] = full_rect(c["img"]); self.show()
        if not silent: self.say(f"Ho gaya: {name} ke exact size me. Ab 'Print Sheet' tab me jayein.")

    def batch_auto(self):
        if not self.items: return self.say("Pehle photos kholein.")
        keep = self.idx
        for i, c in enumerate(self.items):
            self.idx = i; c["corners"] = auto_corners(c["img"]); self.apply_crop(True); self.update_idletasks()
        self.select(keep); self.say(f"{len(self.items)} documents ek saath crop + size ho gaye.")

    def rotate(self, code):
        if self.cur: self.push(); self.cur["img"] = cv2.rotate(self.cur["img"], code); self.cur["corners"] = full_rect(self.cur["img"]); self.show()

    def do_enhance(self):
        if self.cur: self.push(); self.cur["img"] = enhance(self.cur["img"]); self.show(); self.say("Saaf aur sharp kar diya.")

    def undo(self):
        c = self.cur
        if c and c["hist"]: c["img"], c["corners"], c["preset"] = c["hist"].pop(); self.show()

    def reset(self):
        c = self.cur
        if c: self.push(); c["img"] = c["orig"].copy(); c["corners"] = auto_corners(c["img"]); c["preset"] = None; self.show()

    def add_sign(self):
        c = self.cur
        if c is None: return
        p = filedialog.askopenfilename(title="Signature image (PNG)", filetypes=[("Image", "*.png *.jpg *.jpeg")])
        if not p: return
        self.push(); base = to_pil(c["img"]).convert("RGBA"); sg = Image.open(p).convert("RGBA")
        sg.thumbnail((int(base.width * .28), int(base.height * .18)))
        base.alpha_composite(sg, (base.width - sg.width - 20, base.height - sg.height - 20))
        c["img"] = cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR); self.show()

    def new_preset(self):
        n = simpledialog.askstring(APP, "Preset ka naam:")
        if not n: return
        try:
            w = float(simpledialog.askstring(APP, "Chaudai (width) mm me:")); h = float(simpledialog.askstring(APP, "Lambai (height) mm me:"))
        except Exception: return messagebox.showerror(APP, "Sahi number likhein.")
        self.presets[n] = {"w_mm": w, "h_mm": h}; self.save_presets()
        self.pre.configure(values=list(self.presets)); self.pre.set(n)

    def split_id(self):
        c = self.cur
        if c is None: return self.say("Pehle ID PDF kholein.")
        cards = find_cards(c["img"])
        if not cards: return self.say("Card nahi mila — manual corners use karein.")
        base = c["name"]; self.remove()
        for i, cr in enumerate(cards):
            self.add_item(f"{base} {'Front' if i == 0 else 'Back'}", cr); self.idx = len(self.items) - 1; self.apply_crop(True)
        self.say(f"{len(cards)} card alag ho gaye (Front/Back) aur preset size me set hain.")

    # ---------- sheet ----------
    def sel_items(self):
        its = self.items if self.which.get() == "Sab documents" else ([self.cur] if self.cur else [])
        out = []
        for c in its:
            im = to_pil(c["img"])
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
        pages, rows, y, rowh = [], [], M, 0
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
        if not pages: return self.say("Koi document nahi hai.")
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
        if not pages: return self.say("Koi document nahi hai.")
        out = filedialog.asksaveasfilename(defaultextension="." + fmt, initialfile=f"A4_Sheet.{fmt}")
        if out: self.save_pages(pages, out); self.say("Save ho gaya: " + out); open_path(out)

    def sheet_print(self):
        pages = self.build_pages()
        if not pages: return self.say("Koi document nahi hai.")
        tmp = os.path.join(HOME, "JanSeva_print_tmp.pdf"); self.save_pages(pages, tmp); print_file(tmp)

    # ---------- compress ----------
    def kbval(self):
        try: return max(5, int(float(self.kb.get())))
        except Exception: messagebox.showerror(APP, "KB sahi likhein."); return None

    def comp_image(self):
        k = self.kbval()
        if not k or self.cur is None: return
        out = filedialog.asksaveasfilename(defaultextension=".jpg", initialfile=f"{k}KB.jpg")
        if out: open(out, "wb").write(jpeg_under(to_pil(self.cur["img"]), k)); log("Compress", out, os.path.getsize(out) // 1024, self.cust.get()); self.say(f"Save: {out} ({os.path.getsize(out) // 1024} KB)")

    def comp_pdf_items(self):
        k = self.kbval()
        if not k or not self.items: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{k}KB.pdf")
        if out: self.save_pages([to_pil(c["img"]) for c in self.items], out, k); self.say(f"Save: {out} ({os.path.getsize(out) // 1024} KB)")

    def comp_pdf_file(self):
        k = self.kbval(); p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not k or not p: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{k}KB.pdf")
        if not out: return
        doc = fitz.open(p); pages = []
        for pg in doc:
            pix = pg.get_pixmap(dpi=150); pages.append(Image.frombytes("RGB", (pix.w, pix.h), pix.samples))
        self.save_pages(pages, out, k); self.say(f"Save: {out} ({os.path.getsize(out) // 1024} KB)")

    # ---------- pdf tools ----------
    def pdf_merge(self):
        ps = filedialog.askopenfilenames(title="PDF chuno (order me)", filetypes=[("PDF", "*.pdf")])
        if len(ps) < 2: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Merged.pdf")
        if not out: return
        m = fitz.open()
        for p in ps: m.insert_pdf(fitz.open(p))
        m.save(out); log("Merge", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("Merge ho gaya: " + out)

    def imgs_to_pdf(self):
        ps = filedialog.askopenfilenames(filetypes=[("Photos", "*.jpg *.jpeg *.png *.webp *.bmp")])
        out = ps and filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Photos.pdf")
        if not out: return
        ims = [Image.open(p).convert("RGB") for p in ps]; ims[0].save(out, "PDF", resolution=200.0, save_all=True, append_images=ims[1:])
        log("Photos->PDF", out, os.path.getsize(out) // 1024, self.cust.get()); self.say("PDF ban gayi: " + out)

    def pdf_to_imgs(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        d = p and filedialog.askdirectory()
        if not d: return
        for n, pg in enumerate(fitz.open(p)): pg.get_pixmap(dpi=200).save(os.path.join(d, f"page_{n + 1}.jpg"))
        self.say("Photos save ho gayi: " + d); open_path(d)

    def pdf_to_word(self):
        try: from pdf2docx import Converter
        except ImportError: return messagebox.showinfo(APP, "Pehle install karein:  pip install pdf2docx")
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        out = p and filedialog.asksaveasfilename(defaultextension=".docx")
        if out: c = Converter(p); c.convert(out); c.close(); self.say("Word file ban gayi: " + out); open_path(out)

    def pick_print(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: print_file(p)


if __name__ == "__main__":
    ProApp().mainloop()
