import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

menuItemsDict = {
"File":{
    "New...":None,
    "Insert new before":None,
    "Insert new after":None,
    "Insert new as child":None,
    "Save":None,
    "Export...":None,
    "Backup / Export all...":None,
    "Import...":None,
    "Exit":None
    },
"Edit":{
    "Undo":None,
    "Redo":None,
    "Cut":None,
    "Copy":None,
    "Paste":None,
    "Delete":None,
    "Select All":None,
    "Preferences":None,
    "Render Markdown":None
    },
"Search":{
    "Find...":None,
    "Find and Replace...":None
    },
"Help":{
    "About":None
    }
}


def setupMenuBar(menuBar, agr):

    # Drop down menu
    file_menu = Gtk.Menu()
    file_menu_dropdown = Gtk.MenuItem("File")
    edit_menu = Gtk.Menu()
    edit_menu_dropdown = Gtk.MenuItem("Edit")
    search_menu = Gtk.Menu()
    search_menu_dropdown = Gtk.MenuItem("Search")
    help_menu = Gtk.Menu()
    help_menu_dropdown = Gtk.MenuItem("Help")

    # File menu items
    file_new = Gtk.MenuItem("New...") #This should call a dialaog to choose between options: Insert before/after/as child
    key, mod = Gtk.accelerator_parse("<Control>N")
    file_new.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["File"]["New..."] = file_new
    # file_insert_before = Gtk.MenuItem("Insert new before")
    # menuItemsDict["File"]["Insert new before"] = file_insert_before
    # file_insert_after = Gtk.MenuItem("Insert new after")
    # menuItemsDict["File"]["Insert new after"] = file_insert_after
    # file_insert_child = Gtk.MenuItem("Insert new as child")
    # menuItemsDict["File"]["Insert new as child"] = file_insert_child
    #file_open = Gtk.MenuItem("Open")
    #key, mod = Gtk.accelerator_parse("<Control>O")
    #file_open.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    #file_open.set_sensitive(False)
    file_save = Gtk.MenuItem("Save")
    key, mod = Gtk.accelerator_parse("<Control>S")
    file_save.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["File"]["Save"] = file_save
    # file_export = Gtk.MenuItem("Export...")
    # key, mod = Gtk.accelerator_parse("<Control>E")
    # file_export.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    # menuItemsDict["File"]["Export..."] = file_export
    # file_export_all = Gtk.MenuItem("Backup / Export all...")
    # key, mod = Gtk.accelerator_parse("<Control>B")
    # file_export_all.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    # menuItemsDict["File"]["Backup / Export all..."] = file_export_all
    # file_import = Gtk.MenuItem("Import...")
    # key, mod = Gtk.accelerator_parse("<Control>I")
    # file_import.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    # menuItemsDict["File"]["Import..."] = file_import
    file_exit = Gtk.MenuItem("Exit")
    key, mod = Gtk.accelerator_parse("<Control>Q")
    file_exit.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["File"]["Exit"] = file_exit
    
    edit_undo = Gtk.MenuItem("Undo")
    key, mod = Gtk.accelerator_parse("<Control>Z")
    edit_undo.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Undo"] = edit_undo
    edit_redo = Gtk.MenuItem("Redo")
    key, mod = Gtk.accelerator_parse("<Control>Y")
    edit_redo.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Redo"] = edit_redo
    edit_cut = Gtk.MenuItem("Cut")
    key, mod = Gtk.accelerator_parse("<Control>X")
    edit_cut.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Cut"] = edit_cut
    edit_copy = Gtk.MenuItem("Copy")
    key, mod = Gtk.accelerator_parse("<Control>C")
    edit_copy.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Copy"] = edit_copy
    edit_paste = Gtk.MenuItem("Paste")
    key, mod = Gtk.accelerator_parse("<Control>V")
    edit_paste.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Paste"] = edit_paste
    edit_delete = Gtk.MenuItem("Delete")
    key, mod = Gtk.accelerator_parse("<Control>Delete")
    edit_delete.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Delete"] = edit_delete
    edit_select_all = Gtk.MenuItem("Select All")
    key, mod = Gtk.accelerator_parse("<Control>A")
    edit_select_all.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Select All"] = edit_select_all

    edit_render_markdown = Gtk.MenuItem("Render Markdown")
    key, mod = Gtk.accelerator_parse("<Control>R")
    edit_render_markdown.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Render Markdown"] = edit_render_markdown

    edit_preferences = Gtk.MenuItem("Preferences")
    key, mod = Gtk.accelerator_parse("<Control>P")
    edit_preferences.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Edit"]["Preferences"] = edit_preferences

    search_find = Gtk.MenuItem("Find...")
    key, mod = Gtk.accelerator_parse("<Control>F")
    search_find.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Search"]["Find"] = search_find
    search_find_replace = Gtk.MenuItem("Find and Replace...")
    key, mod = Gtk.accelerator_parse("<Control>H")
    search_find_replace.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Search"]["FindReplace"] = search_find_replace

    help_about = Gtk.MenuItem("About")
    key, mod = Gtk.accelerator_parse("<Control>I")
    help_about.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
    menuItemsDict["Help"]["About"] = help_about

    # File button has dropdown
    file_menu_dropdown.set_submenu(file_menu)
    edit_menu_dropdown.set_submenu(edit_menu)
    search_menu_dropdown.set_submenu(search_menu)
    help_menu_dropdown.set_submenu(help_menu)

    # Add menu items
    file_menu.append(file_new)
    # file_menu.append(file_insert_before)
    # file_menu.append(file_insert_after)
    # file_menu.append(file_insert_child)
    #file_menu.append(file_open)
    file_menu.append(file_save)
    # file_menu.append(file_export)
    # file_menu.append(file_export_all)
    # file_menu.append(file_import)
    file_menu.append(Gtk.SeparatorMenuItem())
    file_menu.append(file_exit)

    edit_menu.append(edit_undo)
    edit_menu.append(edit_redo)
    edit_menu.append(Gtk.SeparatorMenuItem())
    edit_menu.append(edit_select_all)
    edit_menu.append(edit_cut)
    edit_menu.append(edit_copy)
    edit_menu.append(edit_paste)
    edit_menu.append(edit_render_markdown)
    edit_menu.append(Gtk.SeparatorMenuItem())
    edit_menu.append(edit_delete)        
    edit_menu.append(Gtk.SeparatorMenuItem())
    edit_menu.append(edit_preferences)

    search_menu.append(search_find)
    search_menu.append(search_find_replace)


    help_menu.append(help_about)

    # Add to menu bar
    menuBar.append(file_menu_dropdown)
    menuBar.append(edit_menu_dropdown)
    menuBar.append(search_menu_dropdown)
    menuBar.append(help_menu_dropdown)
    
    return menuItemsDict
