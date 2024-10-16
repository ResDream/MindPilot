!macro customInstall

  Var Dialog
  Var InstallPythonCheckbox
  Var PythonPathText
  Var BrowseButton


  Function pgPythonOptions
    nsDialogs::Create 1018
    Pop $Dialog

    ${If} $Dialog == error
      Abort
    ${EndIf}

    ${NSD_CreateCheckbox} 10 10 100% 12u "安装Python环境"
    Pop $InstallPythonCheckbox

    ${NSD_CreateText} 10 30 70% 12u ""
    Pop $PythonPathText

    ${NSD_CreateButton} 75% 30 20% 12u "浏览"
    Pop $BrowseButton
    ${NSD_OnClick} $BrowseButton BrowseForPythonPath

    nsDialogs::Show
  FunctionEnd

  Function BrowseForPythonPath
    nsDialogs::SelectFolderDialog "选择Python安装路径" ""
    Pop $0
    ${If} $0 != error
      ${NSD_SetText} $PythonPathText $0
    ${EndIf}
  FunctionEnd

  Function pgPythonOptionsLeave
    ${NSD_GetState} $InstallPythonCheckbox $0
    ${NSD_GetText} $PythonPathText $1

    ${If} $0 == ${BST_CHECKED}
      ${If} $1 == ""
        MessageBox MB_OK "请选择Python安装路径"
        Abort
      ${EndIf}


      NSISdl::download "https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe" "$TEMP\python-installer.exe"
      ExecWait '"$TEMP\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 TargetDir="$1"'


      EnVar::SetHKCU "Path" "$1;$1\Scripts"


      ExecWait '"$1\python.exe" -m pip install -r "$INSTDIR\requirements.txt"'


      Delete "$TEMP\python-installer.exe"
    ${EndIf}
  FunctionEnd

  ; 在安装过程中插入自定义页面
  !insertmacro MUI_PAGE_CUSTOM pgPythonOptions pgPythonOptionsLeave
!macroend
