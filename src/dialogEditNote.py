import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DialogEditNote(Gtk.Dialog):

    def __init__(self, parent, noteTitle="New note title", noteDescription="New note description"):

        Gtk.Dialog.__init__(self, "Edit note details", parent, 0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_default_size(500, 200)

        # Make the OK button the default, so that it automatically activates when Enter key is pressed
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        box = self.get_content_area()
        areaContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add(areaContainer)

        title_entry_label = Gtk.Label("Title:")
        title_entry_label.set_name("title-entry-label")
        title_entry_label.set_halign(1)
        areaContainer.pack_start(title_entry_label, False, False, 0)
        title_entry = Gtk.Entry()
        title_entry.set_activates_default(True)
        self.titleEntry = title_entry
        title_entry.set_name("title-entry-widget")
        title_entry.set_text(noteTitle)
        title_entry.set_max_length(60)
        # title_entry.set_width_chars(40)
        areaContainer.pack_start(title_entry, True, True, 0)

        desc_entry_label = Gtk.Label("Description:")
        desc_entry_label.set_name("desc-entry-label")
        desc_entry_label.set_halign(1)
        areaContainer.pack_start(desc_entry_label, False, False, 0)

        # desc_entry = Gtk.TextView()
        # desc_entry.set_wrap_mode(2)
        # self.descEntry = desc_entry
        # desc_entry_buffer = desc_entry.get_buffer()
        # self.descEntryBuffer = desc_entry_buffer
        # desc_entry_buffer.set_text(noteDescription)
        # desc_entry.set_name("desc-entry-widget")
        # areaContainer.pack_start(desc_entry, True, True, 0)

        desc_entry = Gtk.Entry()
        desc_entry.set_activates_default(True)
        self.descEntry = desc_entry
        desc_entry.set_name("desc-entry-widget")
        desc_entry.set_text(noteDescription)
        desc_entry.set_max_length(60)
        # desc_entry.set_width_chars(40)
        areaContainer.pack_start(desc_entry, True, True, 0)

        self.show_all()

    def get_note_title(self):
        return self.titleEntry.get_text()

    def get_note_description(self):
        return self.descEntry.get_text()


