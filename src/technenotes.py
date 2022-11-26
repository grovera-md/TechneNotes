import json
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, Pango, GObject, GtkSource, GLib, WebKit2, Gio
from peewee import *
import datetime
import dbRepository as dbRepo
import menuBarLogic
import toolBarLogic
import treeviewDnDLogic
from customNotebookTab import notebookTab
import dialogNewNote
import dialogEditNote
import dialogCloseTab
import dialogDeleteOpenedNote
import dialogPreferences
import dialogFirstSetup
import dialogInsertMedia
import os
import sys
import shutil
from pathlib import Path
import renderMarkdown
import math
import uuid
from PIL import Image

# Docs/Required_system_files
# For the application to work properly, the following system files should be set in the installation process:
# 1) GSettings files
#    The '/usr/share/glib-2.0/schemas/ovh.technenotes.myapp.gschema.xml' file should be created and the command 'glib-compile-schemas /usr/share/glib-2.0/schemas/' should be run
# 2) GtkSource syntax highlighting files
#    - '/home/[user]/.local/share/gtksourceview-3.0/language-specs/markdown-extra-tech.lang'
#    - '/home/[user]/.local/share/gtksourceview-3.0/styles/codezone-tech.xml'
# 3) New system fonts
#    At least the "Lato-Regular" font should be added to the system fonts (by copying the files "Lato-Regular.ttf" and "SIL Open Font License.txt" to the '/home/[user]/.local/share/fonts/Lato-Regular' directory)
#
# In case of syntax highlighting errors with javascript code, copy/paste this file:
#    - '/home/[user]/.local/share/gtksourceview-3.0/language-specs/javascript.lang' (this files solves the issue of conflicting syntax definition in newer distros)


class TechneNotes(Gtk.Window):

    def __init__(self):
        # Create a new window
        Gtk.Window.__init__(self, title="TechneNotes")
        self.set_default_size(500, 500)

        icontheme = Gtk.IconTheme.get_default()
        self.icon = icontheme.load_icon(Gtk.STOCK_FLOPPY, 128, 0)
        self.set_icon(self.icon)

        self.notebookTabs = []
        self.currentTab = None
        self.toolButtonsDict = None

        self.displaySearchTermModeOn = False
        self.displayToggledOnlyModeOn = False
        self.toggledRowsDict = dict()
        self.searchTerm = ''

        # TODO (START): These parameters will be retrieved from the db, but for now they will be a hardcoded constant
        self.resultsPerPage = 10
        self.totalResultPagesNum = 1  # This value will be re-calculated as soon as the db connection is initialized
        self.resultsPageNum = 1
        self.orderByColumn = 1 # Possible values: 0 = customOrder, 1 = title, 2 = created, 3 = lastUpdated
        # self.offset = 0
        self.orderAsc = True
        # self.viewcomboPref = 0 # 0 = code & preview, 1 = code only, 2 = preview only
        # TODO (END)

        self.treeviewDndEnabled = True
        self.treeviewDoubleClicked = False # Possible values: False or int (=notebook page to switch to)

        # Set GSettings listeners
        self.BASE_KEY = "ovh.technenotes.myapp"
        self.settings = Gio.Settings.new(self.BASE_KEY)
        # Settings names list (note: corresponding temporary-settings names can be derived adding "-tmp" at the end of the corresponding definitive-setting name)
        self.doubleValueSettingsList = ["code-font", "db-path", "assets-folder-path"]
        # TODO: For now the self.singleValueSettingsList is not used, since when saving/canceling the preferenceDialog all singleValueSettings must be processed differently (listeners not applicable)
        self.singleValueSettingsList = ["webview-css-mod-flag"]
        self.settings_setup_listeners()

        self.vbox = Gtk.VBox()
        #MENUBAR setup
        menuBar = Gtk.MenuBar()        
        #set helpers
        self.agr = Gtk.AccelGroup()
        self.add_accel_group(self.agr)
        #populate menuBar, return dictionary of menuItems as result and set menu callbacks
        self.menuItemsDict = menuBarLogic.setupMenuBar(menuBar, self.agr)
        # self.menuItemsMain = {self.menuItemsDict["File"]["Insert new before"], self.menuItemsDict["File"]["Insert new after"], self.menuItemsDict["File"]["Insert new as child"], self.menuItemsDict["File"]["Export..."], self.menuItemsDict["File"]["Backup / Export all..."], self.menuItemsDict["File"]["Import..."], self.menuItemsDict["Edit"]["Delete"]}
        self.menuItemsMain = {self.menuItemsDict["File"]["New..."], self.menuItemsDict["Edit"]["Delete"]}
        # Temporary removed items: self.menuItemsDict["File"]["Export..."], self.menuItemsDict["File"]["Backup / Export all..."], self.menuItemsDict["File"]["Import..."],
        self.menuItemsEditor = {self.menuItemsDict["File"]["Save"], self.menuItemsDict["Edit"]["Undo"], self.menuItemsDict["Edit"]["Redo"], self.menuItemsDict["Edit"]["Cut"], self.menuItemsDict["Edit"]["Copy"], self.menuItemsDict["Edit"]["Paste"], self.menuItemsDict["Edit"]["Select All"], self.menuItemsDict["Edit"]["Insert Media"], self.menuItemsDict["Edit"]["Render Markdown"], self.menuItemsDict["Search"]["Find"], self.menuItemsDict["Search"]["FindReplace"]}
        self.menuItemsDict["File"]["New..."].connect("activate", self.on_toolbutton_new_clicked)
        self.menuItemsDict["File"]["Save"].connect("activate", self.on_toolbutton_save_clicked)
        self.menuItemsDict["File"]["Exit"].connect("activate", self.customQuit)
        self.menuItemsDict["Edit"]["Undo"].connect("activate", self.on_toolbutton_undo_clicked)
        self.menuItemsDict["Edit"]["Redo"].connect("activate", self.on_toolbutton_redo_clicked)
        self.menuItemsDict["Edit"]["Cut"].connect("activate", self.on_toolbutton_cut_clicked)
        self.menuItemsDict["Edit"]["Copy"].connect("activate", self.on_toolbutton_copy_clicked)
        self.menuItemsDict["Edit"]["Paste"].connect("activate", self.on_toolbutton_paste_clicked)
        self.menuItemsDict["Edit"]["Insert Media"].connect("activate", self.on_toolbutton_insert_media_clicked)
        self.menuItemsDict["Edit"]["Select All"].connect("activate", self.on_toolbutton_select_all_clicked)
        self.menuItemsDict["Edit"]["Render Markdown"].connect("activate", self.on_toolbutton_render_markdown_clicked)
        self.menuItemsDict["Edit"]["Delete"].connect("activate", self.on_toolbutton_delete_clicked)
        self.menuItemsDict["Edit"]["Preferences"].connect("activate", self.on_preferences_clicked)
        self.menuItemsDict["Search"]["Find"].connect("activate", self.on_toolbutton_find_clicked)
        self.menuItemsDict["Search"]["FindReplace"].connect("activate", self.on_toolbutton_find_replace_clicked)
        self.menuItemsDict["Help"]["About"].connect("activate", self.on_toolbutton_about_clicked)

        #add menuBar to the window
        self.vbox.pack_start(menuBar, False, False, 0)
        
        #TOOLBAR setup
        toolBar = Gtk.Toolbar()
        toolBar.set_show_arrow(False)
        #populate toolBar, return dictionary of toolButtons as result and set button callbacks
        toolButtonsDict = toolBarLogic.setupToolBar(toolBar, self.orderByColumn, self.orderAsc, self.totalResultPagesNum)
        self.toolButtonsDict = toolButtonsDict
        toolButtonsDict["new"].connect("clicked", self.on_toolbutton_new_clicked)
        #toolButtonsDict["open"].connect("clicked", self.on_toolbutton_open_clicked)
        toolButtonsDict["delete"].connect("clicked", self.on_toolbutton_delete_clicked)
        toolButtonsDict["save"].connect("clicked", self.on_toolbutton_save_clicked)
        toolButtonsDict["undo"].connect("clicked", self.on_toolbutton_undo_clicked)
        toolButtonsDict["redo"].connect("clicked", self.on_toolbutton_redo_clicked)
        toolButtonsDict["find"].connect("clicked", self.on_toolbutton_find_clicked)
        toolButtonsDict["findReplace"].connect("clicked", self.on_toolbutton_find_replace_clicked)
        toolButtonsDict["renderMarkdown"].connect("clicked", self.on_toolbutton_render_markdown_clicked)
        toolButtonsDict["noteDetails"].connect("clicked", self.on_toolbutton_note_details_clicked)
        toolButtonsDict["view"].connect("changed", self.on_views_combo_changed)
        # toolButtonsDict["search"].connect("search-changed", self.on_search_entry_changed)
        toolButtonsDict["search"].connect("activate", self.on_search_entry_activated)
        toolButtonsDict["toggledOnlyMode"].connect("toggled", self.on_toggled_only_mode_toggled)
        toolButtonsDict["goPrevious"].connect("clicked", self.on_toolbutton_go_previous_clicked)
        toolButtonsDict["goNext"].connect("clicked", self.on_toolbutton_go_next_clicked)
        toolButtonsDict["goToPage"].connect("activate", self.on_gotopage_entry_activated)
        toolButtonsDict["pageResults"].connect("changed", self.on_rows_combo_changed)
        toolButtonsDict["orderBy"].connect("changed", self.on_order_combo_changed)
        toolButtonsDict["orderDir"].connect("changed", self.on_dir_combo_changed)
        self.vbox.pack_start(toolBar, False, False, 0)

        self.toolBtnGroupMain = {toolButtonsDict["new"], toolButtonsDict["delete"], toolButtonsDict["search"], toolButtonsDict["toggledOnlyMode"], toolButtonsDict["goPrevious"], toolButtonsDict["goNext"], toolButtonsDict["goToPage"], toolButtonsDict["pageResults"], toolButtonsDict["orderBy"], toolButtonsDict["orderDir"]}
        self.toolBtnGroupEditor = {toolButtonsDict["save"], toolButtonsDict["undo"], toolButtonsDict["redo"], toolButtonsDict["find"], toolButtonsDict["findReplace"], toolButtonsDict["renderMarkdown"], toolButtonsDict["noteDetails"], toolButtonsDict["view"]}
        
        self.notebook = Gtk.Notebook()
        self.vbox.pack_start(self.notebook, True, True, 0)
        
        #add scrolledwindow to the first notebook tab
        main_tab_label = Gtk.Label.new("Main ")
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.notebook.append_page(self.scrolledwindow, main_tab_label)
        self.notebook.set_tab_reorderable(self.scrolledwindow, True)

        # create a Treestore
        self.store = Gtk.TreeStore(int, bool, str, str, float, int, int, str, str)

        # Check if db-path and assets-folder-path are already set in GSettings or trigger the first-launch-setup dialog
        dbFilePathSetting = self.settings.get_string("db-path")
        assetsFolderPathSetting = self.settings.get_string("assets-folder-path")

        if len(dbFilePathSetting) > 0 and len(assetsFolderPathSetting) > 0:
            # Db folder path has already been set.
            # Initialize Peewee db with saved path
            dbRepo.db.init(dbFilePathSetting)
            dbRepo.db.connect()
            # Load treeview results
            self.store = dbRepo.populateTreestore(self.store, dbRepo.findAllResults(self.orderByColumn, self.orderAsc, self.resultsPerPage, self.calculate_results_offset(), self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm), self.toggledRowsDict)
            self.totalResultPagesNum = dbRepo.findLastResultsPageNum(self.resultsPerPage, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm)
        else:
            # First launch of the app - Show setup dialog
            setupDialog = dialogFirstSetup.DialogFirstSetup(self)
            setupDialogResponse = setupDialog.run()
            if setupDialogResponse == Gtk.ResponseType.OK:
                # Initialize new Peewee db with selected path and connect to it. If db is newly created, also create the tables and add the sampleNote.
                # Note: The connect() method also creates the actual file if it doesn't exist.

                # Retrieve setupDialog info. Note - dialogDbSelectedOption: 1= new db, 2= open existing db
                selectedDbOption = setupDialog.getSelectedDbOption()
                dbFilePath = setupDialog.getDbFilename()
                assetsFolderPath = setupDialog.getAssetsFolderPath()
                mediaCheckboxValue = setupDialog.getMediaCheckboxValue()

                # If db is newly created, delete any previous db file, create the tables and add the sample notes.
                # Otherwise simply initialize the db and connect to it
                if selectedDbOption == 1:
                    # Delete any previous db file
                    if os.path.exists(dbFilePath):
                        os.remove(dbFilePath)
                    # Initialize the db and connect to it
                    dbRepo.db.init(dbFilePath)
                    dbRepo.db.connect()
                    # Create tables in the database
                    dbRepo.db.create_tables([dbRepo.Note, dbRepo.Snippet])
                    # Add the markdownSample + includeSample records in the db (markdownSample.txt file in the data folder)
                    sampleNoteFile = open("../data/markdownSample.txt", "r")
                    sampleNoteStr = sampleNoteFile.read()
                    sampleNoteFile.close()
                    sampleNoteObj = dbRepo.Note.create(title="Markdown Sample", description="Features description", content=sampleNoteStr, parent=None, custom_order=1, fraction_num=1, fraction_denom=1)
                    sampleIncludeFile = open("../data/includeSample.txt", "r")
                    sampleIncludeStr = sampleIncludeFile.read()
                    sampleIncludeFile.close()
                    sampleIncludeObj = dbRepo.Note.create(title="Include Sample", description="Include feature example", content=sampleIncludeStr, parent=None, custom_order=2, fraction_num=2, fraction_denom=1)

                else:
                    # Initialize the db and connect to it
                    dbRepo.db.init(dbFilePath)
                    dbRepo.db.connect()

                # If assetsFolderPath != projectRoot/assets, then copy the sampleMedia folder inside the new assetsFolderPath
                # localAssetsFolderPath = os.path.abspath("../assets")
                # if assetsFolderPath != localAssetsFolderPath:
                #     shutil.move(localAssetsFolderPath+'/sample_media', assetsFolderPath+'/sample_media')

                # If mediaCheckBox is flagged, copy the 'data/sample_media' folder in the selected assets folder. Conflicting files will be automatically overridden.
                if mediaCheckboxValue:
                    shutil.copytree('../data/sample_media', assetsFolderPath + '/sample_media', dirs_exist_ok=True)

                # Save new values to GSettings
                self.settings.set_string("db-path", dbFilePath)
                self.settings.set_string("db-path-tmp", dbFilePath)
                self.settings.set_string("assets-folder-path", assetsFolderPath)
                self.settings.set_string("assets-folder-path-tmp", assetsFolderPath)

                # Load treeview results
                self.store = dbRepo.populateTreestore(self.store, dbRepo.findAllResults(self.orderByColumn, self.orderAsc, self.resultsPerPage, self.calculate_results_offset(), self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm), self.toggledRowsDict)
                self.totalResultPagesNum = dbRepo.findLastResultsPageNum(self.resultsPerPage, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm)

            elif setupDialogResponse == Gtk.ResponseType.CANCEL:
                # Exit the app
                sys.exit("App setup canceled")
            else:
                # Exit the app
                sys.exit("App setup canceled")

            setupDialog.destroy()

        # Disable treestore/treeview sorting - ALSO see the section below about column sorting
        # self.store.set_sort_column_id(Gtk.TREE_SORTABLE_UNSORTED_SORT_COLUMN_ID, Gtk.SortType.ASCENDING)

        # Enable treestore/treeview automatic sorting
        customSortColumnId = self.find_custom_sort_column_id(self.orderByColumn)
        self.store.set_sort_func(4, self.custom_sort_function, None)
        self.store.set_sort_func(2, self.custom_sort_function, None)
        self.store.set_sort_func(7, self.custom_sort_function, None)
        self.store.set_sort_func(8, self.custom_sort_function, None)
        self.store.set_sort_column_id(customSortColumnId, not self.orderAsc)

        # create the TreeView using liststore
        self.treeview = Gtk.TreeView.new_with_model(self.store)
        # allow multiple selection
        sel = self.treeview.get_selection()
        sel.set_mode(Gtk.SelectionMode.MULTIPLE)
        sel.set_select_function(treeviewDnDLogic.rowSelectionFunction, None)
        # Create CellRenderers to render data
        self.cell_toggle = Gtk.CellRendererToggle()
        self.cell_toggle.set_activatable(True)
        self.cell_title = Gtk.CellRendererText()
        self.cell_title.set_padding(5, 2)
        self.cell_description = Gtk.CellRendererText()
        self.cell_description.set_padding(10, 2)
        self.cell_created = Gtk.CellRendererText()
        self.cell_created.set_padding(10, 2)
        self.cell_last_updated = Gtk.CellRendererText()
        self.cell_last_updated.set_padding(10, 2)
        # create the TreeViewColumns to display the data
        self.column_toggle = Gtk.TreeViewColumn("Toggle", self.cell_toggle, active=1)
        self.column_toggle.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.column_title = Gtk.TreeViewColumn('Title', self.cell_title, text=2) # changed from 1 to 2
        self.column_title.set_max_width(300)
        self.column_title.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.column_title.set_expand(True)
        self.column_description = Gtk.TreeViewColumn('Description', self.cell_description, text=3) # changed from 2 to 3
        self.column_description.set_max_width(150)
        self.column_description.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.column_description.set_expand(True)
        self.column_created = Gtk.TreeViewColumn('Created', self.cell_created, text=7) # changed from 6 to 7
        self.column_created.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        # self.column_created.set_spacing(20)
        self.column_last_updated = Gtk.TreeViewColumn('Last updated', self.cell_last_updated, text=8) # changed from 7 to 8
        self.column_last_updated.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        # add columns to treeview
        self.treeview.append_column(self.column_toggle)
        self.treeview.append_column(self.column_title)
        self.treeview.append_column(self.column_description)
        self.treeview.append_column(self.column_created)
        self.treeview.append_column(self.column_last_updated)
        # make treeview searchable
        self.treeview.set_search_column(2)
        # Allow sorting on the column
        #self.column_title.set_sort_column_id(1)
        #self.column_description.set_sort_column_id(2)
        #self.column_created.set_sort_column_id(6)
        #self.column_last_updated.set_sort_column_id(7)
        # Allow enable drag and drop of rows including row move
        self.defer_select = False
        treeviewDnDLogic.enableDnd(self.treeview)

        # Connect signals
        self.cell_toggle.connect("toggled", self.treeview_on_cell_toggled)
        self.treeview.connect("drag_data_get", self.drag_data_get_data)
        self.treeview.connect("drag_data_received", self.drag_data_received_data)
        self.treeview.connect("row_activated", self.treeview_on_row_activated)
        self.treeview.connect('button_press_event', self.on_button_press)
        self.treeview.connect('button_release_event', self.on_button_release)
        self.treeview.connect("key_press_event", self.treeview_on_key_press_event)
        self.notebook.connect("switch-page", self.on_notebook_switch_page)
        self.notebook.connect("page-reordered", self.on_notebook_page_reordered)

        self.scrolledwindow.add(self.treeview)
        self.add(self.vbox)

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.treeview.grab_focus()

    def customQuit(self, widget=None):
        self.close() # Requests that the window is closed, similar to what happens when a window manager close button is clicked. So, the "delete-event" will also be correctly triggered.

    def calculate_results_offset(self):
        offset = self.resultsPerPage * (self.resultsPageNum-1)
        return offset

    def find_custom_sort_column_id(self, orderByColumn):
        if orderByColumn == 0:
            order_column_id = 4
        elif orderByColumn == 1:
            order_column_id = 2
        elif orderByColumn == 2:
            order_column_id = 7
        elif orderByColumn == 3:
            order_column_id = 8
        else:
            order_column_id = 2

        return order_column_id

    # A custom sort function is NECESSARY in order to specify a secondary sort parameter (= dbId), ensuring a UNIQUE ordering even when the primary sort parameter is equal.
    # This is important to guarantee that the result of the findNextResults() method will always be unique and reproducible, otherwise a duplicate record could be appended to the treeview.
    # The findNextResults() method is used when some action (ex. row deletion, d&d) causes a reduction in the total root items count and it is necessary to append new rows.
    def custom_sort_function(self, model, row1, row2, user_data):
        sort_column, _ = model.get_sort_column_id()
        value1 = model.get_value(row1, sort_column)
        value2 = model.get_value(row2, sort_column)
        if value1 < value2:
            return -1
        elif value1 == value2:
            # Add secondary criterion for sorting: dbId - Since dbId is unique, there will never be uncertain cases.
            value3 = model.get_value(row1, 0)
            value4 = model.get_value(row2, 0)
            if value3 < value4:
                return -1
            else:
                return 1
        else:
            return 1

    def drag_data_get_data(self, treeview, context, selection, target_id, etime):
        treeviewDnDLogic.dragDataGet(treeview, context, selection, target_id, etime)

    def drag_data_received_data(self, treeview, context, x, y, selection, info, etime):
        resultDict = treeviewDnDLogic.dragDataReceived(treeview, context, x, y, selection, info, etime, self.defer_select, self.orderByColumn, self.orderAsc, self.resultsPageNum, self.resultsPerPage, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm)
        self.defer_select = resultDict["defer_select"]
        rootItemsNetBalance = resultDict["balance"]
        movedItemsDbIdList = resultDict["movedItemsDbIdList"]
        # Check if the movedItem dbId corresponds to the Id of one of the currently opened notes OR one of its parents. If so, update the Path displayed in the Revealer section.
        # Note: checking for context.get_actions() == Gdk.DragAction.MOVE or len(movedItemsDbIdList) > 0 is the same
        if len(movedItemsDbIdList) > 0:
            for dbId in movedItemsDbIdList:
                for tab in self.notebookTabs:
                    if dbId == tab.noteDbId or dbId in tab.recursiveDbIdPathList:
                        # Update the currentTab.recursiveDbIdPath
                        recursiveDbIdPath = dbRepo.findRecursivePathByDbId(tab.noteDbId)
                        self.currentTab.recursiveDbIdPathList = [subdict["id"] for subdict in recursiveDbIdPath]
                        # Update the displayed notebookTab PathBox and connect its buttons widget with callback
                        tab.createRecursiveDbIdPathBox(recursiveDbIdPath)
                        for button in tab.pathButtonsList:
                            button.connect("clicked", self.on_note_path_button_clicked)

        # TODO: refresh resultsPageTotalNum after d&d (note: this query doesn't depend on the order_by criteria - just count the total root items) - Eventually limit its call when d&d actions are performed on root level
        if rootItemsNetBalance != 0:
            self.updateTotalResultPagesNum()

    # Docs/GSettings_strategy
    # At startup, the app will retrieve the self.settings object and call this method to register all the necessary listeners on all settings variables.
    # In the settings file (/usr/share/glib-2.0/schemas/ovh.technenotes.myapp.gschema.xml), two settings will be defined for each option:
    # one definitive setting (e.g. "code-font") and one temporary setting (e.g. "code-font-tmp").
    # Changing the option value inside the Preferences dialog will only affect the temporary setting value (calling the relative listener method, allowing to preview changes).
    # At this point, there are two possible events: 1) The user exits the dialog by clicking "Cancel" 2) The user saves the settings (with/without changes) by clicking the "OK/Save" button
    # 1) If the user aborts changes, each temporary setting will be checked against the corresponding definitive setting value and be reset to its original value if different
    # 2) If the user saves changes, each definitive setting will be checked against the corresponding temporary setting value and be set to its new value if different
    # In each case, the corresponding listener method will be triggered and preview-changes will be reset (in case 1) or new changes will be applied (in case 2).
    def settings_setup_listeners(self):
        self.settings.connect("changed::code-font", self.on_gsetting_codefont_changed)
        self.settings.connect("changed::code-font-tmp", self.on_gsetting_codefont_tmp_changed)

    def on_gsetting_codefont_changed(self, settings, key):
        # Update the GtkSource font-style of all notebook tabs
        if len(self.notebookTabs) > 0:
            fontString = settings.get_string("code-font")
            for tab in self.notebookTabs:
                tab.sourceview.modify_font(Pango.FontDescription.from_string(fontString))  # fontString is a string representation of a Pango.FontDescription object

    def on_gsetting_codefont_tmp_changed(self, settings, key):
        # Update the font-style of the self.currentTab (if there is at least one tab opened)
        if self.currentTab:
            fontString = settings.get_string("code-font-tmp")
            self.currentTab.sourceview.modify_font(Pango.FontDescription.from_string(fontString))  # fontString is a string representation of a Pango.FontDescription object

    def on_gsetting_dbpath_changed(self, currentFilePath, newFilePath):
        # Close db connection
        dbRepo.db.close()
        # Move db file
        newFolderPath = os.path.dirname(os.path.realpath(newFilePath))
        shutil.move(currentFilePath, newFolderPath)
        # Re-initialize db connection
        dbRepo.db.init(newFilePath)
        dbRepo.db.connect()

    def on_gsetting_assetspath_changed_pre(self, currentFolderPath, newFolderPath):
        fileNames = os.listdir(currentFolderPath)
        for fileName in fileNames:
            shutil.move(os.path.join(currentFolderPath, fileName), newFolderPath)

    def on_gsetting_assetspath_changed_post(self):
        # Re-render any opened tab (if any)
        if len(self.notebookTabs) > 0:
            for tab in self.notebookTabs:
                self.clear_tab_webview_cache(tab)
                self.render_notebooktab_markdown(tab)

    def on_note_path_button_clicked(self, widget):
        # Buttons (with links to parent notes) in the pathBox section of an opened notebookTab have the noteDbId saved as the button-widget name.
        # Get the noteDbId from the widget name
        noteDbId = int(widget.get_name())
        # Open tab for noteDbId
        # Check if noteDbId is already opened in a tab
        openedTab = self.findNotebookTabByDbId(noteDbId)
        if (openedTab):
            tabNum = openedTab.tabNum
        else:
            # Create a new tab
            newNotebookTab = notebookTab(self.store, noteDbId=noteDbId)
            newNotebookTab.tabNum = tabNum = self.notebook.append_page(newNotebookTab.pageWidget, newNotebookTab.titleHBox)
            self.notebook.set_tab_reorderable(newNotebookTab.pageWidget, True)
            self.connect_notebook_tab_signals(newNotebookTab)
            self.notebookTabs.append(newNotebookTab)

        self.notebook.set_current_page(tabNum)

    def updateTotalResultPagesNum(self):
        newTotalResultPagesNum = dbRepo.findLastResultsPageNum(self.resultsPerPage, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm)
        if newTotalResultPagesNum != self.totalResultPagesNum:
            self.totalResultPagesNum = newTotalResultPagesNum
            self.toolButtonsDict["totalPagesNum"].set_text(str(newTotalResultPagesNum))

    def on_button_press(self, widget, event):
        self.defer_select = treeviewDnDLogic.onButtonPress(widget, event, self.treeview, self.defer_select)
        return False

    def on_button_release(self, widget, event):
        self.defer_select = treeviewDnDLogic.onButtonRelease(widget, event, self.treeview, self.defer_select)
        if self.treeviewDoubleClicked:
            self.notebook.set_current_page(self.treeviewDoubleClicked)
            self.treeviewDoubleClicked = False
        return False

    def on_preferences_clicked(self, widget):
        prefDialog = dialogPreferences.DialogPreferences(self)
        prefDialog.webviewCSSsaveBtn.connect("clicked", self.on_webview_css_apply_btn_clicked, prefDialog)
        prefDialog.webviewCSSresetBtn.connect("clicked", self.on_webview_css_reset_btn_clicked, prefDialog)
        prefDialogResponse = prefDialog.run()
        if prefDialogResponse == Gtk.ResponseType.OK:
            saveFlag = True
        elif prefDialogResponse == Gtk.ResponseType.CANCEL:
            saveFlag = False
        else:
            saveFlag = False

        self.process_settings_changes(saveFlag)

        prefDialog.destroy()

    def process_settings_changes(self, saveFlag):
        # DOUBLE VALUE SETTINGS (managed with a single loop that triggers the corresponding event-listeners)
        # Case 1: refDialogResponse == Gtk.ResponseType.OK, so saveFlag = True
        # Check each definitive setting against the corresponding temporary setting value and set it to its new value if different.
        # The corresponding listener method should be automatically triggered.
        # Case 2: prefDialogResponse == Gtk.ResponseType.CANCEL, so saveFlag = False
        # Check each temporary setting against the corresponding definitive setting value and reset it to its original value if different.
        # The corresponding listener method should be automatically triggered.

        for optionName in self.doubleValueSettingsList:
            optionDefValue = self.settings.get_string(optionName)
            optionTmpValue = self.settings.get_string(optionName + '-tmp')
            if optionDefValue != optionTmpValue:
                if saveFlag:
                    if optionName == "db-path":
                        self.on_gsetting_dbpath_changed(optionDefValue, optionTmpValue)
                        self.settings.set_string(optionName, optionTmpValue)
                    elif optionName == "assets-folder-path":
                        self.on_gsetting_assetspath_changed_pre(optionDefValue, optionTmpValue)
                        self.settings.set_string(optionName, optionTmpValue)
                        self.on_gsetting_assetspath_changed_post()
                    else:
                        self.settings.set_string(optionName, optionTmpValue)
                else:
                    self.settings.set_string(optionName + '-tmp', optionDefValue)

        # SINGLE VALUE SETTINGS
        # 1- Setting: Webview custom CSS
        webviewCssModFlag = self.settings.get_boolean("webview-css-mod-flag")
        if webviewCssModFlag:
            # If user is SAVING any new setting (saveFlag = True)
            if saveFlag:
                # Apply new style to all opened tabs (if any)
                if len(self.notebookTabs) > 0:
                    for tab in self.notebookTabs:
                        # Re-render markdown of tab
                        self.clear_tab_webview_cache(tab)
                        self.render_notebooktab_markdown(tab)
                # Update corresponding GSetting
                self.settings.set_boolean("webview-css-mod-flag", False)

            # If user is CANCELING any new setting (saveFlag = False)
            else:
                # Update corresponding GSetting
                self.settings.set_boolean("webview-css-mod-flag", False)
                # Restore css-webview-user-custom-theme.css file content
                cssFileOr = open("css/css-webview-dark-theme-1.css", "r")
                cssStringOr = cssFileOr.read()
                cssFileOr.close()
                cssFileCustom = open("css/css-webview-user-custom-theme.css", "w")
                cssFileCustom.write(cssStringOr)
                cssFileCustom.close()
                # Note: There is no need to restore the webview-CSS textview content in the preferenceDialog since the dialog is destroyed after closing it
                # Re-render markdown of only self.currentTab (if it exists)
                if self.currentTab:
                    self.clear_tab_webview_cache(self.currentTab)
                    self.render_notebooktab_markdown(self.currentTab)


    def on_webview_css_apply_btn_clicked(self, widget, prefDialog):
        cssString = prefDialog.get_webview_custom_css()
        # Set GSetting "webview-css-mod-flag" to True to indicate that there are new changes
        self.settings.set_boolean("webview-css-mod-flag", True)
        # Save new cssString to the css-webview-user-custom-theme.css file
        with open("webview/css/css-webview-user-custom-theme.css", "w") as cssFile:
            cssFile.write(cssString)
            cssFile.close()
        # Re-render markdown of only self.currentTab (if it exists)
        if self.currentTab:
            self.clear_tab_webview_cache(self.currentTab)
            self.render_notebooktab_markdown(self.currentTab)

    def on_webview_css_reset_btn_clicked(self, widget, prefDialog):
        # Set GSetting "webview-css-mod-flag" to False to indicate that there are no changes to apply
        self.settings.set_boolean("webview-css-mod-flag", False)
        # Restore css-webview-user-custom-theme.css file content
        cssFileOr = open("webview/css/css-webview-dark-theme-1.css", "r")
        cssStringOr = cssFileOr.read()
        cssFileOr.close()
        cssFileCustom = open("webview/css/css-webview-user-custom-theme.css", "w")
        cssFileCustom.write(cssStringOr)
        cssFileCustom.close()
        # Restore the textview content in the preferenceDialog
        prefDialog.webviewCSSbuf.set_text(cssStringOr)
        # Re-render markdown of only self.currentTab (if it exists)
        if self.currentTab:
            self.clear_tab_webview_cache(self.currentTab)
            self.render_notebooktab_markdown(self.currentTab)

    def clear_tab_webview_cache(self, notebookTab):
        webview = notebookTab.webview
        webContext = webview.get_context()
        webContext.clear_cache()

    def on_toolbutton_new_clicked(self, widget):
        isSingleSelection = False
        isChildRow = False
        refNoteIter = None

        treeSelection = self.treeview.get_selection()
        model, pathlist = treeSelection.get_selected_rows()
        counter = treeSelection.count_selected_rows()

        if(counter == 1):
            isSingleSelection = True
            refNoteIter = model.get_iter(pathlist[0])
            refNoteDbId = model[refNoteIter][0]

            if(model.iter_parent(refNoteIter)):
                isChildRow = True
            else:
                isChildRow = False
        else:
            isSingleSelection = False

        # If displayToggledOnlyMode is active and multiple items are selected, then no option should be available for note creation.
        # In this case show a warning dialog
        if self.displayToggledOnlyModeOn and not isSingleSelection:
            dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, text="Can't create new items")
            dialog.format_secondary_text("In order to create new items while in Toggle Mode, select one (and only one) treeview item")
            dialog.run()
            dialog.destroy()
        else:
            newDialog = dialogNewNote.DialogNewNote(self, isSingleSelection, isChildRow, self.orderByColumn, self.displayToggledOnlyModeOn)
            newDialogResponse = newDialog.run()

            if newDialogResponse == Gtk.ResponseType.OK:
                selectedOption = newDialog.get_selected_option()
                if(selectedOption == 0 or selectedOption == 1):
                    refNoteDbId = None
                newDialog.destroy()

                # Insert Edit-note-details dialog
                editDialog = dialogEditNote.DialogEditNote(self)
                editDialogResponse = editDialog.run()

                if editDialogResponse == Gtk.ResponseType.OK:
                    noteTitle = editDialog.get_note_title()
                    noteDescription = editDialog.get_note_description()

                    # Create the new note
                    newNotebookTab = notebookTab(self.store, refNoteDbId=refNoteDbId, position=selectedOption, titleString=noteTitle, descriptionString=noteDescription)
                    newNotebookTab.tabNum = self.notebook.append_page(newNotebookTab.pageWidget, newNotebookTab.titleHBox)
                    self.notebook.set_tab_reorderable(newNotebookTab.pageWidget, True)
                    self.connect_notebook_tab_signals(newNotebookTab)
                    # Connect path buttons with callback
                    for button in newNotebookTab.pathButtonsList:
                        button.connect("clicked", self.on_note_path_button_clicked)
                    self.notebookTabs.append(newNotebookTab)
                    self.notebook.set_current_page(newNotebookTab.tabNum)

                elif editDialogResponse == Gtk.ResponseType.CANCEL:
                    pass

                editDialog.destroy()

            elif newDialogResponse == Gtk.ResponseType.CANCEL:
                pass

            newDialog.destroy()

    def on_toolbutton_save_clicked(self, widget=None):
        # Note: The treeRowRef returned by the saveNote function CAN be None in case of a new row inserted in a resultPage that is not currently displayed (so the new row won't be added to the current Treestore)
        if self.currentTab.pendingUpdatesFlag:
            noteDbId = dbRepo.saveNote(self.store, self.currentTab, self.resultsPerPage, self.resultsPageNum)
            if noteDbId:
                self.currentTab.pendingUpdatesFlag = False
                self.currentTab.tabLabel.set_text(self.currentTab.titleString)
                # If creating a new Note
                if not self.currentTab.noteDbId:
                    isNewlyCreatedNote = True
                    # Update the data displayed in the treeview
                    self.updateTreeviewAfterSave(noteDbId, isNewlyCreatedNote)
                    # Update the currentTab parameters
                    self.currentTab.needsSaving = False
                    self.currentTab.noteDbId = noteDbId
                    self.currentTab.refNoteDbId = None # IMPORTANT: this line MUST always come after self.updateTreeviewAfterSave() and never before
                    # Update the noteDbId displayed in the revealer box
                    self.currentTab.revealerNoteIdLabel.set_markup("<b>Id:</b> " + str(noteDbId))
                    recursiveDbIdPath = dbRepo.findRecursivePathByDbId(noteDbId)
                    self.currentTab.recursiveDbIdPathList = [subdict["id"] for subdict in recursiveDbIdPath]
                    # Update the recursiveDbIdPathBox in the revealer section
                    self.currentTab.createRecursiveDbIdPathBox(recursiveDbIdPath)
                    # Connect path buttons with callback
                    for button in self.currentTab.pathButtonsList:
                        button.connect("clicked", self.on_note_path_button_clicked)

                    if self.currentTab.position in [0,1,4,5]:
                        # Delete row(s) if resultsPerPage has been exceded
                        if (len(self.store) > self.resultsPerPage):
                            for x in range(len(self.store) - 1, self.resultsPerPage - 1, -1):
                                rowPath = Gtk.TreePath([x])
                                rowIter = self.store.get_iter(rowPath)
                                self.store.remove(rowIter)

                # If updating an existing Note
                else:
                    isNewlyCreatedNote = False
                    # Update the data displayed in the treeview
                    self.updateTreeviewAfterSave(noteDbId, isNewlyCreatedNote)

    def updateTreeviewAfterSave(self, noteDbId, isNewlyCreatedNote):
        note = dbRepo.findNoteByDbId(noteDbId)

        if isNewlyCreatedNote:
            position = self.currentTab.position
            # New approach: since the treeview is automatically sorted, I can just append the new item without worrying about placing it in the right spot

            if position == 0 or position == 1:
                # Working on root level. IMPORTANT: Options 1 and 2 for root level items are available ONLY in normalDisplayMode; so if displaySearchTermMode or displayToggledMode are active, by definition no treeview update will be necessary
                if not self.displaySearchTermModeOn and not self.displayToggledOnlyModeOn:
                    previousRecordsCount = dbRepo.findPreviousRecordsCountByDbId(self.orderByColumn, self.orderAsc, noteDbId, self.displayToggledOnlyModeOn, self.toggledRowsDict)
                    itemPageNum = math.ceil((previousRecordsCount+1)/self.resultsPerPage)
                    if self.resultsPageNum == itemPageNum:
                        newRowIter = self.store.append(None, (note.id, False, note.title, note.description, note.custom_order, note.fraction_num, note.fraction_denom, str(note.created), str(note.last_updated)))
                        newRowPath = self.store.get_path(newRowIter)
                        self.currentTab.treeRowRef = Gtk.TreeRowReference.new(self.store, newRowPath)

            elif position == 2 or position == 3:
                refNoteParentDbId = dbRepo.findParentDbId(self.currentTab.refNoteDbId)
                self.store.foreach(self.searchTreeviewAndAppendNewNote, refNoteParentDbId, note)

            elif position == 4 or position == 5:
                refNoteParentDbId = dbRepo.findParentDbId(self.currentTab.refNoteDbId)
                if refNoteParentDbId:
                    # Working on a child level
                    self.store.foreach(self.searchTreeviewAndAppendNewNote, refNoteParentDbId, note)
                else:
                    # Working on root level. IMPORTANT: Options 4 and 5 for root level items are available ONLY in normalDisplayMode; so if displaySearchTermMode or displayToggledMode are active, by definition no treeview update will be necessary
                    if not self.displaySearchTermModeOn and not self.displayToggledOnlyModeOn:
                        previousRecordsCount = dbRepo.findPreviousRecordsCountByDbId(self.orderByColumn, self.orderAsc, noteDbId, self.displayToggledOnlyModeOn, self.toggledRowsDict)
                        itemPageNum = math.ceil((previousRecordsCount + 1) / self.resultsPerPage)
                        if self.resultsPageNum == itemPageNum:
                            newRowIter = self.store.append(None, (note.id, False, note.title, note.description, note.custom_order, note.fraction_num, note.fraction_denom, str(note.created), str(note.last_updated)))
                            newRowPath = self.store.get_path(newRowIter)
                            self.currentTab.treeRowRef = Gtk.TreeRowReference.new(self.store, newRowPath)

            elif position == 6:
                self.store.foreach(self.searchTreeviewAndAppendNewNote, self.currentTab.refNoteDbId, note)

        else:
            if self.currentTab.treeRowRef and self.currentTab.treeRowRef.valid():
                rowPath = self.currentTab.treeRowRef.get_path()
                rowIter = self.store.get_iter(rowPath)
                self.store.set_value(rowIter, 2, note.title)
                self.store.set_value(rowIter, 3, note.description)
                self.store.set_value(rowIter, 8, str(note.last_updated))

    def searchTreeviewAndAppendNewNote(self, store, path, iter, refNoteDbId, note):
        # If func returns True, then the tree ceases to be walked, and Gtk.TreeModel.foreach() returns.
        currentItemDbId = store[iter][0]
        if currentItemDbId == refNoteDbId:
            # Append new item
            newRowIter = store.append(iter, (note.id, False, note.title, note.description, note.custom_order, note.fraction_num, note.fraction_denom, str(note.created), str(note.last_updated)))
            newRowPath = store.get_path(newRowIter)
            self.currentTab.treeRowRef = Gtk.TreeRowReference.new(store, newRowPath)

            # If displaySearchTermMode is active, then there may be multiple treenodes to update (= duplicate results) so keep iterating; otherwise return True to stop the foreach loop
            if self.displaySearchTermModeOn and not self.displayToggledOnlyModeOn:
                return False
            else:
                return True

        else:
            return False

    def on_gotopage_entry_activated(self, entry):
        newPageNum = int(entry.get_text())

        if(newPageNum != self.resultsPageNum):
            if(newPageNum <= 1):
                newPageNum = 1
                updateEntryValue = True
            elif(newPageNum >= self.totalResultPagesNum):
                newPageNum = self.totalResultPagesNum
                updateEntryValue = True
            else:
                updateEntryValue = False

            self.resultsPageNum = newPageNum

            if(updateEntryValue):
                self.toolButtonsDict["goToPage"].set_text(str(self.resultsPageNum))

            self.update_go_previous_next_buttons_state()

            self.update_treeview_results()

            # Focus Out - Not working
            # event = Gdk.EventFocus()
            # event.window = entry.get_window()
            # event.send_event = True
            # event.type = Gdk.EventType.FOCUS_CHANGE
            # event.in_ = False
            #
            # entry.do_focus_out_event(self, event)

    def update_go_previous_next_buttons_state(self):
        if (self.resultsPageNum == 1):
            self.toolButtonsDict["goPrevious"].set_sensitive(False)
        else:
            self.toolButtonsDict["goPrevious"].set_sensitive(True)

        if (self.resultsPageNum == self.totalResultPagesNum):
            self.toolButtonsDict["goNext"].set_sensitive(False)
        else:
            self.toolButtonsDict["goNext"].set_sensitive(True)

        if(self.resultsPageNum > 1 and self.resultsPageNum < self.totalResultPagesNum):
            self.toolButtonsDict["goPrevious"].set_sensitive(True)
            self.toolButtonsDict["goNext"].set_sensitive(True)

    def on_toolbutton_go_previous_clicked(self, widget):
        if(self.resultsPageNum > 1):
            self.resultsPageNum = self.resultsPageNum - 1
            self.toolButtonsDict["goToPage"].set_text(str(self.resultsPageNum))

            self.update_go_previous_next_buttons_state()

            self.update_treeview_results()

    def on_toolbutton_go_next_clicked(self, widget):
        if (self.resultsPageNum < self.totalResultPagesNum):
            self.resultsPageNum = self.resultsPageNum + 1
            self.toolButtonsDict["goToPage"].set_text(str(self.resultsPageNum))

            self.update_go_previous_next_buttons_state()

            self.update_treeview_results()

    def on_search_entry_activated(self, searchEntry):
        searchTerm = searchEntry.get_text()
        # Theoretically, if the search entry gets activated it means that self.displayToggledOnlyMode = False (otherwise the search entry would be rendered insensitive and this function couldn't be triggered)

        # If searchTerm is null, do not activate the searchTermMode
        # But if searchTermMode is already activated and searchTerm is null, then exit the searchTermMode
        if len(searchTerm) > 0:
            self.searchTerm = searchTerm
            if not self.displaySearchTermModeOn:
                # Activating displaySearchTermMode for the first time
                self.displaySearchTermModeOn = True
                # Disable the "new" and "delete" menus / toolbuttons
                self.menuItemsDict["File"]["New..."].set_sensitive(False)
                self.menuItemsDict["Edit"]["Delete"].set_sensitive(False)
                self.toolButtonsDict["new"].set_sensitive(False)
                self.toolButtonsDict["delete"].set_sensitive(False)

            self.update_pagenum_toolbuttons()
            self.update_treeview_results()
            if self.treeviewDndEnabled:
                treeviewDnDLogic.disableDnd(self.treeview)
                self.treeviewDndEnabled = False

        elif len(searchTerm) == 0 and self.displaySearchTermModeOn:
            # Exiting searchTermMode
            self.searchTerm = searchTerm
            self.displaySearchTermModeOn = False
            self.update_pagenum_toolbuttons()
            self.update_treeview_results()
            if not self.treeviewDndEnabled:
                treeviewDnDLogic.enableDnd(self.treeview)
                self.treeviewDndEnabled = True

            # Reactivate the "new" and "delete" menus / toolbuttons
            self.menuItemsDict["File"]["New..."].set_sensitive(True)
            self.menuItemsDict["Edit"]["Delete"].set_sensitive(True)
            self.toolButtonsDict["new"].set_sensitive(True)
            self.toolButtonsDict["delete"].set_sensitive(True)

        else:
            # Trying to activate searchTermMode with a null searchTerm. Do nothing and display a warning.
            # This case is equal to: len(searchTerm) == 0 and not self.displaySearchTermModeOn
            dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, text="No Search Term")
            dialog.format_secondary_text("Type a search term in the entry before performing a search")
            dialog.run()
            dialog.destroy()

    def on_toggled_only_mode_toggled(self, widget):
        if widget.get_active():
            # Check if there is at least one toggled item, otherwise disable the displayToggledOnlyMode and (eventually) show a dialog
            if len(self.toggledRowsDict) > 0:
                # Turn displayToggledOnlyMode on
                self.displayToggledOnlyModeOn = True
                searchWidget = self.toolButtonsDict["search"]
                searchToolItem = searchWidget.get_parent().get_parent()
                searchToolItem.set_sensitive(False)
                self.update_pagenum_toolbuttons()
                self.update_treeview_results()
                if not self.treeviewDndEnabled:
                    treeviewDnDLogic.enableDnd(self.treeview)
                    self.treeviewDndEnabled = True

                # If switching from displaySearchTermMode to displayToggledOnlyMode, reactivate the "new" and "delete" menus / toolbuttons
                if self.displaySearchTermModeOn:
                    self.menuItemsDict["File"]["New..."].set_sensitive(True)
                    self.menuItemsDict["Edit"]["Delete"].set_sensitive(True)
                    self.toolButtonsDict["new"].set_sensitive(True)
                    self.toolButtonsDict["delete"].set_sensitive(True)

            else:
                # No items toggled
                widget.set_active(False)
                dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, text="No Toggled Items")
                dialog.format_secondary_text("Toggle at least one item before applying this filter")
                dialog.run()
                dialog.destroy()
        else:
            # Turn displayToggledOnlyMode off
            self.displayToggledOnlyModeOn = False
            searchWidget = self.toolButtonsDict["search"]
            searchToolItem = searchWidget.get_parent().get_parent()
            searchToolItem.set_sensitive(True)
            self.update_pagenum_toolbuttons()
            self.update_treeview_results()
            if self.displaySearchTermModeOn and self.treeviewDndEnabled:
                treeviewDnDLogic.disableDnd(self.treeview)
                self.treeviewDndEnabled = False

            # If switching from displayToggledOnlyMode to displaySearchTermMode, disable the "new" and "delete" menus / toolbuttons.
            if self.displaySearchTermModeOn:
                self.menuItemsDict["File"]["New..."].set_sensitive(False)
                self.menuItemsDict["Edit"]["Delete"].set_sensitive(False)
                self.toolButtonsDict["new"].set_sensitive(False)
                self.toolButtonsDict["delete"].set_sensitive(False)

    def on_toolbutton_select_all_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.Gtk.Entry'>":
                    focusedWidget.select_region(0, -1)
                elif str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    editor_buffer = focusedWidget.get_buffer()
                    editor_buffer.select_range(editor_buffer.get_start_iter(), editor_buffer.get_end_iter())
                else:
                    pass

    def on_toolbutton_cut_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.Gtk.Entry'>":
                    focusedWidget.cut_clipboard()
                elif str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    editor_buffer = focusedWidget.get_buffer()
                    editor_buffer.cut_clipboard(self.clipboard, editor_buffer)
                else:
                    pass

    def on_toolbutton_copy_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.Gtk.Entry'>":
                    focusedWidget.copy_clipboard()
                elif str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    editor_buffer = focusedWidget.get_buffer()
                    editor_buffer.copy_clipboard(self.clipboard)
                else:
                    pass
        # if self.toolButtonsDict["paste"].is_visible():
        #     self.toolButtonsDict["paste"].set_visible(False)
        # else:
        #     self.toolButtonsDict["paste"].set_visible(True)

    def on_toolbutton_paste_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.Gtk.Entry'>":
                    focusedWidget.paste_clipboard()
                elif str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    editor_buffer = focusedWidget.get_buffer()
                    editor_buffer.paste_clipboard(self.clipboard, None, editor_buffer)
                else:
                    pass

    def on_toolbutton_render_markdown_clicked(self, widget):
        notebookTab = self.currentTab
        self.render_notebooktab_markdown(notebookTab)

    def render_notebooktab_markdown(self, notebookTab):
        assetsFolderPath = self.settings.get_string("assets-folder-path")
        dir_path = "file:" + os.path.realpath(assetsFolderPath) + "/"
        sourceViewBuffer = notebookTab.sourceview.get_buffer()
        sourceViewText = sourceViewBuffer.get_text(sourceViewBuffer.get_start_iter(), sourceViewBuffer.get_end_iter(), False)
        renderedMarkdown = renderMarkdown.render(sourceViewText)
        notebookTab.webview.load_html(renderedMarkdown, dir_path)

    def on_toolbutton_undo_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    self.currentTab.sourceview.do_undo(self.currentTab.sourceview)

    def on_toolbutton_redo_clicked(self, widget):
        focusedWidget = self.get_focus()
        if focusedWidget is not None:
            if focusedWidget.has_focus():
                if str(type(focusedWidget)) == "<class 'gi.repository.GtkSource.View'>":
                    self.currentTab.sourceview.do_redo(self.currentTab.sourceview)

    def on_views_combo_changed(self, combo):
        hPaned = self.currentTab.hPaned
        sourceView = hPaned.get_child1()
        preview = hPaned.get_child2()

        activeIndex = combo.get_active()
        if activeIndex == 0: # Code and Preview
            if not sourceView.is_visible():
                sourceView.show()
            if not preview.is_visible():
                preview.show()
        elif activeIndex == 1: # Code only
            if preview.is_visible():
                preview.hide()
            if not sourceView.is_visible():
                sourceView.show()
        elif activeIndex == 2: # Preview only
            if sourceView.is_visible():
                sourceView.hide()
            if not preview.is_visible():
                preview.show()
        else:
            pass

    # def on_button_show_code_only_clicked(self, widget):
    #     self.hpaned.get_child1().hide()
    #
    # def on_button_show_preview_only_clicked(self, widget):
    #     self.hpaned.get_child1().show()
    #
    # def on_button_show_code_and_preview_clicked(self, widget):
    #     self.hpaned.get_child1().show()

    # Changing the number of resultsPerPage
    def on_rows_combo_changed(self, combo):
        self.resultsPerPage = int(combo.get_active_text())
        self.update_pagenum_toolbuttons()
        self.update_treeview_results()

    def update_pagenum_toolbuttons(self):
        self.totalResultPagesNum = dbRepo.findLastResultsPageNum(self.resultsPerPage, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm)
        self.toolButtonsDict["totalPagesNum"].set_text(str(self.totalResultPagesNum))
        if (int(self.toolButtonsDict["goToPage"].get_text()) > self.totalResultPagesNum):
            self.resultsPageNum = self.totalResultPagesNum
            self.toolButtonsDict["goToPage"].set_text(str(self.resultsPageNum))
        self.update_go_previous_next_buttons_state()

    def update_treeview_results(self):
        self.store.clear()
        self.store = dbRepo.populateTreestore(self.store, dbRepo.findAllResults(self.orderByColumn, self.orderAsc, self.resultsPerPage, self.calculate_results_offset(), self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm), self.toggledRowsDict)
        self.recreate_treerowrefs()

    # Changing the orderByColumn
    def on_order_combo_changed(self, combo):
        activeIndex = combo.get_active()
        self.orderByColumn = activeIndex

        self.update_treeview_results()

        # Note: the following code only reorders current items (= items displayed in  the current resultsPage). It is useful if new items are added.
        customSortColumnId = self.find_custom_sort_column_id(self.orderByColumn)
        self.store.set_sort_column_id(customSortColumnId, not self.orderAsc)

    # Changing the ASC / DESC order
    def on_dir_combo_changed(self, combo):
        activeIndex = combo.get_active()
        self.orderAsc = not activeIndex
        self.update_treeview_results()

        # Note: the following code only reorders current items (= items displayed in  the current resultsPage). It is useful if new items are added.
        customSortColumnId = self.find_custom_sort_column_id(self.orderByColumn)
        self.store.set_sort_column_id(customSortColumnId, not self.orderAsc)

    def recreate_treerowrefs(self): # If the treeview order params (column and / or direction) change, then all treeRowRefs of the opened notes are no longer valid and they should be manually recreated
        openedNotesDbIds = []
        for tab in self.notebookTabs:
            if tab.noteDbId:
                openedNotesDbIds.append(int(tab.noteDbId))

        if len(openedNotesDbIds) > 0:
            self.store.foreach(self.custom_foreach_function, openedNotesDbIds)

    def custom_foreach_function(self, model, path, iter, dbIdList):
        storeItemDbId = int(self.store[iter][0])

        # This code is redundant if the toggled status is already set in the dbRepo.populateTreestore() method
        # if len(self.toggledRowsDict) > 0:
        #     if storeItemDbId in self.toggledRowsDict:
        #         self.store[iter][1] = True

        if len(dbIdList) > 0:
            if storeItemDbId in dbIdList:
                treeRowRef = Gtk.TreeRowReference.new(self.store, path)
                tab = self.findNotebookTabByDbId(storeItemDbId)
                if tab:
                    notebookTabsIndex = self.notebookTabs.index(tab)
                    self.notebookTabs[notebookTabsIndex].treeRowRef = treeRowRef

                dbIdList.remove(storeItemDbId)
                if len(dbIdList) == 0:
                    return True # Returning True stops the foreach function


    # EXAMPLE - Working recursive function
    #
    # if (itemDbId in openedNotesDbIds) or self.childItemIsOpened(pathIterUpd, openedNotesDbIds):
    #   ....
    #
    # def childItemIsOpened(self, parentIter, openedNotesDbIds):
    #     if self.store.iter_has_child(parentIter):
    #         childIter = self.store.iter_children(parentIter)
    #         while childIter:
    #             if (self.store[childIter][0] in openedNotesDbIds) or self.childItemIsOpened(childIter, openedNotesDbIds):
    #                 return True
    #
    #             childIter = self.store.iter_next(childIter)
    #
    #         return False
    #
    #     else:
    #         return False

    def on_toolbutton_delete_clicked(self, widget):
        debug = False
        if debug:
            print("You pressed the Ctrl+Canc shortcut")

        rootItemsNetBalance = 0

        #check if at least one treeview item is selected, then delete it
        treeselection = self.treeview.get_selection()
        model, pathlist = treeselection.get_selected_rows()
        if pathlist:

            source_path_ref_list = []
            for path in pathlist:
                new_row_reference = Gtk.TreeRowReference.new(model, path)
                source_path_ref_list.append(new_row_reference)

            openedNotesDbIdsSet = set()
            for tab in self.notebookTabs:
                if tab.noteDbId:
                    openedNotesDbIdsSet.add(int(tab.noteDbId))

            applyToAllFlag = False
            applyToAllResponse = Gtk.ResponseType.CANCEL

            for path_ref in source_path_ref_list:
                if path_ref.valid():
                    pathUpd = path_ref.get_path()
                    pathIterUpd = model.get_iter(pathUpd)
                    itemDbId = model[pathIterUpd][0]
                    # Check if item (OR one of its children) is already opened in a tab
                    if len(openedNotesDbIdsSet) > 0:
                        allChildrenDbIdsSet = dbRepo.findAllChildrenDbIds(itemDbId)
                        criticalTabsSet = allChildrenDbIdsSet.intersection(openedNotesDbIdsSet) # This list will contain all the tabs that need to be closed to safely delete the note record
                        if len(criticalTabsSet) > 0:
                            if not applyToAllFlag:
                                #  Display dialog: Close and delete / Skip deletion / Cancel - Apply to all
                                noteTitle = self.store[pathIterUpd][2]
                                dialog = dialogDeleteOpenedNote.DialogDeleteOpenedNote(self, noteTitle = noteTitle)
                                response = dialog.run()

                                if response == Gtk.ResponseType.YES or response == Gtk.ResponseType.NO:
                                    if dialog.get_apply_to_all():
                                        applyToAllFlag = True
                                        applyToAllResponse = response

                                dialog.destroy()

                            else:
                                response = applyToAllResponse

                            if response == Gtk.ResponseType.YES:
                                # close the problematic tab(s)
                                for criticalId in criticalTabsSet:
                                    criticalTab = self.findNotebookTabByDbId(criticalId)
                                    self.remove_notebookTab_from_memory(criticalTab)
                                pass
                            elif response == Gtk.ResponseType.NO:
                                # skip to the next iteration of the for loop
                                continue
                            else:
                                # response == Gtk.ResponseType.CANCEL
                                return



                    # Debug: To avoid deleting the elements just skip to the next iteration of the for loop
                    # continue

                    dbItem = dbRepo.Note.get_by_id(itemDbId)
                    deletedRowsNum = dbItem.delete_instance() #recursive=True should not be necessary since cascade is set to True in the model
                    if debug:
                        print("Number of database rows deleted: " + str(deletedRowsNum))

                    model.remove(pathIterUpd)
                    if len(str(pathUpd)) == 1:
                        rootItemsNetBalance -= 1
                        if debug:
                            print("rootItemsNetBalance - 1")

            if (len(model) < self.resultsPerPage):
                diffNum = self.resultsPerPage - len(model)
                lastRootItemNum = len(model) - 1
                lastRootItemPath = Gtk.TreePath([lastRootItemNum])
                lastRootItemIter = model.get_iter(lastRootItemPath)
                lastRootItemDbId = model[lastRootItemIter][0]
                dbRepo.populateTreestore(model, dbRepo.findNextResults(self.orderByColumn, self.orderAsc, lastRootItemDbId, diffNum, self.displayToggledOnlyModeOn, self.displaySearchTermModeOn, self.toggledRowsDict, self.searchTerm), self.toggledRowsDict)

            if debug:
                print("Total rootItemsNetBalance: " + str(rootItemsNetBalance))

            if rootItemsNetBalance != 0:
                self.updateTotalResultPagesNum()

            return True # The function will return True if at least one item is deleted

        else:
            if debug:
                print("No treeview items selected - Delete command aborted")
            return False # The function will return False if no item is deleted

    def treeview_on_cell_toggled(self, cellRendererToggle, path): # path is automatically passed as string
        # Add or remove item from the self.toggledRowsDict dictionary
        dbId = int(self.store[path][0])
        toggledValue = self.store[path][1]
        # Item is not toggled - Check if the item can be toggled
        if not toggledValue:
            # Check 1 - Check if the current item is the parent of an already-toggled item
            toggledItemsParentsList = [item for sublist in self.toggledRowsDict.values() for item in sublist]
            if dbId not in toggledItemsParentsList:
                # Check 2 - Check if one of the parent items of the current item is already toggled
                recursiveDbIdPath = dbRepo.findRecursivePathByDbId(dbId)
                recursivePathDbIdList = [subdict["id"] for subdict in recursiveDbIdPath]
                if not set(recursivePathDbIdList) & set(self.toggledRowsDict.keys()):
                    # If both checks are passed, toggle the item and add it to the toggledRowsDict
                    # Change the checkbox status by updating the model
                    self.store[path][1] = not self.store[path][1]
                    # rootParentDbId = int(recursiveDbIdPath[0]["id"])
                    self.toggledRowsDict[dbId] = recursivePathDbIdList

        # Item is already toggled - Remove toggled status and remove corresponding entry from the toggledRowsDict
        else:
            # Change the checkbox status by updating the model
            self.store[path][1] = not self.store[path][1]
            if dbId in self.toggledRowsDict:
                self.toggledRowsDict.pop(dbId)

    def treeview_on_key_press_event(self, widget, event):
        debug = False
        if debug:
            print("Key press event triggered")
        if Gdk.keyval_name(event.keyval) == 'Return':
            if debug:
                print("Enter key was pressed")
            cursor = self.treeview.get_cursor()
            if cursor:
                cursorPath = cursor[0]
                cursorColumn = cursor[1]
                self.treeview_on_row_activated(self.treeview, cursorPath, cursorColumn, True)
                self.treeview.set_cursor(cursorPath, None, False)
                # cursorPath.free() # This causes segmentation error - Should be investigated
            return True
        else:
            if debug:
                print("Generic key was pressed (not Enter key)")
            return False

        
    def treeview_on_row_activated(self, treeview, row_path, treeviewcolumn, enterKeyFlag = False):
        debug = False
        if debug:
            print("Treeview row activated")

        model = treeview.get_model()
        n_columns = model.get_n_columns()

        # check if at least one treeview item is selected
        treeselection = treeview.get_selection()
        model, pathlist = treeselection.get_selected_rows()
        if pathlist:
            if debug:
                print("Number of selected note(s) to open: " + str(len(pathlist)))
            # Note: there should be no need to use rowReferences since this is a read-only operation (paths shouldn't change mid-function)
            for path in pathlist:
                pathIter = model.get_iter(path)
                noteDbId = model[pathIter][0]
                treeRowRef = Gtk.TreeRowReference.new(model, path)
                # check if note is already opened
                openedTab = self.findNotebookTabByDbId(noteDbId)
                if (openedTab):
                    tabNum = openedTab.tabNum
                    self.treeviewDoubleClicked = tabNum
                else:
                    newNotebookTab = notebookTab(self.store, noteDbId=noteDbId, treeRowRef=treeRowRef)
                    newNotebookTab.tabNum = self.notebook.append_page(newNotebookTab.pageWidget, newNotebookTab.titleHBox)
                    self.notebook.set_tab_reorderable(newNotebookTab.pageWidget, True)
                    self.connect_notebook_tab_signals(newNotebookTab)
                    # Connect path buttons with callback
                    for button in newNotebookTab.pathButtonsList:
                        button.connect("clicked", self.on_note_path_button_clicked)
                    self.notebookTabs.append(newNotebookTab)
                    self.treeviewDoubleClicked = newNotebookTab.tabNum

            if enterKeyFlag:
                self.notebook.set_current_page(self.treeviewDoubleClicked)
                self.treeviewDoubleClicked = False

        else:
            if debug:
                print("Error: Treeview-row-activated signal emitted but no selected row(s) were found. This should never happen!!")

    def on_notebook_switch_page(self, notebook, page, pageNum):
        if page.get_name() == "noteDetailsTab":
            tab = self.findNotebookTabByTabNum(pageNum)
            if(tab):
                notebookTabsIndex = self.notebookTabs.index(tab)
                self.currentTab = self.notebookTabs[notebookTabsIndex]
            else:
                debug = False
                if debug:
                    print("Error: Tab was not found in the self.notebookTabs list. This should never happen!!")
                pass
            focusOnMainTab = False
            self.updateToolBtnVisibility(focusOnMainTab)
            self.on_views_combo_changed(self.toolButtonsDict["view"])

        else:
            # The main tab was clicked
            focusOnMainTab = True
            self.updateToolBtnVisibility(focusOnMainTab)
            # Reset self.currentTab to None
            self.currentTab = None
            # Note: self.treeview.grab_focus()  # Seems to not be necessary

    def updateToolBtnVisibility(self, focusOnMainTab):
        if focusOnMainTab:
            # Switching from NoteDetailsTab to MainTab
            for btn in self.toolBtnGroupEditor:
                if (btn == self.toolButtonsDict["view"]):
                    btn = btn.get_parent().get_parent()
                btn.set_visible(False)

            for btn in self.toolBtnGroupMain:
                if btn == self.toolButtonsDict["search"]:
                    if not self.displayToggledOnlyModeOn:
                        # Reactivate also the search entry
                        searchToolItem = btn.get_parent().get_parent()
                        searchToolItem.set_visible(True)
                    else:
                        # Do not reactivate the search entry
                        pass

                # If displaySearchTermMode is activated, the "new" and "delete" toolbuttons should remain disabled. If normal display or displayToggledOnlyMode are activated, then enable them.
                elif btn == self.toolButtonsDict["new"] or btn == self.toolButtonsDict["delete"]:
                    if (not self.displaySearchTermModeOn) or (self.displaySearchTermModeOn and self.displayToggledOnlyModeOn):
                        btn.set_sensitive(True)

                else:
                    if (btn == self.toolButtonsDict["goToPage"] or btn == self.toolButtonsDict["pageResults"] or btn == self.toolButtonsDict["orderBy"] or btn == self.toolButtonsDict["orderDir"]):
                        btn = btn.get_parent().get_parent()
                    elif btn == self.toolButtonsDict["toggledOnlyMode"]:
                        btn = btn.get_parent()

                    btn.set_visible(True)

            # Update Menubar
            # print("Updating menu for Focus Main")

            for menu in self.menuItemsEditor:
                menu.set_sensitive(False)
            for menu in self.menuItemsMain:
                # If displaySearchTermMode is activated, the "new" and "delete" menus should remain disabled.
                if menu == self.menuItemsDict["File"]["New..."] or menu == self.menuItemsDict["Edit"]["Delete"]:
                    if (not self.displaySearchTermModeOn) or (self.displaySearchTermModeOn and self.displayToggledOnlyModeOn):
                        menu.set_sensitive(True)
                else:
                    menu.set_sensitive(True)

            self.update_go_previous_next_buttons_state()

        else:
            # Switching from MainTab to NoteDetailsTab
            for btn in self.toolBtnGroupMain:
                if btn == self.toolButtonsDict["new"] or btn == self.toolButtonsDict["delete"]:
                    btn.set_sensitive(False)
                else:
                    if (btn == self.toolButtonsDict["search"] or btn == self.toolButtonsDict["goToPage"] or btn == self.toolButtonsDict["pageResults"] or btn == self.toolButtonsDict["orderBy"] or btn == self.toolButtonsDict["orderDir"]):
                        btn = btn.get_parent().get_parent()
                    elif btn == self.toolButtonsDict["toggledOnlyMode"]:
                        btn = btn.get_parent()

                    btn.set_visible(False)

            for btn in self.toolBtnGroupEditor:
                if (btn == self.toolButtonsDict["view"]):
                    btn = btn.get_parent().get_parent()
                btn.set_visible(True)

            # Update Menubar
            # print("Updating menu for Focus Editor")

            for menu in self.menuItemsMain:
                menu.set_sensitive(False)

            for menu in self.menuItemsEditor:
                menu.set_sensitive(True)

    def on_notebook_page_reordered(self, notebook, child, page_num):
        if(self.currentTab.tabNum != page_num):
            for tab in self.notebookTabs:
                if(tab.tabNum == self.currentTab.tabNum):
                    tab.tabNum = page_num
                else:
                    if(page_num < self.currentTab.tabNum and tab.tabNum >= page_num and tab.tabNum < self.currentTab.tabNum):
                        tab.tabNum = tab.tabNum+1
                    elif(page_num > self.currentTab.tabNum and tab.tabNum <= page_num and tab.tabNum > self.currentTab.tabNum):
                        tab.tabNum = tab.tabNum-1
                    else:
                        pass

    def findNotebookTabByDbId(self, noteDbId):
        for tab in self.notebookTabs:
            if tab.noteDbId == noteDbId:
                return tab

        return None

    def findNotebookTabByTabNum(self, tabNum):
        for tab in self.notebookTabs:
            if tab.tabNum == tabNum:
                return tab

        return None

    def on_closetab_button_clicked(self, sender, widget):
        #get the page number of the tab we wanted to close
        pagenum = self.notebook.page_num(widget)
        #if there are unsaved changes, prompt a dialog to choose what to do (save / discard / cancel)
        tab = self.findNotebookTabByTabNum(pagenum)
        if tab.pendingUpdatesFlag:
            # check if the tab that is being closed is the one currently displayed, otherwise swith to it
            if tab.tabNum != self.currentTab:
                self.notebook.set_current_page(tab.tabNum)
            dialog = dialogCloseTab.DialogCloseTab(self)
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                self.on_toolbutton_save_clicked()
            elif response == Gtk.ResponseType.NO:
                pass
            else:
                # response == Gtk.ResponseType.CANCEL
                dialog.destroy()
                return

            dialog.destroy()

        self.remove_notebookTab_from_memory(tab)
        

    def remove_notebookTab_from_memory(self, tab):
        pagenum = tab.tabNum
        # close notebook tab
        self.notebook.remove_page(pagenum)
        # remove the tab object from the self.notebookTabs list
        notebookTabsIndex = self.notebookTabs.index(tab)
        del self.notebookTabs[notebookTabsIndex]
        # update tabNum of all the following tabs
        for tab in self.notebookTabs:
            if tab.tabNum > pagenum:
                tab.tabNum = tab.tabNum - 1


    def check_unsaved_changes_before_quit(self, widget, event):
        applyToAllFlag = False
        applyToAllResponse = False
        for tab in self.notebookTabs:
            if tab.pendingUpdatesFlag:
                if not applyToAllFlag:
                    # switch to the tab (so that self.currentTab will be updated and the save function can work correctly)
                    self.notebook.set_current_page(tab.tabNum)
                    dialog = dialogCloseTab.DialogCloseTab(self, displayCheckBoxFlag=True)
                    response = dialog.run()
                    if response == Gtk.ResponseType.YES:
                        self.on_toolbutton_save_clicked()
                        self.remove_notebookTab_from_memory(tab)
                    elif response == Gtk.ResponseType.NO:
                        self.remove_notebookTab_from_memory(tab)
                        pass
                    else:
                        # in this case response == Gtk.ResponseType.CANCEL
                        dialog.destroy()
                        return True

                    if dialog.get_apply_to_all():
                        applyToAllFlag = True
                        applyToAllResponse = response

                    dialog.destroy()

                else:
                    if applyToAllResponse != False and applyToAllResponse == Gtk.ResponseType.YES:
                        # switch to the tab (so that self.currentTab will be updated and the save function can work correctly)
                        self.notebook.set_current_page(tab.tabNum)
                        self.on_toolbutton_save_clicked()

        else:
            return False


    def on_toolbutton_note_details_clicked(self, widget):
        revealer = self.currentTab.revealer
        if revealer.get_reveal_child():
            revealer.set_reveal_child(False)
        else:
            revealer.set_reveal_child(True)

    def on_toolbutton_find_clicked(self, widget):
        srRevealer = self.currentTab.srRevealer
        if srRevealer.get_reveal_child():
            # srRevealer is already open. Two cases: 1) the user is switching between Find and Replace -> Find 2) the user wants to close the srRevealer
            if self.currentTab.srReplaceLabel.is_visible():
                self.setSrReplaceBoxVisibility(self.currentTab, False)

            else:
                if self.currentTab.srSearchContext:
                    srSettings = self.currentTab.srSearchContext.get_settings()
                    debug = False
                    if debug:
                        print("SearchText set to None")
                    srSettings.set_search_text(None)
                srRevealer.set_reveal_child(False)
        else:
            # srRevealer is not yet opened. Open it and display the appropriate commands
            if self.currentTab.srReplaceLabel.is_visible():
                self.setSrReplaceBoxVisibility(self.currentTab, True)

            self.currentTab.srSearchEntry.grab_focus()

            srRevealer.set_reveal_child(True)

    def setSrReplaceBoxVisibility(self, currentTab, visibleFlag):
        if visibleFlag:
            currentTab.srReplaceLabel.show()
            currentTab.srReplaceEntry.show()
            currentTab.srReplaceNextBtn.show()
            currentTab.srReplaceAllBtn.show()

        else:
            currentTab.srReplaceLabel.hide()
            currentTab.srReplaceEntry.hide()
            currentTab.srReplaceNextBtn.hide()
            currentTab.srReplaceAllBtn.hide()

    def on_toolbutton_find_replace_clicked(self, widget):
        srRevealer = self.currentTab.srRevealer
        if srRevealer.get_reveal_child():
            # srRevealer is already open. Two cases: 1) the user is switching between Find -> Find and Replace 2) the user wants to close the srRevealer
            if not self.currentTab.srReplaceLabel.is_visible():
                self.setSrReplaceBoxVisibility(self.currentTab, True)
            else:
                if self.currentTab.srSearchContext:
                    srSettings = self.currentTab.srSearchContext.get_settings()
                    debug = False
                    if debug:
                        print("SearchText set to None")
                    srSettings.set_search_text(None)
                srRevealer.set_reveal_child(False)
        else:
            # srRevealer is not yet opened. Open it and display the appropriate commands
            if not self.currentTab.srReplaceLabel.is_visible():
                self.setSrReplaceBoxVisibility(self.currentTab, True)

            self.currentTab.srSearchEntry.grab_focus()

            srRevealer.set_reveal_child(True)

    def on_srRevealerCloseBtn_clicked(self, widget):
        srRevealer = self.currentTab.srRevealer
        if srRevealer.get_reveal_child():
            if self.currentTab.srSearchContext:
                srSettings = self.currentTab.srSearchContext.get_settings()
                debug = False
                if debug:
                    print("SearchText set to None")
                srSettings.set_search_text(None)
            srRevealer.set_reveal_child(False)

    def on_note_editbtn_clicked(self, widget):
        dialog = dialogEditNote.DialogEditNote(self, self.currentTab.titleString, self.currentTab.descriptionString)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            noteTitle = dialog.get_note_title()
            noteDescription = dialog.get_note_description()

            if noteTitle != self.currentTab.titleString or noteDescription != self.currentTab.descriptionString:
                # Update notebookTab object properties
                self.currentTab.titleString = noteTitle
                self.currentTab.descriptionString = noteDescription

                # Update the data displayed in the notebookTab
                self.currentTab.revealerTitleLabel.set_markup("<b>Title:</b> " + noteTitle)
                self.currentTab.revealerDescLabel.set_markup("<b>Description:</b> " + noteDescription)
                if self.currentTab.lastPathLabel:
                    self.currentTab.lastPathLabel.set_text(noteTitle)

                self.currentTab.pendingUpdatesFlag = True

                escapedTitleString = GLib.markup_escape_text(noteTitle)
                markupTitleString = "<b>" + escapedTitleString + " *</b>"
                self.currentTab.tabLabel.set_markup(markupTitleString)

                # Note: Updating the data displayed in the treeview wil only be done after performing a Save action

        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

    def on_toolbutton_insert_media_clicked(self, widget):
        dialog = dialogInsertMedia.DialogInsertMedia(self)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selectedMediaOption = dialog.getSelectedMediaOption()
            # mediaCheckboxValue (true/false) defines whether thumbnail+gallery should be automatically added
            mediaCheckboxValue = dialog.getMediaCheckboxValue()
            # TODO Modify this section to add the possibility of using a custom asset dir (selected inside the dialog)
            # customAssetsFolderPath = dialog.getCustomAssetFolderPath()
            assetsFolderPathSetting = self.settings.get_string("assets-folder-path")
            # customAssetsFolderPath is an absolute path
            customAssetsFolderPath = assetsFolderPathSetting
            if len(customAssetsFolderPath) > len(assetsFolderPathSetting)+1 and customAssetsFolderPath[0:len(assetsFolderPathSetting)] == assetsFolderPathSetting:
                # customAssetsFolderPath is a subdir of assetsFolderPathSetting (and is different from assetsFolderPathSetting + "/")
                absoluteAssetsFolderPath = customAssetsFolderPath
                relativeAssetsFolderPath = customAssetsFolderPath[len(assetsFolderPathSetting)+1:]
            else:
                absoluteAssetsFolderPath = assetsFolderPathSetting
                relativeAssetsFolderPath = ''

            if selectedMediaOption == 1:
                # Call method to save image (+ thumbnail). Output is tuple (imgFileName, tbImgFileName, imgFilePathAbs, tbImgFilePathAbs, imgFilePathRel, tbImgFilePathRel)
                genImgData = self.save_clipboard_img_to_file(mediaCheckboxValue, absoluteAssetsFolderPath, relativeAssetsFolderPath)
                if genImgData:
                    # Generate markdown string
                    imgFilePathRel = genImgData[4]
                    tbImgFilePathRel = genImgData[5]
                    if mediaCheckboxValue:
                        markdownString = "[![](" + tbImgFilePathRel + ")](" + imgFilePathRel + "){: .gallery}"
                    else:
                        markdownString = "![](" + imgFilePathRel + ")"
                    # Insert new markdown in sourceView
                    sourceviewBuffer = self.currentTab.sourceview.get_buffer()
                    sourceviewBuffer.insert_at_cursor(markdownString, len(markdownString))

            elif selectedMediaOption == 2:
                # Retrieve list of selected images (as absolute filePaths)
                mediaFilesName = dialog.getMediaFilesname()
                for imgPath in mediaFilesName:
                    # If the source img is not already located in a subdir of the assets folder, create a copy of the file in the desired subdir of the assets folder.
                    if imgPath[:len(assetsFolderPathSetting)] != assetsFolderPathSetting:
                        # Generate unique filenames and filepaths for img (and thumbnail, if needed).
                        # Method output is tuple (imgFileName, tbImgFileName, imgFilePathAbs, tbImgFilePathAbs, imgFilePathRel, tbImgFilePathRel).
                        genImgData = self.generate_unique_img_filenames_filepaths(absoluteAssetsFolderPath, relativeAssetsFolderPath)
                        imgFilePathAbs = genImgData[2]
                        # Copy file
                        shutil.copy(imgPath, imgFilePathAbs)
                        tbImgFilePathAbs = genImgData[3]
                        imgFilePathRel = genImgData[4]
                        tbImgFilePathRel = genImgData[5]
                    else:
                        # ImgPath is already in the assets folder: keep the original filename and create a thumbnail name.
                        imgFilePathAbs = imgPath
                        head, tail = os.path.split(imgFilePathAbs)
                        # Absolute path of the image file directory (without trailing /)
                        imgFileDirPathAbs = head
                        # fileName with extension
                        imgFileName = tail
                        # fileExtension includes the dot (e.g. ".png")
                        fileExtension = Path(imgFileName).suffix
                        tbImgFileName = imgFileName[:-len(fileExtension)] + "_tb" + fileExtension
                        tbImgFilePathAbs = imgFileDirPathAbs + "/" + tbImgFileName
                        # Obtain relative folder path (without trailing /)
                        if len(imgFileDirPathAbs) > len(assetsFolderPathSetting)+1:
                            relativeFolderPath = imgFileDirPathAbs[len(assetsFolderPathSetting)+1:]
                            imgFilePathRel = relativeFolderPath + "/" + imgFileName
                            tbImgFilePathRel = relativeFolderPath + "/" + tbImgFileName
                        else:
                            # relativeFolderPath = ''
                            imgFilePathRel = imgFileName
                            tbImgFilePathRel = tbImgFileName


                    # Generate thumbnail img file (if needed)
                    if mediaCheckboxValue:
                        self.save_img_thumbnail(imgFilePathAbs, tbImgFilePathAbs)

                    # Generate markdown syntax
                    # TODO Add new line after each entry
                    if mediaCheckboxValue:
                        markdownString = "[![](" + tbImgFilePathRel + ")](" + imgFilePathRel + "){: .gallery}"
                    else:
                        markdownString = "![](" + imgFilePathRel + ")"

                    # Insert new markdown in sourceView
                    sourceviewBuffer = self.currentTab.sourceview.get_buffer()
                    sourceviewBuffer.insert_at_cursor(markdownString, len(markdownString))

            else:
                pass

        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

    def save_clipboard_img_to_file(self, mediaCheckboxValue, absoluteAssetsFolderPath, relativeAssetsFolderPath):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        imgFile = clipboard.wait_for_image()
        if imgFile:
            # Generate unique filename. Output is tuple (imgFileName, tbImgFileName, imgFilePathAbs, tbImgFilePathAbs, imgFilePathRel, tbImgFilePathRel)
            genImgData = self.generate_unique_img_filenames_filepaths(absoluteAssetsFolderPath, relativeAssetsFolderPath)
            imgFilePathAbs = genImgData[2]
            # Save img to local file
            imgFile.savev(imgFilePathAbs, "png", [], [])
            if mediaCheckboxValue:
                # Create img thumbnail
                tbImgFilePathAbs = genImgData[3]
                self.save_img_thumbnail(imgFilePathAbs, tbImgFilePathAbs)

        else:
            genImgData = None

        return genImgData

    def generate_unique_img_filenames_filepaths(self, absoluteAssetsFolderPath, relativeAssetsFolderPath):
        # Generate unique filenames for image and thumbnail
        datetimePrefix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        randomFilename = str(uuid.uuid4())[:8]
        imgExtension = "png"
        imgFileName = datetimePrefix + "_" + randomFilename + "." + imgExtension
        tbImgFileName = datetimePrefix + "_" + randomFilename + "_tb" + "." + imgExtension
        # Generate absolute filepaths for image and thumbnail
        imgFilePathAbs = absoluteAssetsFolderPath + "/" + imgFileName
        tbImgFilePathAbs = absoluteAssetsFolderPath + "/" + tbImgFileName
        # Generate relative filepaths for image and thumbnail
        if relativeAssetsFolderPath != '':
            imgFilePathRel = relativeAssetsFolderPath + "/" + imgFileName
            tbImgFilePathRel = relativeAssetsFolderPath + "/" + tbImgFileName
        else:
            imgFilePathRel = imgFileName
            tbImgFilePathRel = tbImgFileName

        return (imgFileName, tbImgFileName, imgFilePathAbs, tbImgFilePathAbs, imgFilePathRel, tbImgFilePathRel)

    def save_img_thumbnail(self, imgFilePathAbs, tbImgFilePathAbs):
        img = Image.open(imgFilePathAbs)
        imgW = float(img.size[0])
        imgH = float(img.size[1])
        if imgW > imgH:
            # Proportionally resize to a width of 350 px (arbitrary value)
            newImgW = 350
        else:
            # Proportionally resize to a width of 250 px (arbitrary value)
            newImgW = 250

        wpercent = (newImgW / imgW)
        newImgH = int(imgH * float(wpercent))
        newImg = img.resize((newImgW, newImgH), Image.ANTIALIAS)
        newImg.save(tbImgFilePathAbs)

    def on_sourceview_buffer_changed(self, textBuffer):
        if not self.currentTab.pendingUpdatesFlag:
            self.currentTab.pendingUpdatesFlag = True
            escapedTitleString = GLib.markup_escape_text(self.currentTab.titleString)
            markupTitleString = "<b>" + escapedTitleString + " *</b>"
            self.currentTab.tabLabel.set_markup(markupTitleString)
        else:
            # There are already unsaved changes, so do nothing
            pass

    def on_srSearchEntry_activate(self, widget):
        self.currentTab.srFindNextBtn.clicked()

    def on_srFindNextPrevBtn_clicked(self, widget, direction):
        # Direction is an arbitrary parameter: 1 = search NEXT - 2 = search PREVIOUS
        debug = False

        searchText = self.currentTab.srSearchEntry.get_text()
        searchText = GtkSource.utils_escape_search_text(searchText)

        srSourceBuffer = self.currentTab.sourceview.get_buffer()

        if len(searchText) > 0:

            if not self.currentTab.srSearchContext:
                self.currentTab.srSearchContext = GtkSource.SearchContext.new(srSourceBuffer, None)
                if debug:
                    print("SearchContext created")
                self.currentTab.srSearchContext.connect('notify::occurrences-count', self.on_notify_occurences_count_property_set)

            srSearchSettings = self.currentTab.srSearchContext.get_settings()
            # Set SearchSetting options here
            srSearchSettings.set_wrap_around(True)
            if self.currentTab.srSearchParam == 0:
                srSearchSettings.set_regex_enabled(False)
                srSearchSettings.set_case_sensitive(False)
            elif self.currentTab.srSearchParam == 1:
                srSearchSettings.set_regex_enabled(False)
                srSearchSettings.set_case_sensitive(True)
            elif self.currentTab.srSearchParam == 2:
                srSearchSettings.set_regex_enabled(True)
                pass

            if not srSearchSettings.get_search_text() or len(srSearchSettings.get_search_text()) == 0 or searchText != srSearchSettings.get_search_text():
                if debug:
                    print("Setting srSearchSettings.searchText")
                srSearchSettings.set_search_text(searchText)

            bounds = srSourceBuffer.get_selection_bounds()
            if len(bounds) != 0:
                start, end = bounds
            else:
                srCursorMark = srSourceBuffer.get_insert()
                srCursorIter = srSourceBuffer.get_iter_at_mark(srCursorMark)
                cursorOffset = srCursorIter.get_offset()
                if cursorOffset == srSourceBuffer.get_char_count():
                    start = end = srSourceBuffer.get_start_iter()
                else:
                    start = end = srCursorIter

            if direction == 1:
                if debug:
                    print("Starting forward search async")
                # GtkSource.SearchContext.forward_async(Gtk.TextIter, Gio.Cancellable or None, Gio.AsyncReadyCallback, *user_data)
                self.currentTab.srSearchContext.forward_async(end, None, self.forwardSearchFinished)
            else:
                if debug:
                    print("Starting backward search async")
                # GtkSource.SearchContext.backward_async(Gtk.TextIter, Gio.Cancellable or None, Gio.AsyncReadyCallback, *user_data)
                self.currentTab.srSearchContext.backward_async(start, None, self.backwardSearchFinished)

    # Gio.AsyncReadyCallback(GObject.Object or None, Gio.AsyncResult, *user_data)
    def forwardSearchFinished(self, sourceObject, asyncResult):
        success, matchStart, matchEnd = self.currentTab.srSearchContext.forward_finish(asyncResult)
        if success:
            self.selectSearchOccurence(matchStart, matchEnd)

    # Gio.AsyncReadyCallback(GObject.Object or None, Gio.AsyncResult, *user_data)
    def backwardSearchFinished(self, sourceObject, asyncResult):
        success, matchStart, matchEnd = self.currentTab.srSearchContext.backward_finish(asyncResult)
        if success:
            self.selectSearchOccurence(matchStart, matchEnd)

    def selectSearchOccurence(self, matchStart, matchEnd):
        srSourceView = self.currentTab.sourceview
        srSourceBuffer = srSourceView.get_buffer()
        srSourceBuffer.select_range(matchStart, matchEnd)
        insert = srSourceBuffer.get_insert()
        srSourceView.scroll_mark_onscreen(insert)

        if self.currentTab.idleUpdateLabelId == 0:
            self.currentTab.idleUpdateLabelId = GLib.idle_add(self.updateLabelIdleCb)  # GLib.PRIORITY_DEFAULT_IDLE

    def updateLabelIdleCb(self):
        debug = False
        if debug:
            print("Idle process called")
        self.currentTab.idleUpdateLabelId = 0
        self.updateLabelOccurrences()
        return GLib.SOURCE_REMOVE

    def updateLabelOccurrences (self):
        srSourceBuffer = self.currentTab.sourceview.get_buffer()
        srSearchContext = self.currentTab.srSearchContext
        srSearchSettings = srSearchContext.get_settings()

        if srSearchSettings.get_search_text():
            occurrencesCount = srSearchContext.get_occurrences_count()

            if occurrencesCount == -1:
                text = ""

            elif occurrencesCount == 0:
                text = "No match found"

            else:
                bounds = srSourceBuffer.get_selection_bounds()
                if len(bounds) != 0:
                    selectStart, selectEnd = bounds

                    occurrencePos = srSearchContext.get_occurrence_position(selectStart, selectEnd)

                    if occurrencePos == -1:
                        text = str(occurrencesCount) + " occurences"
                    else:
                        text = str(occurrencePos) + " of " + str(occurrencesCount) + " occurences"

                else:
                    text = str(occurrencesCount) + " occurences"

        else:
            text = ""

        self.currentTab.srResNumLabel.set_text(text)

    def on_notify_occurences_count_property_set(self, object, pspec):
        debug = False
        if debug:
            print("Notify occurences count triggered - Occurences: " + str(self.currentTab.srSearchContext.get_occurrences_count()))
        self.updateLabelOccurrences()

    def on_srReplaceEntry_activate(self, widget):
        self.currentTab.srReplaceNextBtn.clicked()

    def on_srReplaceBtns_clicked(self, widget, replaceAllFlag = False):
        # These are the key steps:
        # 1: Check if the srSearchContext and the srSearchSettings are properly set, otherwise trigger a searchNext
        # 2: Check if there is already a text-selection, otherwise trigger a searchNext
        # 3: If there is a text-selection, call the replace method (it will automatically check if the text-selection corresponds to the search-term before replacing it)
        # 4: Either case (text-selection is match or not), after (potentially) replacing text, trigger searchNext (to potentially highlight next match)
        searchText = self.currentTab.srSearchEntry.get_text()
        replaceText = self.currentTab.srReplaceEntry.get_text()
        srSearchContext = self.currentTab.srSearchContext
        if len(searchText) > 0:
            if srSearchContext:
                srSearchSettings = srSearchContext.get_settings()
                if srSearchSettings.get_search_text() and len(srSearchSettings.get_search_text()) != 0 and searchText == srSearchSettings.get_search_text():
                    srSourceBuffer = self.currentTab.sourceview.get_buffer()
                    bounds = srSourceBuffer.get_selection_bounds()
                    if len(bounds) != 0:
                        start, end = bounds
                        if replaceAllFlag:
                            srSearchContext.replace_all(replaceText, len(replaceText))
                        else:
                            srSearchContext.replace(start, end, replaceText, len(replaceText))
                            self.currentTab.srFindNextBtn.clicked()
                    else:
                        self.currentTab.srFindNextBtn.clicked()
                else:
                    self.currentTab.srFindNextBtn.clicked()
            else:
                self.currentTab.srFindNextBtn.clicked()
        else:
            pass

    def on_context_menu_create(self, webview, contextMenu, event, hitTestResult):
        return True

    def on_webview_decide_policy(self, webview, decision, decisionType):

        if decisionType == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
            navAction = decision.get_navigation_action()
            request = navAction.get_request()
            uri = str(request.get_uri())
            # print("Request uri: " + uri)
            assetsFolderPath = self.settings.get_string("assets-folder-path")
            dir_path = "file://" + os.path.realpath(assetsFolderPath) + "/"
            note_ref_path = dir_path + 'note/'
            pathLen = len(note_ref_path)
            # Check if uri is a reference to another note in database (e.g. note/*)
            if uri[:pathLen] == note_ref_path:
                noteDbId = uri[pathLen:]
                try:
                    # Check if noteDbId string is a valid integer number, otherwise display an error modal dialog
                    int(noteDbId)
                    # Check if a db record for noteDbId exists, otherwise display an error modal dialog
                    dbNote = dbRepo.findNoteByDbId(noteDbId)

                except ValueError:
                    dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, text="Invalid note db id")
                    dialog.format_secondary_text("Value '" + str(noteDbId) + "' is not a valid database id")
                    dialog.run()
                    dialog.destroy()

                except:
                    dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, text="Note id not found")
                    dialog.format_secondary_text("Note with id '" + str(noteDbId) + "' not found in database")
                    dialog.run()
                    dialog.destroy()

                else:
                    # Open tab for noteDbId
                    # Check if noteDbId is already opened in a tab
                    openedTab = self.findNotebookTabByDbId(noteDbId)
                    if (openedTab):
                        tabNum = openedTab.tabNum
                    else:
                        # Create a new tab
                        newNotebookTab = notebookTab(self.store, noteDbId=noteDbId)
                        newNotebookTab.tabNum = tabNum = self.notebook.append_page(newNotebookTab.pageWidget, newNotebookTab.titleHBox)
                        self.notebook.set_tab_reorderable(newNotebookTab.pageWidget, True)
                        self.connect_notebook_tab_signals(newNotebookTab)
                        self.notebookTabs.append(newNotebookTab)

                    self.notebook.set_current_page(tabNum)

            else:
                # Case 1: web uri (= starts with http://) -> no changes needed
                if uri[0:7] == 'http://' or uri[0:8] == 'https://':
                    Gtk.show_uri_on_window(None, uri, Gdk.CURRENT_TIME)
                else:
                    # Other cases: local file
                    # Ensure proper URI scheme - REDUNDANT since uri will automatically be converted either in "http://..." or "file:///..." form
                    # Case 2: file uri is already in proper form (= start with 'file:///') -> no changes needed
                    if uri[0:8] == 'file:///':
                        pass
                    # Case 3: file uri is absolute path -> prepend 'file://' string
                    elif uri[0:1] == '/':
                        uri = 'file://' + uri
                    # Case 4: file uri is relative path -> prepend 'file:///' + dirPath
                    else:
                        uri = dir_path + uri

                    subUri = uri[7:]
                    my_file = Path(subUri)
                    if my_file.exists():
                        Gtk.show_uri_on_window(None, uri, Gdk.CURRENT_TIME)
                    else:
                        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.WARNING,
                                                   buttons=Gtk.ButtonsType.CANCEL, text="File not found")
                        dialog.format_secondary_text("File with path '" + uri + "' not found")
                        dialog.run()
                        dialog.destroy()

            # Should probably set the ignore policy
            decision.ignore()

        else:
            return False

    def on_toolbutton_about_clicked(self, widget):
        aboutDialog = Gtk.AboutDialog.new()
        logoImage = Gtk.Image()
        logoImage.set_from_file('technenotes.png')
        logoPixbuf = logoImage.get_pixbuf()
        aboutDialog.set_logo(logoPixbuf)
        aboutDialog.set_program_name("TechneNotes")
        aboutDialog.set_version("Version 0.1")
        aboutDialog.set_website_label("Official Website")
        aboutDialog.set_website("http://www.google.it")
        aboutDialog.set_comments("Technical information and issues/bugs reporting available in the official Github repository")
        aboutDialog.set_authors(["Guido Rovera", None])
        aboutDialog.connect("response", self.on_aboutDialog_close)
        aboutDialog.show()

    def on_aboutDialog_close(self, dialog, responseId):
        dialog.destroy()

    def connect_notebook_tab_signals(self, newNotebookTab):
        newNotebookTab.closeTabBtn.connect('clicked', self.on_closetab_button_clicked, newNotebookTab.pageWidget)
        newNotebookTab.editBtn.connect('clicked', self.on_note_editbtn_clicked)
        newNotebookTab.sourceview.get_buffer().connect('changed', self.on_sourceview_buffer_changed)
        newNotebookTab.srRevealerCloseBtn.connect('clicked', self.on_srRevealerCloseBtn_clicked)
        newNotebookTab.srSearchEntry.connect('activate', self.on_srSearchEntry_activate)
        newNotebookTab.srReplaceEntry.connect('activate', self.on_srReplaceEntry_activate)
        newNotebookTab.hPaned.set_position(self.notebook.get_allocated_width() / 2)
        newNotebookTab.srFindNextBtn.connect('clicked', self.on_srFindNextPrevBtn_clicked, 1)  # Direction is an arbitrary parameter: 1 = search NEXT - 2 = search PREVIOUS
        newNotebookTab.srFindPrevBtn.connect('clicked', self.on_srFindNextPrevBtn_clicked, 0)  # Direction is an arbitrary parameter: 1 = search NEXT - 2 = search PREVIOUS
        newNotebookTab.srReplaceNextBtn.connect('clicked', self.on_srReplaceBtns_clicked)
        newNotebookTab.srReplaceAllBtn.connect('clicked', self.on_srReplaceBtns_clicked, True)
        newNotebookTab.webview.connect('context_menu', self.on_context_menu_create)
        newNotebookTab.webview.connect('decide-policy', self.on_webview_decide_policy)

win = TechneNotes()
win.connect("destroy", Gtk.main_quit)
win.connect("delete-event", win.check_unsaved_changes_before_quit)
win.show_all()
Gtk.main()

