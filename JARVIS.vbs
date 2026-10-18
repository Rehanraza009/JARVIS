' ==============================================================================
' JARVIS — High-Reliability Windows Launcher
' ==============================================================================
' Uses the verified Python 3.13 interpreter, maintains project directory context,
' logs startup diagnostics to data\startup_launcher.log, displays informative
' error messages if launch fails, and runs windowless without a lingering console.
' ==============================================================================

Option Explicit

Dim WshShell, fso, strPath, logPath, pythonExe
Dim potentialPaths, p, cmd, args, i, preCheckCode
Dim objLogFile

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 1. Determine absolute project root directory
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

' 2. Ensure data directory exists for logging
If Not fso.FolderExists(strPath & "\data") Then
    On Error Resume Next
    fso.CreateFolder(strPath & "\data")
    On Error GoTo 0
End If
logPath = strPath & "\data\startup_launcher.log"

' 3. Discover the correct Python executable
' Priority:
'   A. Local project virtual environment (.venv / venv)
'   B. Verified installation at C:\Python313\pythonw.exe
'   C. User AppData Python 3.13
'   D. ProgramFiles Python 3.13
'   E. Fallback to python.exe at C:\Python313\python.exe
pythonExe = ""

potentialPaths = Array( _
    strPath & "\.venv\Scripts\pythonw.exe", _
    strPath & "\venv\Scripts\pythonw.exe", _
    "C:\Python313\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"), _
    WshShell.ExpandEnvironmentStrings("%ProgramFiles%\Python313\pythonw.exe"), _
    "C:\Python313\python.exe" _
)

For Each p In potentialPaths
    If p <> "" And fso.FileExists(p) Then
        pythonExe = p
        Exit For
    End If
Next

' 4. If Python executable was not found, show user-friendly error dialog
If pythonExe = "" Then
    Dim missingErrMsg
    missingErrMsg = "JARVIS Launch Error:" & vbCrLf & vbCrLf & _
                    "The Python 3.13 interpreter required for JARVIS was not found." & vbCrLf & vbCrLf & _
                    "Checked locations:" & vbCrLf & _
                    " - C:\Python313\pythonw.exe" & vbCrLf & _
                    " - " & strPath & "\.venv\Scripts\pythonw.exe" & vbCrLf & _
                    " - %LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" & vbCrLf & vbCrLf & _
                    "Please verify your Python installation."
    
    On Error Resume Next
    Set objLogFile = fso.OpenTextFile(logPath, 8, True)
    If Err.Number = 0 Then
        objLogFile.WriteLine "[" & Now & "] [LAUNCHER_ERROR] " & missingErrMsg
        objLogFile.Close
    End If
    On Error GoTo 0
    
    MsgBox missingErrMsg, 16, "JARVIS Launcher Error"
    WScript.Quit 1
End If

' 5. Verify run_jarvis.py exists
If Not fso.FileExists(strPath & "\run_jarvis.py") Then
    Dim missingScriptMsg
    missingScriptMsg = "JARVIS Launch Error:" & vbCrLf & vbCrLf & _
                       "The entry point script was not found:" & vbCrLf & _
                       strPath & "\run_jarvis.py"
    
    On Error Resume Next
    Set objLogFile = fso.OpenTextFile(logPath, 8, True)
    If Err.Number = 0 Then
        objLogFile.WriteLine "[" & Now & "] [LAUNCHER_ERROR] " & missingScriptMsg
        objLogFile.Close
    End If
    On Error GoTo 0
    
    MsgBox missingScriptMsg, 16, "JARVIS Launcher Error"
    WScript.Quit 1
End If

' 6. Build command-line with forwarded arguments (e.g. --startup)
args = ""
For i = 0 To WScript.Arguments.Count - 1
    args = args & " " & """" & WScript.Arguments(i) & """"
Next

cmd = """" & pythonExe & """ """ & strPath & "\run_jarvis.py""" & args

' 8. Log invocation to startup_launcher.log
On Error Resume Next
Set objLogFile = fso.OpenTextFile(logPath, 8, True)
If Err.Number = 0 Then
    objLogFile.WriteLine ""
    objLogFile.WriteLine "------------------------------------------------------------"
    objLogFile.WriteLine "[" & Now & "] [LAUNCHER] Starting JARVIS..."
    objLogFile.WriteLine "[" & Now & "] [LAUNCHER] Python: " & pythonExe
    objLogFile.WriteLine "[" & Now & "] [LAUNCHER] WorkDir: " & strPath
    objLogFile.WriteLine "[" & Now & "] [LAUNCHER] Command: " & cmd
    objLogFile.Close
End If
On Error GoTo 0

' 9. Launch JARVIS asynchronously without a console window
WshShell.Run cmd, 0, False

Set WshShell = Nothing
Set fso = Nothing
