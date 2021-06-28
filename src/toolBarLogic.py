import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

toolButtonsDict = {
    "new":None,
    "delete":None,
    "save":None,
    "undo":None,
    "redo":None,
    "cut":None,
    "copy":None,
    "paste":None,
    "find":None,
    "findReplace":None,
    "renderMarkdown":None,
    "view":None,
    "search":None,
    "goPrevious":None,
    "goNext":None,
    "goToPage":None,
    "pageResults":None,
    "orderBy":None
}

def setupToolBar(toolbar, orderByColumn, orderAsc, totalResultPagesNum):

    toolbutton_new = Gtk.ToolButton()
    toolbutton_new.set_icon_name("document-new")
    toolButtonsDict["new"] = toolbutton_new
    toolbar.insert(toolbutton_new, 0)

    #toolbutton_open = Gtk.ToolButton()
    #toolbutton_open.set_icon_name("document-open")
    #toolButtonsDict["open"] = toolbutton_open
    #toolbar.insert(toolbutton_open, 1)

    toolbutton_delete = Gtk.ToolButton()
    toolbutton_delete.set_icon_name("edit-delete")
    toolButtonsDict["delete"] = toolbutton_delete
    toolbar.insert(toolbutton_delete, 1)

    # toolbar.insert(Gtk.SeparatorToolItem(), 2)

    toolbutton_save = Gtk.ToolButton()
    toolbutton_save.set_icon_name("document-save")
    toolButtonsDict["save"] = toolbutton_save
    toolbar.insert(toolbutton_save, 2)
            
    toolbutton_undo = Gtk.ToolButton()
    toolbutton_undo.set_icon_name("edit-undo")
    toolButtonsDict["undo"] = toolbutton_undo
    toolbar.insert(toolbutton_undo, 3)

    toolbutton_redo = Gtk.ToolButton()
    toolbutton_redo.set_icon_name("edit-redo")
    toolButtonsDict["redo"] = toolbutton_redo
    toolbar.insert(toolbutton_redo, 4)

    # toolbar.insert(Gtk.SeparatorToolItem(), 6)

    toolbutton_find = Gtk.ToolButton()
    toolbutton_find.set_icon_name("edit-find")
    toolButtonsDict["find"] = toolbutton_find
    toolbar.insert(toolbutton_find, 5)

    toolbutton_find_replace = Gtk.ToolButton()
    toolbutton_find_replace.set_icon_name("edit-find-replace")
    toolButtonsDict["findReplace"] = toolbutton_find_replace
    toolbar.insert(toolbutton_find_replace, 6)

    # toolbar.insert(Gtk.SeparatorToolItem(), 9)

    toolbutton_renderMarkdown = Gtk.ToolButton()
    toolbutton_renderMarkdown.set_icon_name("media-playback-start")
    toolButtonsDict["renderMarkdown"] = toolbutton_renderMarkdown
    toolbar.insert(toolbutton_renderMarkdown, 7)

    toolbutton_noteDetails = Gtk.ToolButton()
    toolbutton_noteDetails.set_icon_name("document-edit")
    toolButtonsDict["noteDetails"] = toolbutton_noteDetails
    toolbar.insert(toolbutton_noteDetails, 8)

    # toolbar.insert(Gtk.SeparatorToolItem(), 12)

    views_combo_container = Gtk.ToolItem.new()
    views_combo_hbox = Gtk.HBox()
    views_combo_label = Gtk.Label("View:")
    views_combo_hbox.pack_start(views_combo_label, False, False, 0)
    views_options = ["Code & Preview ", "Code only", "Preview only"]
    views_combo = Gtk.ComboBoxText.new()
    views_combo.set_entry_text_column(0)
    for view in views_options:
        views_combo.append_text(view)
    views_combo.set_active(0)
    views_combo_hbox.pack_start(views_combo, False, False, 7)
    views_combo_container.add(views_combo_hbox)
    toolButtonsDict["view"] = views_combo
    toolbar.insert(views_combo_container, 9)

    toolbar_spacer = Gtk.SeparatorToolItem()
    toolbar_spacer.set_draw(False)
    toolbar_spacer.set_expand(True)
    toolbar.insert(toolbar_spacer, 10)

    search_entry_container = Gtk.ToolItem.new()
    search_entry_hbox = Gtk.HBox()
    search_entry_label = Gtk.Label("Search:")
    search_entry_hbox.pack_start(search_entry_label, False, False, 0)
    search_entry = Gtk.SearchEntry()
    search_entry.set_placeholder_text("Type here...")
    search_entry.set_max_length(22)
    search_entry.set_width_chars(15)
    search_entry_hbox.pack_start(search_entry, False, False, 10)
    search_entry_container.add(search_entry_hbox)
    toolButtonsDict["search"] = search_entry
    toolbar.insert(search_entry_container, 11)

    toolbutton_toggledOnlyMode_container = Gtk.ToolItem.new()
    toolbutton_toggledOnlyMode = Gtk.ToggleButton.new_with_label("T-Mode")
    toolButtonsDict["toggledOnlyMode"] = toolbutton_toggledOnlyMode
    toolbutton_toggledOnlyMode_container.add(toolbutton_toggledOnlyMode)
    toolbar.insert(toolbutton_toggledOnlyMode_container, 12)

    # toolbutton_toggledOnlyMode.set_icon_name("mail-mark-read")
    # toggleImage = Gtk.Image.new_from_icon_name("mail-mark-read", Gtk.IconSize.LARGE_TOOLBAR)
    # toolbutton_toggledOnlyMode.set_icon_widget(toggleImage)

    toolbutton_go_previous = Gtk.ToolButton()
    toolbutton_go_previous.set_icon_name("go-previous")
    toolButtonsDict["goPrevious"] = toolbutton_go_previous
    toolbar.insert(toolbutton_go_previous, 13)
    #toolbutton_go_previous.set_sensitive(False)

    toolbutton_go_next = Gtk.ToolButton()
    toolbutton_go_next.set_icon_name("go-next")
    toolButtonsDict["goNext"] = toolbutton_go_next
    toolbar.insert(toolbutton_go_next, 14)

    toolbar_page_entry_container = Gtk.ToolItem.new()
    toolbar_page_entry_hbox = Gtk.HBox()
    toolbar_page_entry_label = Gtk.Label("Go to page:")
    toolbar_page_entry_hbox.pack_start(toolbar_page_entry_label, False, False, 0)
    toolbar_page_entry = Gtk.Entry()
    toolbar_page_entry.set_text("1")
    toolbar_page_entry.set_max_length(4)
    toolbar_page_entry.set_width_chars(5)
    toolbar_page_entry_hbox.pack_start(toolbar_page_entry, False, False, 5)
    toolButtonsDict["goToPage"] = toolbar_page_entry
    toolbar_page_entry_label_2 = Gtk.Label("of")
    toolbar_page_entry_hbox.pack_start(toolbar_page_entry_label_2, False, False, 0)
    toolbar_page_entry_label_3 = Gtk.Label(str(totalResultPagesNum))
    toolbar_page_entry_hbox.pack_start(toolbar_page_entry_label_3, False, False, 5)
    toolButtonsDict["totalPagesNum"] = toolbar_page_entry_label_3
    toolbar_page_entry_container.add(toolbar_page_entry_hbox)
    toolbar.insert(toolbar_page_entry_container, 15)

    rows_combo_container = Gtk.ToolItem.new()
    rows_combo_hbox = Gtk.HBox()
    rows_combo_label = Gtk.Label("Page results:")
    rows_combo_hbox.pack_start(rows_combo_label, False, False, 5)
    rows_options = ["10", "20", "30", "50", "75", "100", "200"]
    #rows_combo = Gtk.ComboBoxText.new_with_entry() #This is useful if you want the combobox to also be editable
    rows_combo = Gtk.ComboBoxText.new()
    rows_combo.set_entry_text_column(0)
    for option in rows_options:
        rows_combo.append_text(option)
    rows_combo.set_active(0)
    rows_combo_hbox.pack_start(rows_combo, False, False, 5)
    rows_combo_container.add(rows_combo_hbox)
    toolButtonsDict["pageResults"] = rows_combo
    toolbar.insert(rows_combo_container, 16)

    order_combo_container = Gtk.ToolItem.new()
    order_combo_hbox = Gtk.HBox()
    order_combo_label = Gtk.Label("Order by:")
    order_combo_hbox.pack_start(order_combo_label, False, False, 5)
    order_options = ["Custom", "Title", "Created", "Updated"]
    order_combo = Gtk.ComboBoxText.new()
    order_combo.set_entry_text_column(0)
    for option in order_options:
        order_combo.append_text(option)

    order_combo.set_active(orderByColumn)

    order_combo_hbox.pack_start(order_combo, False, False, 5)
    order_combo_container.add(order_combo_hbox)
    toolButtonsDict["orderBy"] = order_combo
    toolbar.insert(order_combo_container, 17)

    dir_combo_container = Gtk.ToolItem.new()
    dir_combo_hbox = Gtk.HBox()
    dir_options = ["Asc", "Desc"]
    dir_combo = Gtk.ComboBoxText.new()
    for option in dir_options:
        dir_combo.append_text(option)
    if orderAsc:
        dir_combo.set_active(0)
    else:
        dir_combo.set_active(1)
    dir_combo_hbox.pack_start(dir_combo, False, False, 5)
    dir_combo_container.add(dir_combo_hbox)
    toolButtonsDict["orderDir"] = dir_combo
    toolbar.insert(dir_combo_container, 18)
    
    return toolButtonsDict
