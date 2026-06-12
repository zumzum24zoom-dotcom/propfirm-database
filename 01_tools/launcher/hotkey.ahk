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

; 可視リージョンを「左から幅 w 分」に設定。ウィンドウを右へ動かしたとき、画面右端
; (= 2枚目モニター境界)を越えた部分を隠すために使う。w<=0 なら空＝不可視。
SetClipW(id, w, h) {
    if (w <= 0)
        rgn := DllCall("gdi32\CreateRectRgn", "Int", 0, "Int", 0, "Int", 0, "Int", 0, "Ptr")
    else
        rgn := DllCall("gdi32\CreateRectRgn", "Int", 0, "Int", 0, "Int", w, "Int", h, "Ptr")
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", rgn, "Int", 1)   ; 以後 rgn はOSが管理
}
ClearClip(id) {
    DllCall("user32\SetWindowRgn", "Ptr", id, "Ptr", 0, "Int", 1)     ; クリップ解除＝全面
}

; 右からスライドイン。ウィンドウを画面右端の外(x=R)から定位置(x=R-WIDTH)へ動かし、
; 右端を越える分はクリップで隠す → パネルが剛体のまま右から入ってくる。
ShowPanel(id) {
    global WIDTH, STEPS, STEP_MS
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    h  := B - T
    x0 := R - WIDTH
    SetClipW(id, 0, h)                              ; まず不可視
    WinMove(R, T, WIDTH, h, "ahk_id " id)           ; 右端の外へ
    WinShow("ahk_id " id)
    WinSetAlwaysOnTop(1, "ahk_id " id)
    try WinActivate("ahk_id " id)
    Loop STEPS {
        p := (STEPS - A_Index) / STEPS              ; 1→0
        x := x0 + Round(WIDTH * p)
        SetClipW(id, R - x, h)                      ; 先にクリップ(右はみ出しを隠す)
        WinMove(x, T, WIDTH, h, "ahk_id " id)       ; 後で移動 → 2枚目にチラ見えしない
        Sleep STEP_MS
    }
    ClearClip(id)
    WinMove(x0, T, WIDTH, h, "ahk_id " id)
}

; 右へスライドアウトしてから隠す。
HidePanel(id) {
    global WIDTH, STEPS, STEP_MS
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    h  := B - T
    x0 := R - WIDTH
    Loop STEPS {
        p := A_Index / STEPS                        ; 0→1
        x := x0 + Round(WIDTH * p)
        SetClipW(id, R - x, h)
        WinMove(x, T, WIDTH, h, "ahk_id " id)
        Sleep STEP_MS
    }
    WinHide("ahk_id " id)
    ClearClip(id)
    WinMove(x0, T, WIDTH, h, "ahk_id " id)          ; 次回のため定位置へ戻す
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
        WinMove(R - WIDTH, T, WIDTH, B - T, "ahk_id " id)
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
