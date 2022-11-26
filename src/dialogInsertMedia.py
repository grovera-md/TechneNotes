import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DialogInsertMedia(Gtk.Dialog):

    def __init__(self, parent):

        self.selectedMediaOption = 1
        self.selectedImageFiles = []

        Gtk.Dialog.__init__(self, "Insert Media", parent, 0)
        self.set_default_size(500, 450)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        # To make a stockButton insensitive, use this method: Dialog.set_response_sensitive(Gtk.ResponseType.OK, True / False)

        # Make the OK button the default, so that it automatically activates when Enter key is pressed
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        dialogContentArea = self.get_content_area()
        # self.mainContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0) # This is an alternative container that I could use
        self.mainContainer = Gtk.Grid()
        self.mainContainer.set_margin_top(15)
        self.mainContainer.set_margin_left(15)
        self.mainContainer.set_row_spacing(10)
        dialogContentArea.add(self.mainContainer)

        # Add content to mainContainer vBox
        ## Welcome message
        labelWelcome = Gtk.Label()
        labelWelcome.set_text("Select media to insert:")
        labelWelcome.set_hexpand(True)
        labelWelcome.set_line_wrap(True)
        labelWelcome.set_justify(Gtk.Justification.LEFT)

        ## RadioButtons
        button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Image from clipboard")
        button1.connect("toggled", self.onRadioButtonToggled, 1)
        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Images from local files")
        button2.connect("toggled", self.onRadioButtonToggled, 2)

        ## FileChooserButton for Db
        self.fileChooserButton = Gtk.Button(label="Select images")
        self.fileChooserButton.set_halign(3)
        self.fileChooserButton.set_hexpand(True)
        self.fileChooserButton.connect("clicked", self.on_file_chooser_clicked)
        # Disable fileChooserButton (by default the user will be prompted to paste image from clipboard)
        self.fileChooserButton.set_sensitive(False)

        # fcButtonFilter = Gtk.FileFilter.new()
        # fcButtonFilter.add_pixbuf_formats()
        # self.imgOpenFCButton.set_filter(fcButtonFilter)
        # self.imgOpenFCButton.set_select_multiple(True)

        self.labelSelectedImages = Gtk.Label()
        self.labelSelectedImages.set_text("No files selected")
        self.labelSelectedImages.set_halign(3)
        self.labelSelectedImages.set_hexpand(True)

        ## Checkbox for sample_media
        self.mediaButton = Gtk.CheckButton(label="Create thumbnail and add image-gallery functionality")
        self.mediaButton.set_active(True)

        labelMedia = Gtk.Label()
        labelMedia.set_text("Note: thumbnails will be created according to default settings.")
        labelMedia.set_hexpand(True)
        labelMedia.set_line_wrap(True)
        labelMedia.set_xalign(0.0)
        labelMedia.set_margin_bottom(10)

        # Add all widgets to self.mainContainer
        self.mainContainer.attach(labelWelcome, 0, 0, 2, 1)
        self.mainContainer.attach(button1, 0, 1, 2, 1)
        self.mainContainer.attach(button2, 0, 2, 2, 1)
        self.mainContainer.attach(self.fileChooserButton, 0, 3, 1, 1)
        self.mainContainer.attach(self.labelSelectedImages, 1, 3, 1, 1)
        self.mainContainer.attach(self.mediaButton, 0, 4, 2, 1)
        self.mainContainer.attach(labelMedia, 0, 5, 2, 1)

        self.show_all()

    def onRadioButtonToggled(self, button, value):
        # Check which button was toggled and update widget sensitivity accordingly

        # Option 1 - Image from Clipboard
        if value == 1:
            # Disable fileChooserButton of option 2
            self.fileChooserButton.set_sensitive(False)
            self.set_response_sensitive(Gtk.ResponseType.OK, True)

        # Option 2 - Images from local files
        else:
            # Enable fileChooserButton of option 2
            self.fileChooserButton.set_sensitive(True)
            # Check if the fileChooserButton value is not None and update the Gtk.ResponseType Button accordingly
            if len(self.selectedImageFiles) > 0:
                self.set_response_sensitive(Gtk.ResponseType.OK, True)
            else:
                self.set_response_sensitive(Gtk.ResponseType.OK, False)

        # Update the self.selectedMediaOption parameter
        self.selectedMediaOption = value

    def getSelectedMediaOption(self):
        # Possible values: 1= Image from Clipboard, 2= Images from local files
        return self.selectedMediaOption

    def getMediaFilesname(self):
        # User has chosen to use existing image(s) with a specific absolute file path
        # Absolute file path (/home/.../folder/file.png) Img file extension may vary
        return self.selectedImageFiles

    def getMediaCheckboxValue(self):
        return self.mediaButton.get_active()

    def on_file_chooser_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Choose files", parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        fileFilter = Gtk.FileFilter.new()
        fileFilter.add_pixbuf_formats()
        dialog.set_filter(fileFilter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selectedImageFiles = dialog.get_filenames()
            filesCount = len(self.selectedImageFiles)
            if filesCount > 0:
                # Update the description label about selected files
                self.labelSelectedImages.set_text(str(filesCount) + " images selected")
                # Update dialog button sensitivity
                self.set_response_sensitive(Gtk.ResponseType.OK, True)
            # for filename in self.selectedImageFiles:
            #     print(filename)
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()