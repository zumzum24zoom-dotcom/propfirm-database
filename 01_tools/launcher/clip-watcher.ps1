#Requires -Version 5.1
# PFD Launcher — クリップボード監視ワーカー
#
# Windows のクリップボード "シーケンス番号"（変更のたびに増える軽量カウンタ）を
# ポーリングし、変化したときだけ内容を読み取って 1 行の JSON を stdout に出力する。
# テキストはそのまま、画像は PNG として ImageDir に保存しパスを返す。
# serve.py がこの stdout を読んで履歴に積む。
#
# 実行: powershell -sta -noprofile -ExecutionPolicy Bypass -File clip-watcher.ps1 -ImageDir <dir>
param([Parameter(Mandatory = $true)][string]$ImageDir)

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class ClipSeq {
  [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber();
}
"@

if (-not (Test-Path $ImageDir)) { New-Item -ItemType Directory -Path $ImageDir -Force | Out-Null }

function Emit([hashtable]$o) {
  try {
    [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress))
    [Console]::Out.Flush()
  } catch {
    exit   # stdout pipe closed → parent serve.py is gone, stop watching (no orphan)
  }
}

$lastSeq  = [ClipSeq]::GetClipboardSequenceNumber()
$lastText = ''

while ($true) {
  Start-Sleep -Milliseconds 500
  $seq = [ClipSeq]::GetClipboardSequenceNumber()
  if ($seq -eq $lastSeq) { continue }   # 変更なし → 読み取らない（軽量）
  $lastSeq = $seq
  try {
    if ([System.Windows.Forms.Clipboard]::ContainsText()) {
      $t = [System.Windows.Forms.Clipboard]::GetText()
      if ($t -and $t -ne $lastText) {     # 直前と同一テキストは無視（再コピーの重複抑制）
        $lastText = $t
        Emit @{ type = 'text'; text = $t }
      }
    }
    elseif ([System.Windows.Forms.Clipboard]::ContainsImage()) {
      $img = [System.Windows.Forms.Clipboard]::GetImage()
      if ($img) {
        $name = ([Guid]::NewGuid().ToString('N')) + '.png'
        $path = Join-Path $ImageDir $name
        $img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
        $w = $img.Width; $h = $img.Height
        $img.Dispose()
        $lastText = ''
        Emit @{ type = 'image'; file = $path; w = $w; h = $h }
      }
    }
  } catch {}
}
