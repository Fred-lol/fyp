Option Explicit

' Run the local AquaLoad launcher with no PowerShell window left open.
Dim shell, command
Set shell = CreateObject("WScript.Shell")
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\fyp\StartAquaLoad.ps1"""
shell.Run command, 0, False

' Open the app for the laptop user. iPad users use the LAN address written
' to C:\fyp\AquaLoad-LAN-URL.txt after the launcher starts.
shell.Run "http://localhost:8501", 1, False
