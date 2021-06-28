import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk
import os
from pathlib import Path

class DialogFirstSetup(Gtk.Dialog):

    def __init__(self, parent):

        self.selectedDbOption = 1

        # Get application GSettings
        self.BASE_KEY = "ovh.technenotes.myapp"
        self.settings = Gio.Settings.new(self.BASE_KEY)
        dbFolderPathSetting = self.settings.get_string("db-path")

        Gtk.Dialog.__init__(self, "First Setup", parent, 0)
        self.set_default_size(500, 450)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        # To make a stockButton insensitive, use this method: Dialog.set_response_sensitive(Gtk.ResponseType.OK, True / False)

        # Make the OK button the default, so that it automatically activates when Enter key is pressed
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        dialogContentArea = self.get_content_area()
        # self.mainContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.mainContainer = Gtk.Grid()
        self.mainContainer.set_margin_top(15)
        self.mainContainer.set_margin_left(15)
        self.mainContainer.set_row_spacing(10)
        dialogContentArea.add(self.mainContainer)

        # Add content to mainContainer vBox
        ## Welcome message
        labelWelcome = Gtk.Label()
        labelWelcome.set_text("Welcome!! To start using the app, set the following options. If you accept the default settings, the necessary folders will be created inside the installation directory.")
        labelWelcome.set_hexpand(True)
        labelWelcome.set_line_wrap(True)
        labelWelcome.set_justify(Gtk.Justification.LEFT)


        ## Db storage label
        labelDbStorage = Gtk.Label()
        labelDbStorage.set_markup("<b>Database Storage</b>")
        labelDbStorage.set_halign(1)
        labelDbStorage.set_hexpand(True)

        ## RadioButtons
        button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Create new database")
        button1.connect("toggled", self.onRadioButtonToggled, 1)
        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Use existing database")
        button2.connect("toggled", self.onRadioButtonToggled, 2)

        ## FolderChooserButton for Db
        labelDbNewFCButton = Gtk.Label()
        labelDbNewFCButton.set_text("Select DB folder:")
        labelDbNewFCButton.set_halign(3)
        labelDbNewFCButton.set_hexpand(True)
        self.dbNewFCButton = Gtk.FileChooserButton.new("Select DB folder", Gtk.FileChooserAction.SELECT_FOLDER)
        # newDbPath = str(Path.home()) + "/TechneNotes/db"
        newDbPath = os.getcwd() + "/../db"
        Path(newDbPath).mkdir(parents=True, exist_ok=True)
        self.dbNewFCButton.set_filename(newDbPath)
        self.dbNewFCButton.set_halign(3)
        self.dbNewFCButton.set_hexpand(True)

        ## FileChooserButton for Db
        labelDbOpenFCButton = Gtk.Label()
        labelDbOpenFCButton.set_text("Select DB file:")
        labelDbOpenFCButton.set_halign(3)
        labelDbOpenFCButton.set_hexpand(True)
        self.dbOpenFCButton = Gtk.FileChooserButton.new("Select DB file", Gtk.FileChooserAction.OPEN)
        fcButtonFilter = Gtk.FileFilter.new()
        fcButtonFilter.add_mime_type("application/vnd.sqlite3")
        self.dbOpenFCButton.set_filter(fcButtonFilter)
        self.dbOpenFCButton.connect("file-set", self.onFileChooserFileSet)
        # Disable fileChooserButton (by default the user will be prompted to create a new db)
        self.dbOpenFCButton.set_sensitive(False)
        self.dbOpenFCButton.set_halign(3)
        self.dbOpenFCButton.set_hexpand(True)

        ## Assets storage label
        labelAssetsStorage = Gtk.Label()
        labelAssetsStorage.set_markup("<b>Assets Storage</b>")
        labelAssetsStorage.set_halign(1)
        labelAssetsStorage.set_hexpand(True)
        labelAssetsStorage.set_margin_top(10)

        ## FolderChooserButton for Assets
        labelAssetsFCButton = Gtk.Label()
        labelAssetsFCButton.set_text("Select assets folder:")
        labelAssetsFCButton.set_halign(1)
        labelAssetsFCButton.set_hexpand(True)
        self.assetsFCButton = Gtk.FileChooserButton.new("Select assets folder", Gtk.FileChooserAction.SELECT_FOLDER)
        # newDbPath = str(Path.home()) + "/TechneNotes/assets"
        newDbPath = os.getcwd() + "/../assets"
        Path(newDbPath).mkdir(parents=True, exist_ok=True)
        self.assetsFCButton.set_filename(newDbPath)
        self.assetsFCButton.set_halign(3)
        self.assetsFCButton.set_hexpand(True)
        self.assetsFCButton.set_margin_bottom(10)

        ## Checkbox for sample_media
        self.mediaButton = Gtk.CheckButton(label="Add sample media (images, videos) to the assets folder")
        self.mediaButton.set_active(True)

        labelMedia = Gtk.Label()
        labelMedia.set_text("Note: sample media are required to render the sample note. Unflag only if you are using assets from a previous installation.")
        labelMedia.set_hexpand(True)
        labelMedia.set_line_wrap(True)
        labelMedia.set_xalign(0.0)
        labelMedia.set_margin_bottom(10)

        # Add all widgets to self.mainContainer
        self.mainContainer.attach(labelWelcome, 0, 0, 2, 1)
        self.mainContainer.attach(labelDbStorage, 0, 1, 2, 1)
        self.mainContainer.attach(button1, 0, 2, 2, 1)
        self.mainContainer.attach(labelDbNewFCButton, 0, 3, 1, 1)
        self.mainContainer.attach(self.dbNewFCButton, 1, 3, 1, 1)
        self.mainContainer.attach(button2, 0, 4, 2, 1)
        self.mainContainer.attach(labelDbOpenFCButton, 0, 5, 1, 1)
        self.mainContainer.attach(self.dbOpenFCButton, 1, 5, 1, 1)
        self.mainContainer.attach(labelAssetsStorage, 0, 6, 2, 1)
        self.mainContainer.attach(labelAssetsFCButton, 0, 7, 1, 1)
        self.mainContainer.attach(self.assetsFCButton, 1, 7, 1, 1)
        self.mainContainer.attach(self.mediaButton, 0, 8, 2, 1)
        self.mainContainer.attach(labelMedia, 0, 9, 2, 1)

        self.show_all()

    def onRadioButtonToggled(self, button, value):
        # Check which button was toggled and update widget sensitivity accordingly

        # Option 1 - Create new database
        if value == 1:
            # Disable fileChooserButton of option 2
            self.dbOpenFCButton.set_sensitive(False)
            # Enable fileChooserButton of option 1
            self.dbNewFCButton.set_sensitive(True)
            # Check if the fileChooserButton value is not None and update the Gtk.ResponseType Button accordingly
            fileName = self.dbNewFCButton.get_filename()
            if fileName:
                self.set_response_sensitive(Gtk.ResponseType.OK, True)
            else:
                self.set_response_sensitive(Gtk.ResponseType.OK, False)

        # Option 2 - Open existing db file
        else:
            # Disable fileChooserButton of option 1
            self.dbNewFCButton.set_sensitive(False)
            # Enable fileChooserButton of option 2
            self.dbOpenFCButton.set_sensitive(True)
            # Check if the fileChooserButton value is not None and update the Gtk.ResponseType Button accordingly
            fileName = self.dbOpenFCButton.get_filename()
            if fileName:
                self.set_response_sensitive(Gtk.ResponseType.OK, True)
            else:
                self.set_response_sensitive(Gtk.ResponseType.OK, False)

        # Update the self.selectedDbOption parameter
        self.selectedDbOption = value

    def onFileChooserFileSet(self, button):
        self.set_response_sensitive(Gtk.ResponseType.OK, True)

    def getSelectedDbOption(self):
        # Possible values: 1= create new db, 2= open existing db
        return self.selectedDbOption

    def getDbFilename(self):
        if self.selectedDbOption == 1:
            # User has chosen to create a new db in the selected folder path
            # Absolute folder path without trailing slash (/home/.../folder)
            fileName = self.dbNewFCButton.get_filename() + "/codebits.db"
        else:
            # User has chosen to open an existing db with a specific absolute file path
            # Absolute file path (/home/.../folder/file.db)
            fileName = self.dbOpenFCButton.get_filename()

        return fileName

    def getAssetsFolderPath(self):
        # An absolute folder path without trailing slash (/home/.../folder) will be returned
        folderPath = self.assetsFCButton.get_filename()
        return folderPath

    def getMediaCheckboxValue(self):
        return self.mediaButton.get_active()
