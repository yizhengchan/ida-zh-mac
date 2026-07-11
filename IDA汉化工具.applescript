(*
  IDA 通用汉化工具 - AppleScript 前端
  调用 ida_zh_installer.py 执行实际安装/卸载操作
*)

-- 获取当前 app bundle 中 Python 脚本的路径
set myPath to POSIX path of (path to me)
set resourcesPath to myPath & "Contents/Resources/"
set installerScript to resourcesPath & "ida_zh_installer.py"

-- 对话框配置
set titleText to "Mac IDA 通用一键汉化工具"
set authorText to "52pojie: RedFree (dylib 方案)  |  52pojie: m ra cry (一键打包)  |  Justin Chan (通用化改造, 多版本适配)"

-- 获取 IDA 列表
try
	set idaList to do shell script "python3 '" & installerScript & "' --list"
on error errMsg
	display dialog "无法运行安装器：" & return & errMsg buttons {"退出"} default button 1 with icon stop
	return
end try

-- 解析输出，构建菜单
set idaEntries to paragraphs of idaList
set menuItems to {}
set idaPaths to {}
set currentIndex to 0

repeat with i from 1 to count of idaEntries
	set entry to item i of idaEntries
	if entry starts with "  [" then
		set currentIndex to currentIndex + 1
		set labelText to text 7 thru -1 of entry

		try
			set AppleScript's text item delimiters to " — "
			set parts to text items of labelText
			set versionStr to item 1 of parts
			set statusStr to item 2 of parts
			set AppleScript's text item delimiters to ""
		on error
			set versionStr to labelText
			set statusStr to "未知"
		end try

		if statusStr contains "已安装" then
			set end of menuItems to "[" & currentIndex & "] " & versionStr & " [已汉化，选择将卸载汉化]"
		else
			set end of menuItems to "[" & currentIndex & "] " & versionStr & " [未汉化，选择将安装汉化]"
		end if

		set end of idaPaths to "/Applications/" & versionStr & ".app"
	end if
end repeat

-- 构建菜单文本
set menuText to titleText & return & return & authorText & return & return & "本汉化工具完全免费！" & return & return & "检测到以下 IDA：" & return
repeat with itemText in menuItems
	set menuText to menuText & return & itemText
end repeat
set menuText to menuText & return & return & "请输入序号操作（输入 0 退出）："

-- 弹出对话框
set userChoice to text returned of (display dialog menuText default answer "" buttons {"确定", "退出"} default button "确定" with title titleText)

if userChoice is "0" then return

-- 解析选择
try
	set choiceNum to userChoice as integer
	if choiceNum < 1 or choiceNum > currentIndex then
		display dialog "无效的序号。" buttons {"退出"} default button 1 with icon stop
		return
	end if
on error
	display dialog "请输入数字序号。" buttons {"退出"} default button 1 with icon stop
	return
end try

-- 获取 app 路径和操作类型
set idaAppPath to item choiceNum of idaPaths
set chosenEntry to item choiceNum of menuItems

if chosenEntry contains "卸载" then
	set action to "--uninstall"
else
	set action to "--install"
end if

-- 执行（带 --path 避免交互模式）
try
	set shellCmd to "python3 '" & installerScript & "' " & action & " --path '" & idaAppPath & "' 2>&1"
	set resultText to do shell script shellCmd with administrator privileges

	display dialog resultText buttons {"确定"} default button 1 with icon note
on error errMsg
	display dialog "操作失败：" & return & errMsg buttons {"退出"} default button 1 with icon stop
end try
