Option Explicit
Dim shell, fso, folder, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
cmd = "pyw.exe -3 """ & folder & "\detail_manager.py"""
shell.Run cmd, 0, False
