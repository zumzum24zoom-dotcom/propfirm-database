import json
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import ctypes
from ctypes import wintypes

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

BG_COLORS = [
    ("#1A1A2E", "#2A2A4E", "#4040AA", "#252545", "#35355E"),
    ("#0D3B66", "#1D5B96", "#2D7BC6", "#154B76", "#2565A6"),
    ("#1E2E1E", "#2E4E2E", "#40AA40", "#253E25", "#35583E"),
    ("#2E1E1E", "#4E2E2E", "#AA4040", "#3E2525", "#583535"),
    ("#2B1B2E", "#4B3B5E", "#8B5BAE", "#3B2B3E", "#5B4B6E"),
    ("#2D2D2D", "#4D4D4D", "#6D6D6D", "#3D3D3D", "#555555"),
    ("#1B2838", "#3B4858", "#5B6878", "#2B3848", "#455868"),
    ("#2E2E1E", "#4E4E2E", "#AAAA40", "#3E3E25", "#585835"),
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
        self.grid_rowconfigure(3, weight=1)

        # === Row 0: 入力 ===
        self.inp_frame = tk.Frame(self, bg=self.header_bg)
        self.inp_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.inp_frame.grid_columnconfigure(0, weight=1)

        self.target_label = tk.Label(self.inp_frame, text="To: ", font=("", 8), bg=self.header_bg, fg=HINT_FG, anchor="w")
        self.target_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(2, 0))

        self.txt = tk.Text(self.inp_frame, height=2, font=("Segoe UI", 10), bg="#F0F0F0", fg="#333",
                           insertbackground="#333", relief="sunken", bd=1, wrap="word",
                           highlightthickness=1, highlightbackground="#555", highlightcolor="#777")
        self.txt.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.txt.bind("<Return>", self._on_enter)

        self.send_btn = tk.Button(self.inp_frame, text="追加", font=("", 9), width=4, height=1,
                                  bg="#555", fg="#FFF", bd=1, relief="raised", command=self.add_msg)
        self.send_btn.grid(row=1, column=1, padx=(4, 2), pady=(0, 6))

        # === Row 1: コントロール ===
        self.ctrl = tk.Frame(self, bg=self.header_bg)
        self.ctrl.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))

        self.toggle_view_btn = tk.Button(self.ctrl, text="管理画面", command=self.toggle_view)
        self.toggle_view_btn.pack(side="left")

        tk.Button(self.ctrl, text="−", font=("", 8), width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised",
                  command=self.del_tab).pack(side="left")
        tk.Button(self.ctrl, text="+", font=("", 8), width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised",
                  command=self.add_tab).pack(side="left", padx=(2, 8))

        self.ime_on = self.data.get("ime", True)
        self.ime_btn = tk.Button(self.ctrl, text="あ" if self.ime_on else "A", font=("", 8), width=3, height=1,
                                 bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_ime)
        self.ime_btn.pack(side="right")

        self.pin_btn = tk.Button(self.ctrl, text="■" if self.data.get("pin") else "□", font=("", 8), 
                                 width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_pin)
        self.pin_btn.pack(side="right", padx=2)

        self.is_mini = self.data.get("mini", False)
        self.mini_btn = tk.Button(self.ctrl, text="▬" if self.is_mini else "▭", font=("", 8),
                                  width=3, height=1, bg="#444", fg=HINT_FG, bd=1, relief="raised", command=self.toggle_mini)
        self.mini_btn.pack(side="right", padx=2)

        # === Row 3: Notebook ===
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.nb.bind("<Double-1>", self.rename_tab)

        self._load_tabs()  # 既存のタブを読み込む

        geo = self.data.get("geo")
        self.geometry(geo if geo else "380x420")

        self.after(100, lambda: set_ime(self.txt.winfo_id(), self.ime_on))
        self.after(200, lambda: self.attributes("-topmost", True))

    def _on_enter(self, event):
        """エンターキーが押されたときの処理"""
        text = self.txt.get("1.0", tk.END).strip()
        if text:
            messagebox.showinfo("メモ", f"メモが追加されました:\n{text}")
            self.txt.delete("1.0", tk.END)  # 入力フィールドをクリア
        return "break"  # Enterキーによる新しい行の追加を防ぐ

    def add_msg(self):
        """メッセージをリストに追加する処理"""
        text = self.txt.get("1.0", tk.END).strip()
        if text:
            current_tab_index = self.nb.index(self.nb.select())
            self.data["tabs"][current_tab_index]["messages"].append(text)
            self.txt.delete("1.0", tk.END)  # 入力フィールドをクリア
            self.show_notes()  # 表示を更新

    def show_notes(self):
        """ノートのメッセージを表示する"""
        current_tab_index = self.nb.index(self.nb.select())
        messages = self.data["tabs"][current_tab_index]["messages"]
        self.txt.delete("1.0", tk.END)  # 現在のテキスト内容をクリア
        for msg in messages:
            self.txt.insert(tk.END, msg + "\n")  # メッセージを挿入

    def del_tab(self):
        """選択されたタブを削除する処理"""
        current_tab_index = self.nb.index(self.nb.select())
        if len(self.data["tabs"]) > 1:
            del self.data["tabs"][current_tab_index]
            self.nb.forget(current_tab_index)
            
            # 削除後に選択するタブを調整
            if current_tab_index >= len(self.data["tabs"]):
                current_tab_index -= 1
            self.nb.select(current_tab_index)  # 新しいタブを選択
            self.show_notes()  # メッセージ表示を更新
            save(self.data)
        else:
            messagebox.showwarning("警告", "少なくとも1つのノートが必要です。")

    def add_tab(self):
        """新しいタブを追加する処理"""
        tab_name = simpledialog.askstring("新しいタブ名", "タブ名を入力してください:")
        if tab_name:
            self.data["tabs"].append({"name": tab_name, "messages": []})
            new_tab_frame = tk.Frame(self.nb)
            self.nb.add(new_tab_frame, text=tab_name)
            self.nb.select(new_tab_frame)  # 新しいタブを選択
            self.show_notes()  # メッセージ表示を更新
            save(self.data)

    def toggle_view(self):
        """管理画面とノートの表示を切り替える"""
        if self.toggle_view_btn["text"] == "管理画面":
            self.show_management_view()
            self.toggle_view_btn.config(text="ノートに戻る")
        else:
            self.show_note_view()
            self.toggle_view_btn.config(text="管理画面")

    def show_management_view(self):
        """全ノートのリストを表示する管理画面"""
        self.clear_view()
        self.management_frame = tk.Frame(self)
        self.management_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))

        for idx, tdata in enumerate(self.data["tabs"]):
            note_frame = tk.Frame(self.management_frame)
            note_frame.pack(fill=tk.X, padx=5, pady=2)
            note_label = tk.Label(note_frame, text=tdata["name"], bg=self.header_bg, fg="#FFF")
            note_label.pack(side=tk.LEFT, padx=10, pady=5)

            edit_btn = tk.Button(note_frame, text="編集", command=lambda idx=idx: self.rename_tab_by_index(idx))
            edit_btn.pack(side=tk.RIGHT)

    def show_note_view(self):
        """選択中のノートを表示"""
        self.clear_view()
        self._load_tabs()

    def clear_view(self):
        """現在の表示をクリアする"""
        for widget in self.winfo_children():
            widget.destroy()

    def rename_tab_by_index(self, idx):
        """タブ名のリネーム"""
        old_name = self.data["tabs"][idx]["name"]
        new_name = simpledialog.askstring("タブ名変更", "新しい名前を入力:", initialvalue=old_name)
        if new_name:
            self.data["tabs"][idx]["name"] = new_name
            self.nb.tab(idx, text=new_name)
            save(self.data)

    def _set_colors(self):
        """背景色を設定する"""
        colors = BG_COLORS[self.bg_idx]
        self.bg = colors[0]
        self.header_bg = colors[1]

    def close(self):
        """ウィンドウを閉じる"""
        save(self.data)  # データを保存
        self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.after(0, lambda: NoteWindow(self))

if __name__ == "__main__":
    App().mainloop()