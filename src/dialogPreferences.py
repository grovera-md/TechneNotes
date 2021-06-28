import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, Pango
import os

class DialogPreferences(Gtk.Dialog):

    def __init__(self, parent):

        # Get application GSettings
        self.BASE_KEY = "ovh.technenotes.myapp"
        self.settings = Gio.Settings.new(self.BASE_KEY)
        fontStringSettings = self.settings.get_string("code-font")

        Gtk.Dialog.__init__(self, "Preferences", parent, 0)
        self.set_default_size(800, 600)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        # Make the OK button the default, so that it automatically activates when Enter key is pressed
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        dialogContentArea = self.get_content_area()
        self.mainContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        dialogContentArea.add(self.mainContainer)

        # Add dialog content to mainContainer vBox
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.LEFT)
        self.notebook.set_vexpand(True)
        self.mainContainer.pack_start(self.notebook, True, True, 0)

        # TAB: "General"
        # - Tab Grid container
        self.page1 = Gtk.Grid()
        self.page1.set_margin_top(11)
        self.page1.set_margin_left(15)
        self.page1.set_row_spacing(10)

        # - DB FileChooserButton
        labelDbFCButton = Gtk.Label()
        labelDbFCButton.set_markup("<b>Change db folder path</b>")
        labelDbFCButton.set_halign(1)
        labelDbFCButton.set_hexpand(True)
        labelDbFCButton.set_valign(3)
        labelDbFCButton.set_margin_top(10)
        labelDbFCButtonNote = Gtk.Label()
        labelDbFCButtonNote.set_text("Note: db file will be simply moved and no data will be lost")
        labelDbFCButtonNote.set_halign(1)
        labelDbFCButtonNote.set_hexpand(True)
        labelDbFCButtonNote.set_valign(3)
        labelDbFCButtonNote.set_margin_bottom(10)
        self.dbFCButton = Gtk.FileChooserButton.new("Select DB folder", Gtk.FileChooserAction.SELECT_FOLDER)
        dbFilePathSetting = self.settings.get_string("db-path")
        dbFolderPath = os.path.dirname(os.path.realpath(dbFilePathSetting))
        self.dbFCButton.set_filename(dbFolderPath)
        self.dbFCButton.connect("file-set", self.on_db_fcbutton_file_set)
        self.dbFCButton.set_halign(3)
        self.dbFCButton.set_hexpand(True)
        self.dbFCButton.set_valign(3)
        self.page1.attach(labelDbFCButton, 0, 0, 1, 1)
        self.page1.attach(labelDbFCButtonNote, 0, 1, 1, 1)
        self.page1.attach(self.dbFCButton, 1, 0, 1, 2)

        # - Assets FileChooserButton
        labelAssetsFCButton = Gtk.Label()
        labelAssetsFCButton.set_markup("<b>Change assets folder path</b>")
        labelAssetsFCButton.set_halign(1)
        labelAssetsFCButton.set_hexpand(True)
        labelAssetsFCButton.set_margin_top(10)
        labelAssetsFCButtonNote = Gtk.Label()
        labelAssetsFCButtonNote.set_text("Note: all assets will be moved and no data will be lost")
        labelAssetsFCButtonNote.set_halign(1)
        labelAssetsFCButtonNote.set_hexpand(True)
        labelAssetsFCButtonNote.set_margin_bottom(10)
        self.assetsFCButton = Gtk.FileChooserButton.new("Select assets folder", Gtk.FileChooserAction.SELECT_FOLDER)
        assetsFolderPathSetting = self.settings.get_string("assets-folder-path")
        assetsFolderPath = os.path.realpath(assetsFolderPathSetting)
        self.assetsFCButton.set_filename(assetsFolderPath)
        self.assetsFCButton.connect("file-set", self.on_assets_fcbutton_file_set)
        self.assetsFCButton.set_halign(3)
        self.assetsFCButton.set_hexpand(True)
        self.assetsFCButton.set_valign(3)
        self.page1.attach(labelAssetsFCButton, 0, 2, 1, 1)
        self.page1.attach(labelAssetsFCButtonNote, 0, 3, 1, 1)
        self.page1.attach(self.assetsFCButton, 1, 2, 1, 2)

        # - Tab label
        labelGeneralSection = Gtk.Label()
        labelGeneralSection.set_markup("<b>General</b>")
        labelGeneralSection.set_margin_left(5)
        labelGeneralSection.set_margin_right(5)

        # - Add tab to notebook
        self.notebook.append_page(self.page1, labelGeneralSection)


        self.page2 = Gtk.Grid()
        self.page2.set_margin_top(13)
        self.page2.set_margin_left(15)
        self.page2.set_margin_bottom(15)
        self.page2.set_row_spacing(25)
        self.fontButton = Gtk.FontButton.new()
        self.fontButton.set_font(fontStringSettings)
        self.fontButton.connect("font-set", self.on_fontbutton_font_set)
        self.fontButton.set_halign(3)
        self.fontButton.set_hexpand(True)
        labelFont = Gtk.Label()
        labelFont.set_markup("<b>Markdown font style</b>")
        labelFont.set_halign(1)
        labelFont.set_hexpand(True)
        self.page2.attach(labelFont, 0, 0, 1, 1)
        self.page2.attach(self.fontButton, 1, 0, 1, 1)

        # CSS TextView for Webview styling options (user will be able to edit CSS directly - Reset option should be added)
        labelWebviewCSS = Gtk.Label()
        labelWebviewCSS.set_markup("<b>Webview CSS</b>\rEdit the following CSS rules to change notes appearance.")
        labelWebviewCSS.set_halign(1)
        self.page2.attach(labelWebviewCSS, 0, 1, 2, 1)
        webviewCSSsw = Gtk.ScrolledWindow()
        webviewCSSsw.set_hexpand(True)
        webviewCSSsw.set_vexpand(True)
        self.page2.attach(webviewCSSsw, 0, 2, 2, 1)
        self.webviewCSStw = Gtk.TextView()
        self.webviewCSSbuf = self.webviewCSStw.get_buffer()
        # Get custom user webview css
        cssFile = open("webview/css/css-webview-user-custom-theme.css", "r")
        cssString = cssFile.read()
        cssFile.close()
        self.webviewCSSbuf.set_text(cssString)
        webviewCSSsw.add(self.webviewCSStw)
        # Add "Apply" and "Reset" buttons
        webviewCSSBtnBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        webviewCSSBtnBox.set_halign(2)
        self.webviewCSSsaveBtn = Gtk.Button.new_with_label("Apply")
        self.webviewCSSresetBtn = Gtk.Button.new_with_label("Reset")
        webviewCSSBtnBox.pack_start(self.webviewCSSsaveBtn, False, False, 0)
        webviewCSSBtnBox.pack_start(self.webviewCSSresetBtn, False, False, 5)
        self.page2.attach(webviewCSSBtnBox, 0, 3, 2, 1)

        # Add new page to the notebook
        labelEditorSection = Gtk.Label()
        labelEditorSection.set_markup("<b>Editor</b>")
        labelEditorSection.set_margin_left(5)
        labelEditorSection.set_margin_right(5)
        labelEditorSection.set_margin_top(5)
        self.notebook.append_page(self.page2, labelEditorSection)

        self.show_all()

    def on_fontbutton_font_set(self, fontButton):
        # Check if the selected font is different than the "code-font-tmp" setting; if so, update the "code-font-tmp" setting. The "code-font-tmp" listener should be automatically triggered.
        fontStringSettingsTmp = self.settings.get_string("code-font-tmp") # String representation of a Pango.FontDescription object
        fontDescSettingsTmp = Pango.FontDescription.from_string(fontStringSettingsTmp)

        fontDescButton = self.fontButton.get_font_desc()
        if fontDescSettingsTmp.equal(fontDescButton):
            pass
        else:
            # update the "code-font-tmp" setting
            fontStringButton = fontDescButton.to_string() # String representation of a Pango.FontDescription object
            self.settings.set_string("code-font-tmp", fontStringButton)

    def get_webview_custom_css(self):
        cssString = self.webviewCSSbuf.get_text(self.webviewCSSbuf.get_start_iter(), self.webviewCSSbuf.get_end_iter(), False)
        return cssString

    def on_db_fcbutton_file_set(self, fcButton):
        # Get the selected db folder path (not file path)
        selectedFolderPath = fcButton.get_filename()
        # Get the current db filename from GSettings
        dbFilePathSetting = self.settings.get_string("db-path-tmp")
        dbFileName = os.path.basename(dbFilePathSetting)
        # Check if the selected path is different from the one saved in the GSettings. If so, save the new path in the corresponding -tmp GSetting
        selectedFilePath = selectedFolderPath + "/" + dbFileName
        if selectedFilePath != dbFilePathSetting:
            self.settings.set_string("db-path-tmp", selectedFilePath)

    def on_assets_fcbutton_file_set(self, fcButton):
        # Get the selected assets folder path (not file path)
        selectedFolderPath = fcButton.get_filename()
        # Get the current assets folder from GSettings
        assetsFolderPathSetting = self.settings.get_string("assets-folder-path-tmp")
        # Check if the selected folder path is different from the one saved in the GSettings. If so, save the new path in the corresponding -tmp GSetting
        if selectedFolderPath != assetsFolderPathSetting:
            self.settings.set_string("assets-folder-path-tmp", selectedFolderPath)