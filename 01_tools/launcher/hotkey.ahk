#Requires AutoHotkey v2.0
#SingleInstance Force
; PFD Launcher — グローバルホットキー常駐スクリプト
;
;   Insert : 右端サイドバーをトグル開閉（ネイティブ実装＝高速）
;
; 仕組み: しまう時はウィンドウを破棄せず「非表示(WinHide)」。スライドは CSS transform
;         (GPUで滑らか)がページ側で中身を動かし、AHKは同時にウィンドウの可視リージョンを
;         同じ時間配分でクリップして「中身が退避した白いウィンドウ領域」を隠す。両者は
;         時間ベース(200ms linear)で同期するので、白枠が出ずに中身ごと右へスライドして
;         見える。ウィンドウは動かさない＝Chromeの再描画が走らずカクつかない。右の2枚目
;         モニターにもはみ出さない。初回だけブラウザ(--app)を起動。
; A_ScriptDir 起点でブラウザ/URLを解決 → 自宅/職場でクローン先パスが違っても動く。
; 常駐させるには setup-startup.ps1 を一度実行（shell:startup に登録）。
; Insert は一部エディタで挿入/上書き切替に使われるため、変えたい場合は下の Insert:: を変更。

SetTitleMatchMode 2
DetectHiddenWindows true

TITLE := "PFD Launcher"
URL   := "http://127.0.0.1:8765/01_tools/launcher/"
WIDTH := 360
DUR   := 200        ; スライド時間(ms)。CSSの transition と一致させること

Insert:: TogglePanel()

TogglePanel() {
    global TITLE
    id := WinExist(TITLE)
    if (id) {
        if DllCall("IsWindowVisible", "Ptr", id)
            HidePanel(id)                ; 表示中 → スライドアウトして隠す
        else
            ShowPanel(id)                ; 隠れている → スライドイン
    } else {
        LaunchPanel()                    ; 無ければ初回起動
    }
}

; 可視リージョンを [leftX, 0, WIDTH, h]（右側 WIDTH-leftX 分が見える）に設定。
SetClip(id, leftX) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    rgn := DllCall("gdi32\CreateRectRgn", "Int", leftX, "Int", 0, "Int", WIDTH, "Int", (B - T), "Ptr")
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", rgn, "Int", 1)
}
ClearClip(id) {
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", 0, "Int", 1)
}

; CSSの translateX(0↔100%)に合わせて leftX(0↔WIDTH)を時間ベースで動かす。
Animate(id, opening) {
    global WIDTH, DUR
    DllCall("winmm\timeBeginPeriod", "UInt", 1)   ; Sleep精度を1msに（カクつき防止）
    t0 := A_TickCount
    Loop {
        el := A_TickCount - t0
        if (el >= DUR)
            break
        f := el / DUR                              ; 0→1
        leftX := opening ? (WIDTH * (1 - f)) : (WIDTH * f)
        SetClip(id, Round(leftX))
        Sleep 5
    }
    SetClip(id, opening ? 0 : WIDTH)               ; 最終コマ
    DllCall("winmm\timeEndPeriod", "UInt", 1)
}

Dock(id) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    WinMove(R - WIDTH, T, WIDTH, B - T, "ahk_id " id)
}

ShowPanel(id) {
    global WIDTH
    Dock(id)
    SetClip(id, WIDTH)                   ; まず不可視（中身も translateX(100%) で退避中）
    WinShow("ahk_id " id)
    WinSetAlwaysOnTop(1, "ahk_id " id)
    try WinActivate("ahk_id " id)
    try Send("{F13}")                    ; CSSスライドイン開始（visibilitychangeでも保険）
    Animate(id, true)                    ; リージョンを同期で開く
    ClearClip(id)
}

HidePanel(id) {
    try WinActivate("ahk_id " id)        ; キーがページに届くよう前面化
    Sleep 20
    try Send("{F14}")                    ; CSSスライドアウト開始
    Animate(id, false)                   ; リージョンを同期で閉じる
    WinHide("ahk_id " id)
    ClearClip(id)
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
    if WinWait(TITLE, , 6) {
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
