import json
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk, ImageGrab
import base64
from io import BytesIO

# ---- Windows IME ----
try:
    imm32 = ctypes.windll.imm32
    imm32.ImmGetContext.argtypes = [wintypes.HWND]
    imm32.ImmGetContext.restype = wintypes.HANDLE
    imm32.ImmSetOpenStatus.argtypes = [wintypes.HANDLE, wintypes.BOOL]
    imm32.ImmSetOpenStatus.restype = wintypes.BOOL
    imm32.ImmReleaseContext.argtypes = [wintypes.HWND, wintypes.HANDLE]
    imm32.ImmReleaseContext.restype = wintypes.BOOL
    IME_OK = True
except:
    IME_OK = False

def set_ime(hwnd, on):
    if not IME_OK:
        return
    try:
        h = imm32.ImmGetContext(wintypes.HWND(hwnd))
        if h:
            imm32.ImmSetOpenStatus(h, wintypes.BOOL(1 if on else 0))
            imm32.ImmReleaseContext(wintypes.HWND(hwnd), h)
    except:
        pass

# ---- データ ----
def data_dir():
    d = os.path.join(os.path.expanduser("~"), "StickyNote")
    os.makedirs(d, exist_ok=True)
    return d

DATA_PATH = os.path.join(data_dir(), "sticky_note_data.json")
DEFAULT = {"tabs": [{"name": "メモ1", "messages": []}], "bg_idx": 0, "pin": False, "ime": True, "geo": None, "tab": 0, "mini": False}

# プリセット背景色: (背景, カード, ピン済み, ヘッダー, タブ)
BG_COLORS = [
    ("#1A1A2E", "#2A2A4E", "#4040AA", "#252545", "#35355E"),  # 青
    ("#0D3B66", "#1D5B96", "#2D7BC6", "#154B76", "#2565A6"),  # 明るい青
    ("#1E2E1E", "#2E4E2E", "#40AA40", "#253E25", "#35583E"),  # 緑
    ("#2E1E1E", "#4E2E2E", "#AA4040", "#3E2525", "#583535"),  # 赤
    ("#2B1B2E", "#4B3B5E", "#8B5BAE", "#3B2B3E", "#5B4B6E"),  # 紫
    ("#2D2D2D", "#4D4D4D", "#6D6D6D", "#3D3D3D", "#555555"),  # グレー
    ("#1B2838", "#3B4858", "#5B6878", "#2B3848", "#455868"),  # スレート
    ("#2E2E1E", "#4E4E2E", "#AAAA40", "#3E3E25", "#585835"),  # 黄
]

def load():
    try:
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in DEFAULT.items():
                    d.setdefault(k, v)
                return d
    except:
        pass
    return DEFAULT.copy()

def save(d):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ---- スタイル ----
TEXT_FG = "#E0E0E0"
HINT_FG = "#888"

class NoteWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Sticky Note")
        self.protocol("WM_DELETE_WINDOW", self.close)
        
        self.data = load()
        self.imgs = []
        self.drag = {}
        
        # 背景色
        self.bg_idx = self.data.get("bg_idx", 0) % len(BG_COLORS)
        self._set_colors()
        
        self.configure(bg=self.bg)
        self.attributes("-topmost", self.data.get("pin", False))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Notebookの行
        
        # === Row 0: 入力 ===
        self.inp_frame = tk.Frame(self, bg=self.header_bg)
        self.inp_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.inp_frame.grid_columnconfigure(0, weight=1)
        
        # 入力枠のタイトルとしてタブ名を表示
        self.target_label = tk.Label(self.inp_frame, text="To: ", font=("", 8), bg=self.header_bg, fg=HINT_FG, anchor="w")
        self.target_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(2, 0))

        # 入力欄
        self.txt = tk.Text(self.inp_frame, height=2, font=("Segoe UI", 10), bg="#F0F0F0", fg="#333",
                          insertbackground="#333", relief="sunken", bd=1, wrap="word",
                          highlightthickness=1, highlightbackground="#555", highlightcolor="#777")
        self.txt.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.txt.bind("<Return>", self._on_enter)
        self.txt.bind("<Shift-Return>", lambda e: None)
        self.txt.bind("<FocusIn>", self._on_focus_in)
        self.txt.bind("<FocusOut>", self._on_focus_out)
        
        # 追加ボタン
        self.send_btn = tk.Button(self.inp_frame, text="追加", font=("", 9), width=4, height=1,
                                 bg="#555", fg="#FFF", bd=1, relief="raised", command=self.add_msg)
        self.send_btn.grid(row=1, column=1, padx=(4, 2), pady=(0, 6))
        
        # 画像ボタン
        self.img_btn = tk.Button(self.inp_frame, text="Img", font=("", 8), width=4, height=1,
                                 bg="#555", fg="#FFF", bd=1, relief="raised", command=self.add_img)
        self.img_btn.grid(row=1, column=2, padx=(0, 6), pady=(0, 6))
        
        # === Row 1: コントロール ===
        self.ctrl = tk.Frame(self, bg=self.header_bg)
        self.ctrl.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))
        
        # タブ操作（横長ボタン）
        # タブ操作
        tk.Button(self.ctrl, text="−", font=("", 8), width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised",
                 command=self.del_tab).pack(side="left")
        tk.Button(self.ctrl, text="+", font=("", 8), width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised",
                 command=self.add_tab).pack(side="left", padx=(2, 8))
        
        # 右側コントロール
        self.ime_on = self.data.get("ime", True)
        self.ime_btn = tk.Button(self.ctrl, text="あ" if self.ime_on else "A", font=("", 8), width=3, height=1,
                                bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_ime)
        self.ime_btn.pack(side="right")
        
        # ピンボタン
        self.pin_btn = tk.Button(self.ctrl, text="■" if self.data.get("pin") else "□", font=("", 8), 
                                width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_pin)
        self.pin_btn.pack(side="right", padx=2)
        
        # ミニモードボタン
        self.is_mini = self.data.get("mini", False)
        self.mini_btn = tk.Button(self.ctrl, text="▬" if self.is_mini else "▭", font=("", 8),
                                 width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_mini)
        self.mini_btn.pack(side="right", padx=2)
        
        # 色ボタン（複数並べる）
        self.color_Frame = tk.Frame(self.ctrl, bg=self.header_bg)
        self.color_Frame.pack(side="right", padx=2)
        for i, (bg, _, _, _, _) in enumerate(BG_COLORS):
            btn = tk.Button(self.color_Frame, text="", width=1, bg=bg, relief="raised", bd=1,
                           command=lambda idx=i: self.set_color(idx))
            btn.pack(side="left", padx=0)
        
        # === Row 2: ミニ表示（通常は非表示） ===
        self.mini_frame = tk.Frame(self, bg=self.bg)
        self.mini_label = tk.Label(self.mini_frame, text="", font=("Segoe UI", 9), fg=TEXT_FG, 
                                  bg=self.card_bg, anchor="w", justify="left", wraplength=350, padx=8, pady=6)
        self.mini_label.pack(fill="x", padx=6, pady=4)
        
        # === Row 3: Notebook ===
        self._setup_style()
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.nb.bind("<Double-1>", self.rename_tab)
        self.nb.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        self._load_tabs()
        
        geo = self.data.get("geo")
        self.geometry(geo if geo else "380x420")
        
        if self.is_mini:
            self._enter_mini()
        
        self.place_holder = "ここにメモを入力..."
        self._show_placeholder()
        
        self.after(100, lambda: set_ime(self.txt.winfo_id(), self.ime_on))
        self.after(200, lambda: self.attributes("-topmost", True))
        self.after(1000, lambda: self.attributes("-topmost", self.data.get("pin", False)))
    
    def _show_placeholder(self):
        if not self.txt.get("1.0", "end-1c").strip():
            self.txt.configure(fg="#888")
            self.txt.delete("1.0", "end")
            self.txt.insert("1.0", self.place_holder)

    def _on_focus_in(self, e):
        if self.txt.get("1.0", "end-1c") == self.place_holder:
            self.txt.delete("1.0", "end")
            self.txt.configure(fg="#000") # 入力時は黒文字（背景白系にするため）
    
    def _on_focus_out(self, e):
        if not self.txt.get("1.0", "end-1c").strip():
            self._show_placeholder()

    def _set_colors(self):
        colors = BG_COLORS[self.bg_idx]
        self.bg = colors[0]
        self.card_bg = colors[1]
        self.card_pin = colors[2]
        self.header_bg = colors[3]
        self.tab_bg = colors[4]
    
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.bg, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[10, 4], font=("Segoe UI", 9), 
                       background=self.tab_bg, foreground="#CCC")
        style.map("TNotebook.Tab", 
                 background=[("selected", self.card_pin)], 
                 foreground=[("selected", "#FFF")])
    
    def _load_tabs(self):
        for t in self.data.get("tabs", []):
            self._make_tab(t)
        idx = self.data.get("tab", 0)
        if 0 <= idx < len(self.nb.tabs()):
            self.nb.select(idx)
    
    def _make_tab(self, tdata):
        tab = tk.Frame(self.nb, bg=self.bg)
        
        canvas = tk.Canvas(tab, bg=self.bg, highlightthickness=0)
        sb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner = tk.Frame(canvas, bg=self.bg)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta/120), "units"))
        
        tab.canvas = canvas
        tab.inner = inner
        tab.rows = []
        tab.tdata = tdata
        
        for m in tdata.get("messages", []):
            self._add_row(inner, m, tab, top=False)
        
        self.nb.add(tab, text=tdata.get("name", "Tab"))
        return tab
    
    def add_tab(self):
        n = len(self.data["tabs"])
        t = {"name": f"メモ{n+1}", "messages": []}
        self.data["tabs"].append(t)
        self._make_tab(t)
        self.nb.select(len(self.nb.tabs()) - 1)
        self._save()
    
    def del_tab(self):
        if len(self.nb.tabs()) <= 1:
            return
        idx = self.nb.index(self.nb.select())
        self.nb.forget(idx)
        del self.data["tabs"][idx]
        self._save()
    
    def rename_tab(self, e):
        try:
            i = self.nb.tk.call(self.nb._w, "identify", "tab", e.x, e.y)
            if i != "":
                old = self.nb.tab(i, "text")
                new = simpledialog.askstring("タブ名", "新しい名前:", initialvalue=old)
                if new:
                    self.nb.tab(i, text=new)
                    self.data["tabs"][int(i)]["name"] = new
                    self._save()
        except:
            pass
    
    def on_tab_change(self, e):
        # タブ切り替え直後の描画乱れを防ぐため少し遅延（長めに設定）
        self.after(150, self._delayed_tab_update)

    def _delayed_tab_update(self):
        try:
            self.update_idletasks()
            if not self.nb.select():
                if self.nb.tabs():
                    self.nb.select(0)
            
            idx = self.nb.index(self.nb.select())
            self.data["tab"] = idx
            tab = self._tab()
            
            # ターゲットラベル更新
            tdata = self._tdata()
            if tdata:
                self.target_label.config(text=f"To: {tdata.get('name', 'Tab')}")
            
            if tab:
                self._refresh(tab)
                # スクロール領域を強制更新
                tab.inner.update_idletasks()
                tab.canvas.configure(scrollregion=tab.canvas.bbox("all"))
                tab.canvas.yview_moveto(0)
            if self.is_mini:
                self._update_mini()
            self._save()
        except:
            pass
    
    def _tab(self):
        try:
            return self.nb.nametowidget(self.nb.select())
        except:
            return None
    
    def _tdata(self):
        try:
            return self.data["tabs"][self.nb.index(self.nb.select())]
        except:
            return None
    
    def toggle_pin(self):
        self.data["pin"] = not self.data.get("pin", False)
        self.attributes("-topmost", self.data["pin"])
        self.pin_btn.config(text="■" if self.data["pin"] else "□")
        self._save()
    
    def toggle_ime(self):
        self.ime_on = not self.ime_on
        self.data["ime"] = self.ime_on
        self.ime_btn.config(text="あ" if self.ime_on else "A")
        set_ime(self.txt.winfo_id(), self.ime_on)
        self._save()
    
    def toggle_mini(self):
        self.is_mini = not self.is_mini
        self.data["mini"] = self.is_mini
        self.mini_btn.config(text="▬" if self.is_mini else "▭")
        if self.is_mini:
            self._enter_mini()
        else:
            self._leave_mini()
        self._save()
    
    def _enter_mini(self):
        self.nb.grid_remove()
        self.mini_frame.grid(row=2, column=0, sticky="ew")
        self._update_mini()
        self.geometry("380x120")
    
    def _leave_mini(self):
        self.mini_frame.grid_remove()
        self.nb.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.geometry("380x420")
    
    def _update_mini(self):
        tdata = self._tdata()
        if tdata and tdata.get("messages"):
            m = tdata["messages"][0]  # 最新の1件
            self.mini_label.config(text=f"[{m.get('t', '')}] {m.get('m', '')}")
        else:
            self.mini_label.config(text="(メモなし)")
    
    def set_color(self, idx):
        self.bg_idx = idx % len(BG_COLORS)
        self.data["bg_idx"] = self.bg_idx
        self._set_colors()
        self._apply_bg()
        self._save()
    
    def _on_enter(self, e):
        self.add_msg()
        return "break"
    
    def add_msg(self):
        text = self.txt.get("1.0", "end-1c").strip()
        ph = getattr(self, "place_holder", "").strip()
        if not text or (ph and text == ph):
            self.bell()
            return
        
        tdata = self._tdata()
        tab = self._tab()
        
        # タブ情報が取れない場合、強制的に先頭を選択して再試行
        if not tdata or not tab:
            if self.nb.tabs():
                self.nb.select(0)
                self.update_idletasks()
                tdata = self._tdata()
                tab = self._tab()
        
        if not tdata or not tab:
            self.bell()
            return
        
        self.txt.delete("1.0", "end")
        m = {"t": time.strftime("%Y-%m-%d %H:%M"), "m": text, "pin": False}
        tdata["messages"].insert(0, m)
        self._add_row(tab.inner, m, tab, top=True)
        self._save()
        if self.is_mini:
            self._update_mini()
        self.after(50, lambda: tab.canvas.yview_moveto(0))
        self.txt.focus_set()
    
    def add_img(self):
        img = None
        try:
            img = ImageGrab.grabclipboard()
        except:
            pass
        
        if not isinstance(img, Image.Image):
            p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")])
            if p:
                try:
                    img = Image.open(p)
                except:
                    return
        
        if isinstance(img, Image.Image):
            if img.width > 280:
                r = 280 / img.width
                img = img.resize((280, int(img.height * r)), Image.Resampling.LANCZOS)
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            tdata = self._tdata()
            tab = self._tab()
            if not tdata or not tab:
                return
            
            m = {"t": time.strftime("%Y-%m-%d %H:%M"), "m": "[画像]", "img": b64, "pin": False}
            tdata["messages"].insert(0, m)
            self._add_row(tab.inner, m, tab, top=True)
            self._save()
            if self.is_mini:
                self._update_mini()
    
    def _add_row(self, parent, m, tab, top=False):
        row = self._make_row(parent, m, tab)
        if top and parent.winfo_children():
            row.pack(fill="x", pady=2, before=parent.winfo_children()[0])
            tab.rows.insert(0, row)
        else:
            row.pack(fill="x", pady=2)
            tab.rows.append(row)
    
    def _make_row(self, parent, m, tab):
        is_pinned = m.get("pin", False)
        bg = self.card_pin if is_pinned else self.card_bg
        
        row = tk.Frame(parent, bg=bg)
        
        # 左
        left = tk.Frame(row, bg=bg)
        left.pack(side="left", fill="y", padx=4, pady=4)
        
        drag = tk.Label(left, text="≡", font=("", 9), fg=HINT_FG, bg=bg, cursor="fleur")
        drag.pack()
        drag.bind("<Button-1>", lambda e: self._drag_start(e, row, tab))
        drag.bind("<B1-Motion>", lambda e: self._drag_move(e, row, tab))
        drag.bind("<ButtonRelease-1>", lambda e: self._drag_end(row))
        
        pin = tk.Label(left, text="●" if is_pinned else "○", font=("", 8), fg=HINT_FG, bg=bg, cursor="hand2")
        pin.pack(pady=(2, 0))
        pin.bind("<Button-1>", lambda e: self._toggle_pin(m, tab))
        
        # 中央
        mid = tk.Frame(row, bg=bg)
        mid.pack(side="left", fill="both", expand=True, pady=4)
        
        tk.Label(mid, text=m.get("t", ""), font=("", 8), fg=HINT_FG, bg=bg, anchor="w").pack(fill="x")
        tk.Label(mid, text=m.get("m", ""), font=("", 9), fg=TEXT_FG, bg=bg, anchor="w",
                justify="left", wraplength=220).pack(fill="x")
        
        if m.get("img"):
            try:
                photo = ImageTk.PhotoImage(Image.open(BytesIO(base64.b64decode(m["img"]))))
                lbl = tk.Label(mid, image=photo, bg=bg)
                lbl.image = photo
                lbl.pack(pady=2)
                self.imgs.append(photo)
            except:
                pass
        
        # 右
        right = tk.Frame(row, bg=bg)
        right.pack(side="right", fill="y", padx=4, pady=4)
        
        edit = tk.Label(right, text="✎", font=("", 9), fg=HINT_FG, bg=bg, cursor="hand2")
        edit.pack()
        edit.bind("<Button-1>", lambda e: self._edit(m, tab))
        
        copy = tk.Label(right, text="⧉", font=("", 9), fg=HINT_FG, bg=bg, cursor="hand2")
        copy.pack(pady=(2, 0))
        copy.bind("<Button-1>", lambda e: self._copy(m.get("m", ""), copy))
        
        dele = tk.Label(right, text="×", font=("", 9), fg=HINT_FG, bg=bg, cursor="hand2")
        dele.pack(pady=(2, 0))
        dele.bind("<Button-1>", lambda e: self._del(m, row, tab))
        
        return row
    
    def _toggle_pin(self, m, tab):
        tdata = getattr(tab, "tdata", None)
        if not tdata or m not in tdata["messages"]:
            return
        m["pin"] = not m.get("pin", False)
        if m["pin"]:
            tdata["messages"].remove(m)
            tdata["messages"].insert(0, m)
        self._refresh(tab)
        self._save()
    
    def _edit(self, m, tab):
        new = simpledialog.askstring("編集", "メモ:", initialvalue=m.get("m", ""))
        if new is not None:
            m["m"] = new
            self._refresh(tab)
            self._save()
    
    def _copy(self, text, lbl):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            lbl.config(text="✓")
            self.after(400, lambda: lbl.config(text="⧉"))
        except:
            pass
    
    def _del(self, m, row, tab):
        tdata = getattr(tab, "tdata", None)
        if tdata and m in tdata["messages"]:
            tdata["messages"].remove(m)
            if row in tab.rows:
                tab.rows.remove(row)
            row.destroy()
            self._save()
    
    def _drag_start(self, e, row, tab):
        try:
            self.drag = {"row": row, "y": e.y_root, "idx": tab.rows.index(row)}
            row.config(relief="raised", bd=1)
        except:
            pass
    
    def _drag_move(self, e, row, tab):
        if self.drag.get("row") != row:
            return
        dy = e.y_root - self.drag["y"]
        idx = self.drag["idx"]
        if dy > 30 and idx < len(tab.rows) - 1:
            self._swap(tab, idx, idx + 1)
            self.drag["idx"] = idx + 1
            self.drag["y"] = e.y_root
        elif dy < -30 and idx > 0:
            self._swap(tab, idx, idx - 1)
            self.drag["idx"] = idx - 1
            self.drag["y"] = e.y_root
    
    def _drag_end(self, row):
        row.config(relief="flat", bd=0)
        self.drag = {}
        self._save()
    
    def _swap(self, tab, i, j):
        tdata = getattr(tab, "tdata", None)
        if tdata:
            msgs = tdata["messages"]
            msgs[i], msgs[j] = msgs[j], msgs[i]
            self._refresh(tab)
            if 0 <= j < len(tab.rows):
                tab.rows[j].config(relief="raised", bd=1)
                self.drag["row"] = tab.rows[j]
    
    def _refresh(self, tab):
        for r in tab.rows:
            r.destroy()
        tab.rows = []
        tdata = getattr(tab, "tdata", None)
        if tdata:
            for m in tdata["messages"]:
                self._add_row(tab.inner, m, tab, top=False)
    
    def _apply_bg(self):
        self.configure(bg=self.bg)
        self.inp_frame.configure(bg=self.header_bg)
        
        # テキストエリアは白背景で見やすく
        self.txt.configure(bg="#FFF", fg="#000", insertbackground="#000")
        if self.txt.get("1.0", "end-1c") == getattr(self, "place_holder", ""):
            self.txt.configure(fg="#888")
            
        self.ctrl.configure(bg=self.header_bg)
        
        if hasattr(self, "color_Frame"):
            self.color_Frame.configure(bg=self.header_bg)
            
        self.mini_frame.configure(bg=self.bg)
        self.mini_label.configure(bg=self.card_bg)
        
        self._setup_style()
        
        for tab_id in self.nb.tabs():
            tab = self.nb.nametowidget(tab_id)
            tab.configure(bg=self.bg)
            tab.canvas.configure(bg=self.bg)
            tab.inner.configure(bg=self.bg)
        
        tab = self._tab()
        if tab:
            self._refresh(tab)
    
    def _save(self):
        try:
            self.data["geo"] = self.geometry()
        except:
            pass
        save(self.data)
    
    def close(self):
        self._save()
        self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.after(0, lambda: NoteWindow(self))

if __name__ == "__main__":
    App().mainloop()
