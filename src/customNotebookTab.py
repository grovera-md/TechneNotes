import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GtkSource, GLib, WebKit2, Gio, Pango
import dbRepository as dbRepo
import renderMarkdown as renderMarkdown
import os

class notebookTab:

    # Initializer for newly created notes (no record in database)
    def __init__(self, treestore, noteDbId=None, treeRowRef=None, refNoteDbId=None, position=0, titleString=None, descriptionString=None):
        self.refNoteDbId = refNoteDbId
        self.position = position
        self.needsSaving = False # This parameter is True for newly-generated notes (notes that aren't already in the database)
        self.pendingUpdatesFlag = False # This parameter is set to True if there are unsaved changes (either a note is newly generated or the user made some changes to its content)
        self.noteDbId = noteDbId
        if self.noteDbId:
            recursiveDbIdPath = dbRepo.findRecursivePathByDbId(self.noteDbId)
            self.recursiveDbIdPathList = [subdict["id"] for subdict in recursiveDbIdPath]
        else:
            self.recursiveDbIdPathList = []  # This parameter will be empty for new notes and will be filled when saving the note in the db; path could change after d&d the item or one of its parents
        # pathButtonsList is a list of the button widgets in the Path section of the note-details revealer. This is necessary to later hook-up the callbacks in the main file
        self.pathButtonsList = []
        self.lastPathLabel = None
        self.treeRowRef = treeRowRef
        self.tabNum = None
        self.titleHBox = None
        self.tabLabel = None
        self.closeTabBtn = None
        self.pageWidget = None
        # self.titleEntry = None
        self.titleString = titleString
        self.revealerVBox = None
        self.revealerTitleLabel = None
        self.revealerNoteIdLabel = None
        # self.descriptionEntry = None
        self.descriptionString = descriptionString
        self.revealerDescLabel = None
        self.recursiveDbIdPathBox = None
        self.hPaned = None
        self.sourceview = None
        self.webview = None
        self.editBtn = None
        self.revealer = None
        # self.hContainer = None
        self.srRevealer = None
        self.srSearchParam = 0
        self.srSearchContext = None
        self.idleUpdateLabelId = 0
        self.srResNumLabel = None
        self.srRevealerCloseBtn = None
        self.srSearchEntry = None
        self.srFindNextBtn = None
        self.srFindPrevBtn = None
        self.srReplaceLabel = None
        self.srReplaceEntry = None
        self.srReplaceNextBtn = None
        self.srReplaceAllBtn = None

        if self.noteDbId:
            #retrieve note data from noteDbId
            note = dbRepo.findNoteByDbId(self.noteDbId)
            self.titleString = note.title
            self.descriptionString = note.description
            sourceviewText = note.content
        else:
            self.needsSaving = True
            self.pendingUpdatesFlag = True
            # titleEntryText = "New note title"
            # descriptionEntryText = "New note description"
            sourceviewText = ""

        # Tab content: a single label/text
        tab_widget_h_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_widget_h_container.set_name("noteDetailsTab")
        self.pageWidget = tab_widget_h_container
        #tab_widget_h_container.set_name(str(row_values[0]) + "-")
        tab_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # # Title and Description Entries section
        # tab_widget_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        # title_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        # title_entry_label = Gtk.Label("Title:")
        # title_entry_label.set_name("tab-title-entry-label")
        # title_wrapper.pack_start(title_entry_label, False, False, 0)
        # title_entry = Gtk.Entry()
        # self.titleEntry = title_entry
        # title_entry.set_name("tab-title-entry-widget")
        # #title_entry.set_text(str(row_values[1]))
        # title_entry.set_text(titleEntryText)
        # title_entry.set_max_length(60)
        # title_entry.set_width_chars(50)
        # title_wrapper.pack_start(title_entry, False, False, 0)
        # tab_widget_entry_box.pack_start(title_wrapper, False, False, 0)
        #
        # description_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        # description_entry_label = Gtk.Label("Description:")
        # description_entry_label.set_name("tab-description-entry-label")
        # description_wrapper.pack_start(description_entry_label, False, False, 0)
        # description_entry = Gtk.Entry()
        # self.descriptionEntry = description_entry
        # description_entry.set_name("tab-description-entry-widget")
        # #description_entry.set_text(str(row_values[2]))
        # description_entry.set_text(descriptionEntryText)
        # description_entry.set_max_length(100)
        # description_entry.set_width_chars(100)
        # description_wrapper.pack_start(description_entry, True, True, 0)
        # tab_widget_entry_box.pack_start(description_wrapper, True, True, 0)
        #
        # tab_widget.pack_start(tab_widget_entry_box, False, False, 15)

        # Insert new Title and Description labels here

        # editHbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # showHideBtn = Gtk.Button.new_from_icon_name("go-down", 2)
        # self.showHideBtn = showHideBtn
        # editHbox.pack_start(showHideBtn, False, False, 5)
        # showHideBtnLabel = Gtk.Label.new("Show Title and Description")
        # showHideBtnLabel.set_halign(1)
        # self.showHideLabel = showHideBtnLabel
        # editHbox.pack_start(showHideBtnLabel, True, True, 0)
        # tab_widget.pack_start(editHbox, False, False, 0)

        # showHideToggleBtn = Gtk.ToggleButton.new_with_label("Show / Hide")
        # showHideToggleBtn.set_halign(1)
        # self.toggleBtn = showHideToggleBtn
        # tab_widget.pack_start(showHideToggleBtn, False, False, 10)

        revealer = Gtk.Revealer.new()

        sectionVbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.revealerVBox = sectionVbox
        sectionVbox.set_margin_top(12)
        sectionVbox.set_margin_left(12)
        sectionVbox.set_margin_bottom(10)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(7)
        editBtn = Gtk.Button.new_from_icon_name("document-edit", 2) # Icon: accessories-text-editor
        self.editBtn = editBtn
        grid.attach(editBtn, 0, 1, 1, 2)
        noteIdLabel = Gtk.Label()
        noteIdLabelContent = str(self.noteDbId) if self.noteDbId else "n.a."
        noteIdLabel.set_markup("<b>Id:</b> " + noteIdLabelContent)
        noteIdLabel.set_halign(1)
        self.revealerNoteIdLabel = noteIdLabel
        grid.attach(noteIdLabel, 1, 0, 1, 1)
        titleLabel = Gtk.Label()
        titleLabel.set_markup("<b>Title:</b> " + self.titleString)
        titleLabel.set_halign(1)
        self.revealerTitleLabel = titleLabel
        grid.attach(titleLabel, 1, 1, 1, 1)
        descriptionLabel = Gtk.Label()
        descriptionLabel.set_markup("<b>Description:</b> " + self.descriptionString)
        self.revealerDescLabel = descriptionLabel
        descriptionLabel.set_line_wrap(True)
        grid.attach(descriptionLabel, 1, 2, 1, 1)
        sectionVbox.pack_start(grid, False, False, 0)
        if self.noteDbId:
            self.createRecursiveDbIdPathBox(recursiveDbIdPath)

        revealer.add(sectionVbox)
        self.revealer = revealer
        tab_widget.pack_start(revealer, False, False, 0)

        # otherLabel = Gtk.Label.new("New awesome text!!!")
        # otherLabel.set_halign(1)
        # otherLabel.set_xalign(0.0)
        # # otherLabel.set_justify(Gtk.Justification.LEFT)
        # # otherLabel.set_margin_left(0)
        # tab_widget.pack_start(otherLabel, True, True, 0)

        hpaned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        hpaned.set_name("tab-hpaned")
        self.hPaned = hpaned
        self.hPaned.set_wide_handle(True) #TODO: This should be an option because it's only useful in non-default OS themes
        # Gtk.Widget.set_size_request(hpaned, 800, -1)

        childBox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hpaned.pack1(childBox1, True, False)
        # Gtk.Widget.set_size_request(childBox1, 400, -1)

        childBox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hpaned.pack2(childBox2, True, False)
        # Gtk.Widget.set_size_request(childBox2, 400, -1)


        sw1 = Gtk.ScrolledWindow()
        sw1.set_hexpand(True)
        sw1.set_vexpand(True)

        editor = GtkSource.View.new()
        self.sourceview = editor
        editor.set_show_line_numbers(True)
        editor.set_auto_indent(True)
        editor.set_highlight_current_line(True)
        editor.set_wrap_mode(Gtk.WrapMode.WORD)
        editor.set_tab_width(4)
        editor.set_top_margin(10)
        editor.set_bottom_margin(10)
        editor.set_left_margin(5)
        editor_buffer = editor.get_buffer()
        editor_buffer.begin_not_undoable_action()
        editor_buffer.set_text(sourceviewText)
        editor_buffer.end_not_undoable_action()

        # style_scheme = self.buffer.get_style_scheme() #this was already commented

        scheme_manager = GtkSource.StyleSchemeManager.get_default()
        # scheme_color = scheme_manager.get_scheme('monokai-extended')
        scheme_color = scheme_manager.get_scheme('codezone-tech')
        editor_buffer.set_style_scheme(scheme_color)
        syntax_language = GtkSource.LanguageManager.get_default().get_language('markdown-extra-tech')
        editor_buffer.set_language(syntax_language)
        editor_buffer.set_highlight_syntax(True)

        # Get application GSettings
        self.BASE_KEY = "ovh.technenotes.myapp"
        settings = Gio.Settings.new(self.BASE_KEY)
        fontString = settings.get_string("code-font")

        # Set custom font with Pango
        self.sourceview.modify_font(Pango.FontDescription.from_string(fontString)) # String representation of a Pango.FontDescription object
        # Options: Sans Regular 10, Source Sans Pro Regular 10, System-ui Regular 10, Ubuntu Regular 10, Ubuntu Mono Regular 10, Umpush Regular 10,

        # Apply custom CSS rules to GtkSource widget
        # editor_context = editor.get_style_context()
        # editor_provider = Gtk.CssProvider.new()
        # editor_provider.load_from_path("css/custom-gtk-styles.css")
        # editor_context.add_provider(editor_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        sw1.add(editor)

        childBox1.pack_start(sw1, True, True, 0)

        # Search and Replace Revealer
        srRevealer = Gtk.Revealer.new()
        self.srRevealer = srRevealer

        srGrid = Gtk.Grid()
        srGrid.set_column_spacing(10)
        srGrid.set_row_spacing(7)
        srGrid.set_margin_top(5)
        srGrid.set_margin_bottom(5)
        srGrid.set_margin_left(7)
        srGrid.set_margin_right(7)

        paramsBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        paramsBox.set_hexpand(True)
        srSearchParam1 = Gtk.RadioButton.new_with_label_from_widget(None, "Case insensitive")
        srSearchParam1.connect("toggled", self.on_srSearchParam_toggled, 0)
        srSearchParam2 = Gtk.RadioButton.new_with_label_from_widget(srSearchParam1, "Case sensitive")
        srSearchParam2.connect("toggled", self.on_srSearchParam_toggled, 1)
        srSearchParam3 = Gtk.RadioButton.new_with_label_from_widget(srSearchParam1, "Regular expression")
        srSearchParam3.connect("toggled", self.on_srSearchParam_toggled, 2)
        paramsBox.pack_start(srSearchParam1, False, False, 0)
        paramsBox.pack_start(srSearchParam2, False, False, 0)
        paramsBox.pack_start(srSearchParam3, False, False, 0)

        searchResLabel = Gtk.Label.new("Results: ")
        searchResLabel.set_margin_left(40)
        searchResLabel.set_halign(1)
        self.srResNumLabel = Gtk.Label.new("")
        self.srResNumLabel.set_halign(1)
        paramsBox.pack_start(searchResLabel, False, False, 0)
        paramsBox.pack_start(self.srResNumLabel, False, False, 0)

        self.srRevealerCloseBtn = Gtk.Button()
        self.srRevealerCloseBtn.set_focus_on_click(False)
        closeIcon = Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        self.srRevealerCloseBtn.set_image(closeIcon)
        self.srRevealerCloseBtn.set_relief(Gtk.ReliefStyle.NONE)
        # self.srRevealerCloseBtn.set_halign(2) # Not necessary if you use Gtk.Box.pack_end() method
        paramsBox.pack_end(self.srRevealerCloseBtn, False, False, 0)

        srGrid.attach(paramsBox, 0, 0, 4, 1)

        searchLabel = Gtk.Label.new("Search: ")
        searchLabel.set_halign(1)
        searchLabel.set_margin_left(5)
        searchLabel.set_hexpand(False)
        srGrid.attach(searchLabel, 0, 1, 1, 1)

        searchEntry = Gtk.Entry()
        searchEntry.set_hexpand(True)
        self.srSearchEntry = searchEntry
        srGrid.attach(searchEntry, 1, 1, 1, 1)

        self.srFindNextBtn = Gtk.Button.new_with_label("Next")
        self.srFindNextBtn.set_hexpand(False)
        self.srFindPrevBtn = Gtk.Button.new_with_label("Previous")
        self.srFindPrevBtn.set_hexpand(False)
        srGrid.attach(self.srFindNextBtn, 2, 1, 1, 1)
        srGrid.attach(self.srFindPrevBtn, 3, 1, 1, 1)

        replaceLabel = Gtk.Label.new("Replace: ")
        replaceLabel.set_halign(1)
        replaceLabel.set_margin_left(5)
        self.srReplaceLabel = replaceLabel
        srGrid.attach(replaceLabel, 0, 2, 1, 1)

        replaceEntry = Gtk.Entry()
        self.srReplaceEntry = replaceEntry
        srGrid.attach(replaceEntry, 1, 2, 1, 1)

        self.srReplaceNextBtn = Gtk.Button.new_with_label("Replace Next")
        self.srReplaceAllBtn = Gtk.Button.new_with_label("Replace All")
        srGrid.attach(self.srReplaceNextBtn, 2, 2, 1, 1)
        srGrid.attach(self.srReplaceAllBtn, 3, 2, 1, 1)

        srRevealer.add(srGrid)

        childBox1.pack_start(srRevealer, False, False, 0)

        sw2 = Gtk.ScrolledWindow()
        sw2.set_size_request(580, -1)
        sw2.set_hexpand(True)
        sw2.set_vexpand(True)

        browser_settings = WebKit2.Settings.new()
        self.webview = WebKit2.WebView.new()
        browser_settings.set_property('javascript-can-access-clipboard', bool(True))
        self.webview.set_settings(browser_settings)
        # TODO: change webview background color depending on theme
        bgColor = Gdk.RGBA(0.169, 0.169, 0.169, 1)
        self.webview.set_background_color(bgColor)

        childBox2.pack_start(sw2, True, True, 0)
        sw2.add(self.webview)

        assetsFolderPath = settings.get_string("assets-folder-path")
        dir_path = "file:" + os.path.realpath(assetsFolderPath) + "/"
        # dir_path = "file:"+ os.path.dirname(os.path.realpath(__file__)) + "/"
        renderedMarkdown = renderMarkdown.render(sourceviewText)
        self.webview.load_html(renderedMarkdown, dir_path)
        # inputTxtFile = open('html-sample.html', 'r')
        # markdownString = inputTxtFile.read()
        # self.webview.load_html_string(markdownString, dir_path)

        tab_widget.pack_start(hpaned, True, True, 0)

        tab_widget_h_container.pack_start(tab_widget, True, True, 0)

        tab_widget_h_container.show_all()

        # Tab title: hbox with a label + close button
        title_hbox = Gtk.HBox(False, 0)
        # label
        #label = Gtk.Label("Row " + str(row_values[0]) + " tab")
        label = Gtk.Label(self.titleString)
        self.tabLabel = label
        if self.pendingUpdatesFlag:
            escapedTitleString = GLib.markup_escape_text(self.titleString)
            markupTitleString = "<b>" + escapedTitleString + " *</b>"
            label.set_markup(markupTitleString)
        else:
            label.set_text(self.titleString)
        title_hbox.pack_start(label, True, True, 4)
        # close button
        tab_btn = Gtk.Button()
        self.closeTabBtn = tab_btn
        tab_btn.set_focus_on_click(False)
        close_image = Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        # tab_btn.add(close_image)
        tab_btn.set_image(close_image)
        tab_btn.set_relief(Gtk.ReliefStyle.NONE)
        title_hbox.pack_start(tab_btn, False, False, 2)
        #tab_btn.connect('clicked', self.on_closetab_button_clicked, tab_widget)
        title_hbox.show_all()

        self.titleHBox = title_hbox
        # self.hContainer = tab_widget_h_container
        #self.notebook.set_current_page(new_page_num)

        # Debug
        # hwa = self.webview.get_major_version()
        # print("Hw accel policy: " + str(hwa))

    def on_srSearchParam_toggled(self, button, optionValue):
        if button.get_active():
            self.srSearchParam = optionValue

    def get_srSearchParam(self):
        return self.srSearchParam

    def createRecursiveDbIdPathBox(self, recursivePathList):
        # Check if the currentTab already has a recursiveDbIdPathBox, if so destroy it and clear the self.pathButtonsList
        if self.recursiveDbIdPathBox:
            self.recursiveDbIdPathBox.destroy()
            self.pathButtonsList.clear()

        recursiveDbIdPathBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        # self.recursiveDbIdPathBox = recursiveDbIdPathBox
        recursiveDbIdPathBox.set_halign(1)
        pathLabel = Gtk.Label()
        pathLabel.set_markup("<b>Path:</b> ")
        recursiveDbIdPathBox.pack_start(pathLabel, False, False, 0)
        pathListLength = len(recursivePathList)
        i = 0
        for itemDict in recursivePathList:
            i += 1
            itemDictTitleLabel = Gtk.Label.new(str(itemDict["title"]))
            recursiveDbIdPathBox.pack_start(itemDictTitleLabel, False, False, 0)
            if i < pathListLength:
                newTabBtn = Gtk.Button.new_from_icon_name("tab-new", 2)
                newTabBtn.set_name(str(itemDict["id"]))
                self.pathButtonsList.append(newTabBtn)
                recursiveDbIdPathBox.pack_start(newTabBtn, False, False, 0)
                separator = Gtk.Label.new("/")
                recursiveDbIdPathBox.pack_start(separator, False, False, 0)

            # Make the last label (which contains the note title) available for future updates (self.lastPathLabel) (ex. when user changes the note name before saving)
            if i == pathListLength:
                self.lastPathLabel = itemDictTitleLabel

        self.revealerVBox.pack_start(recursiveDbIdPathBox, False, False, 0)
        self.recursiveDbIdPathBox = recursiveDbIdPathBox
        self.revealerVBox.show_all()
