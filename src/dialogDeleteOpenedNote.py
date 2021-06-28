import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DialogDeleteOpenedNote(Gtk.Dialog):

    def __init__(self, parent, noteTitle):

        Gtk.Dialog.__init__(self, "Warning: note already opened", parent, 0,
            (
                "Delete", Gtk.ResponseType.YES,
                "Skip", Gtk.ResponseType.NO,
                "Cancel", Gtk.ResponseType.CANCEL
            )
        )

        self.set_default_size(500, 150)

        box = self.get_content_area()
        message = 'The note titled "' + noteTitle + '" and/or one of its children are already opened in a tab. Would you like to close the tab(s) and delete the note?'
        messageLabel = Gtk.Label(message)
        messageLabel.set_margin_start(10)
        messageLabel.set_margin_end(10)
        messageLabel.set_margin_top(10)
        messageLabel.set_margin_bottom(10)
        box.add(messageLabel)

        self.checkBtn = Gtk.CheckButton.new_with_label("Apply to all cases")
        box.add(self.checkBtn)

        self.show_all()

    def get_apply_to_all(self):
        return self.checkBtn.get_active()
