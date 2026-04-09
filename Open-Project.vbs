' ============================================================
' Ideal-Now Diagram — Web UI Launcher
' Double-click this file to start the local review server
' and open it in your default browser.
' ============================================================

Dim shell, fso, projectDir, pythonCmd
Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonCmd   = "python """ & projectDir & "\serve.py"""

' Launch the server (hidden console window)
shell.Run "cmd /c cd /d """ & projectDir & """ && " & pythonCmd, 0, False

Set fso   = Nothing
Set shell = Nothing
