import threading
import time
import sublime, sublime_plugin

refreshThreads = {}

#Enables autorefresh for the specified view
def enable_autorefresh_for_view(view):
	settings = sublime.load_settings('AutoRefresh.sublime-settings')
	refreshRate = 0.1

	if refreshThreads.get(view.id()) is None or not refreshThreads.get(view.id()).enabled:
		refreshThreads[view.id()] = RefreshThread(view, refreshRate)
		refreshThreads[view.id()].start()

#Disables autorefresh for the specified view.
#Does nothing if autorefresh was already disabled
def disable_autorefresh_for_view(view):
	if refreshThreads.get(view.id()) != None:
		refreshThreads[view.id()].enabled = False


#Commands
class EnableAutoRefreshCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		enable_autorefresh_for_view(self.view)

class DisableAutoRefreshCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		disable_autorefresh_for_view(self.view)

class AutoRefreshRememberFileCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		curFileName = self.view.file_name()
		if curFileName is None:
			return

		settings = sublime.load_settings('AutoRefresh.sublime-settings')
		autoRefreshFiles = settings.get('files_with_auto_refresh_enabled_on_load')

		if autoRefreshFiles is None or not isinstance(autoRefreshFiles, (list)):
			autoRefreshFiles = []

		global refreshThreads
		refreshThreadForCurView = refreshThreads.get(self.view.id())
		if refreshThreadForCurView is not None and refreshThreadForCurView.enabled:
			#Autorefresh is currently enabled
			if curFileName not in autoRefreshFiles:
				autoRefreshFiles.append(curFileName)
		else:
			#Autorefresh is currently disabled
			if curFileName in autoRefreshFiles:
				autoRefreshFiles.remove(curFileName)
		
		settings.set('files_with_auto_refresh_enabled_on_load', autoRefreshFiles)
		

#Event handler for editor events
class SublimeEventHandler(sublime_plugin.EventListener):
	def on_pre_close(self, view):
		disable_autorefresh_for_view(view)

	def on_load(self, view):
		settings = sublime.load_settings('AutoRefresh.sublime-settings')
		autoRefreshFiles = settings.get('files_with_auto_refresh_enabled_on_load')

		if autoRefreshFiles is None or not isinstance(autoRefreshFiles, (list)):
			print("Invalid files_with_auto_refresh_enabled_on_load setting")
			autoRefreshFiles = []

		curFileName = view.file_name()
		if curFileName is not None and curFileName in autoRefreshFiles:
			enable_autorefresh_for_view(view)


#Threading class that continuously reloads a file
class RefreshThread(threading.Thread):
	def __init__(self, view, refreshRate):
		self.view = view
		self.enabled = True
		self.refreshRate = refreshRate
		threading.Thread.__init__(self)

	def run(self):
		while True:
			sublime.set_timeout(self.reloadFile, 1)
			time.sleep(0.1)

	def reloadFile(self):
		row = self.view.rowcol(self.view.sel()[0].begin())[0] + 1
		rowCount = (self.view.rowcol(self.view.size())[0] + 1)

		self.view.run_command('revert')
		sublime.set_timeout(self.setView, 5)

	def setView(self):
		if not self.view.is_loading():
			self.view.run_command("move_to", {"to": "eof", "extend": "false"})
		else:
			sublime.set_timeout(self.setView, 5)
