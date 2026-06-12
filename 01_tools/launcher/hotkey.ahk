#Requires AutoHotkey v2.0
#SingleInstance Force
; PFD Launcher — グローバルホットキー常駐スクリプト
;
;   Insert : 右端サイドバーをトグル開閉
;
; 方針: 確実さ最優先。AHK は WinShow/WinHide で出し入れするだけ（エラーの出ない最小構成）。
;       スライド（中身が右からスッと入る動き）はページ側の CSS が担当する
;       （index.html の visibilitychange → translateX）。閉じる時は即時。
;       しまう＝破棄ではなく非表示なので次が速い／履歴も保持。初回だけブラウザを起動。
; A_ScriptDir 起点でブラウザ/URLを解決 → 自宅/職場でクローン先パスが違っても動く。
; 常駐させるには setup-startup.ps1 を一度実行（shell:startup に登録）。
; Insert を変えたい場合は下の Insert:: を別キーに。

SetTitleMatchMode 2
DetectHiddenWindows true

TITLE := "PFD Launcher"
URL   := "http://127.0.0.1:8765/01_tools/launcher/"
WIDTH := 360

Insert:: TogglePanel()

TogglePanel() {
    global TITLE
    id := WinExist(TITLE)
    if (!id) {
        LaunchPanel()
        return
    }
    if DllCall("IsWindowVisible", "Ptr", id)
        WinHide("ahk_id " id)
    else
        ShowDocked(id)
}

ShowDocked(id) {
    global WIDTH
    MonitorGetWorkArea(MonitorGetPrimary(), &L, &T, &R, &B)
    WinMove(R - WIDTH, T, WIDTH, B - T, "ahk_id " id)
    WinShow("ahk_id " id)
    WinSetAlwaysOnTop(1, "ahk_id " id)
    try WinActivate("ahk_id " id)
}

LaunchPanel() {
    global TITLE, URL, WIDTH
    browser := FindBrowser()
    if (browser = "") {
        Run(URL)
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
