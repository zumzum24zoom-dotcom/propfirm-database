' Startup entry: ensure the PFD Launcher server is running, WITHOUT opening the
' window. Lightweight (idle pythonw ~10-15MB) so it can live in shell:startup.
' The panel window is opened on demand by the ELECOM button (start.vbs).
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = scriptDir
sh.Run """" & scriptDir & "\start.bat"" server", 0, False
