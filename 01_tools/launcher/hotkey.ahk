#Requires AutoHotkey v2.0
#SingleInstance Force
; PFD Launcher — グローバルホットキー常駐スクリプト
;
;   Insert        : 右端サイドバーをトグル開閉
;
; A_ScriptDir 起点で start.vbs を呼ぶ → 自宅/職場でクローン先パスが違っても動く。
; 常駐させるには本ファイルのショートカット（または本体）を shell:startup に置く。
; Insert は一部エディタで挿入/上書き切替に使われるため、変えたい場合は下行のキー名を変更。

startVbs := A_ScriptDir "\start.vbs"

Insert:: Run('wscript.exe "' startVbs '"', A_ScriptDir)
