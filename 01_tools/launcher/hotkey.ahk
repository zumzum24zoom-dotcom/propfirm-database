#Requires AutoHotkey v2.0
#SingleInstance Force
; PFD Launcher — グローバルホットキー常駐スクリプト
;
;   Insert : 右端サイドバーをトグル開閉（ネイティブ実装＝高速）
;
; 仕組み: 閉じる＝ウィンドウ破棄ではなく「非表示(WinHide)」。再表示は WinShow + ドックで
;         一瞬。初回だけブラウザ(--app)を起動する。ページは再読込されないので履歴等も保持。
; A_ScriptDir 起点でブラウザ/URLを解決 → 自宅/職場でクローン先パスが違っても動く。
; 常駐させるには setup-startup.ps1 を一度実行（shell:startup に登録）。
; Insert は一部エディタで挿入/上書き切替に使われるため、変えたい場合は下の Insert:: を変更。

SetTitleMatchMode 2
DetectHiddenWindows true

TITLE := "PFD Launcher"
URL   := "http://127.0.0.1:8765/01_tools/launcher/"
WIDTH := 360

Insert:: TogglePanel()

TogglePanel() {
    global TITLE
    id := WinExist(TITLE)
    if (id) {
        if DllCall("IsWindowVisible", "Ptr", id)
            WinHide("ahk_id " id)        ; 表示中 → 隠す（破棄しない＝次回が一瞬）
        else
            ShowDocked(id)               ; 隠れている → 出してドック
    } else {
        LaunchPanel()                    ; 無ければ初回起動
    }
}

ShowDocked(id) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    WinShow("ahk_id " id)
    WinMove(R - WIDTH, T, WIDTH, B - T, "ahk_id " id)
    WinSetAlwaysOnTop(1, "ahk_id " id)
    try WinActivate("ahk_id " id)
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
    if WinWait(TITLE, , 6)
        ShowDocked(WinExist(TITLE))
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
