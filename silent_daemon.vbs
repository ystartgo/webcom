Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = ScriptDir
q = Chr(34)
cmd = "cmd.exe /c call " & q & ScriptDir & "\start_daemon.bat" & q & " __bg__"
WshShell.Run cmd, 0, False
