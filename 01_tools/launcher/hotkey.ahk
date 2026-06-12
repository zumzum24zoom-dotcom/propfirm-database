#Requires AutoHotkey v2.0
#SingleInstance Force
; PFD Launcher — グローバルホットキー常駐スクリプト
;
;   Insert : 右端サイドバーをトグル開閉（ネイティブ実装＝高速）
;
; 仕組み: しまう時はウィンドウを破棄せず「非表示(WinHide)」。開閉アニメは、ウィンドウの
;         可視リージョン(SetWindowRgn)を右端から伸縮させて実現する。背景パネルごと右から
;         開く/閉じる。ウィンドウは動かさず幅も変えないので、右の2枚目モニターにはみ出さず、
;         Chromeの最小幅制限にも当たらない。初回だけブラウザ(--app)を起動。ページは再読込
;         されないので履歴等も保持。
; A_ScriptDir 起点でブラウザ/URLを解決 → 自宅/職場でクローン先パスが違っても動く。
; 常駐させるには setup-startup.ps1 を一度実行（shell:startup に登録）。
; Insert は一部エディタで挿入/上書き切替に使われるため、変えたい場合は下の Insert:: を変更。

SetTitleMatchMode 2
DetectHiddenWindows true

TITLE := "PFD Launcher"
URL   := "http://127.0.0.1:8765/01_tools/launcher/"
WIDTH := 360
STEPS := 16        ; スライドの分割数
STEP_MS := 7       ; 1コマの待ち(ms) → 16*7≈112ms

Insert:: TogglePanel()

TogglePanel() {
    global TITLE
    id := WinExist(TITLE)
    if (id) {
        if DllCall("IsWindowVisible", "Ptr", id)
            HidePanel(id)                ; 表示中 → 右へ閉じてから隠す
        else
            ShowPanel(id)                ; 隠れている → 右から開く
    } else {
        LaunchPanel()                    ; 無ければ初回起動
    }
}

; 可視リージョンを [leftX, 0, WIDTH, height] に設定（右側 WIDTH-leftX 分だけ見える）。
SetClip(id, leftX) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    rgn := DllCall("gdi32\CreateRectRgn", "Int", leftX, "Int", 0, "Int", WIDTH, "Int", (B - T), "Ptr")
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", rgn, "Int", 1)   ; 以後 rgn はOSが管理
}
ClearClip(id) {
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", 0, "Int", 1)     ; クリップ解除＝全面
}

Dock(id) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    WinMove(R - WIDTH, T, WIDTH, B - T, "ahk_id " id)
}

ShowPanel(id) {
    global WIDTH, STEPS, STEP_MS
    Dock(id)
    SetClip(id, WIDTH)                    ; 先に「幅0」にクリップ（チラ見え防止）
    WinShow("ahk_id " id)
    WinSetAlwaysOnTop(1, "ahk_id " id)
    try WinActivate("ahk_id " id)
    Loop STEPS {                          ; 右端から左へ開く
        leftX := Round(WIDTH * (STEPS - A_Index) / STEPS)
        SetClip(id, leftX)
        Sleep STEP_MS
    }
    ClearClip(id)
}

HidePanel(id) {
    global WIDTH, STEPS, STEP_MS
    Loop STEPS {                          ; 左から右へ閉じる
        leftX := Round(WIDTH * A_Index / STEPS)
        SetClip(id, leftX)
        Sleep STEP_MS
    }
    WinHide("ahk_id " id)
    ClearClip(id)                         ; 隠している間は全面に戻しておく
}

LaunchPanel() {
    global TITLE, URL, WIDTH
    browser := FindBrowser()
    if (browser = "") {
        Run(URL)                         ; 最後の手段：既定ブラウザ（ドック不可）
        return
    }
    udir := EnvGet("LOCALAPPDATA") "\PFDLauncher\edge-profile"
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    x := R - WIDTH
    flags := Format('--app={1} --user-data-dir="{2}" --window-position={3},{4} --window-size={5},{6}'
        . ' --no-first-run --no-default-browser-check --no-service-autorun --disable-sync'
        . ' --disable-features=msEdgeFirstRunExperience,EdgeWelcomeEnabled,WelcomeExperienceEnabled,msUndersideButton',
        URL, udir, x, T, WIDTH, B - T)
    Run('"' browser '" ' flags)
    if WinWait(TITLE, , 6) {              ; 初回はそのまま全面表示（1回だけポップ）
        id := WinExist(TITLE)
        Dock(id)
        WinSetAlwaysOnTop(1, "ahk_id " id)
        try WinActivate("ahk_id " id)
    }
}

FindBrowser() {
    pf  := EnvGet("ProgramFiles")
    pfx := EnvGet("ProgramFiles(x86)")
    for path in [pf  "\Google\Chrome\Application\chrome.exe",
                 pfx "\Google\Chrome\Application\chrome.exe",
                 pf  "\Microsoft\Edge\Application\msedge.exe",
                 pfx "\Microsoft\Edge\Application\msedge.exe"] {
        if FileExist(path)
            return path
    }
    return ""
}
