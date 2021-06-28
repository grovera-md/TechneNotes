import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DialogCloseTab(Gtk.Dialog):

    def __init__(self, parent, displayCheckBoxFlag = False):

        Gtk.Dialog.__init__(self, "Unsaved changes", parent, 0)
        self.add_buttons("Save", Gtk.ResponseType.YES, "Discard", Gtk.ResponseType.NO, "Cancel", Gtk.ResponseType.CANCEL)

        self.set_default_size(500, 150)

        box = self.get_content_area()
        message = "This document contains unsaved changes. Would you like to save them?"
        messageLabel = Gtk.Label(message)
        messageLabel.set_margin_start(10)
        messageLabel.set_margin_end(10)
        messageLabel.set_margin_top(10)
        messageLabel.set_margin_bottom(10)
        box.add(messageLabel)

        if displayCheckBoxFlag:
            self.checkBtn = Gtk.CheckButton.new_with_label("Apply to all cases")
            box.add(self.checkBtn)

        self.show_all()

    def get_apply_to_all(self):
        return self.checkBtn.get_active()
