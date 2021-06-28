import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DialogNewNote(Gtk.Dialog):

    def __init__(self, parent, isSingleSelection, isChildRow, orderByColumn, displayToggledOnlyModeOn):

        # IMPORTANT: In displayToggledOnlyMode (for now) the creation of new items at root level will be forbidden.
        # This way there is no need to manage the toggled status of newly created rows or to assign a temporary custom_order parameter.
        # In displaySearchTermMode the creation of new items is forbidden in any case (because there could be duplicate results in the treeview, so many tree-nodes could require an update).

        # The self.selectedOption parameter will be initially set to None and then changed to the value of the first sensitive RadioButton
        self.selectedOption = None

        Gtk.Dialog.__init__(self, "Create New Note", parent, 0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_default_size(150, 100)

        # Make the OK button the default, so that it automatically activates when Enter key is pressed
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        box = self.get_content_area()
        areaContainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add(areaContainer)

        dialogLabel = Gtk.Label("Choose new note position:")
        areaContainer.pack_start(dialogLabel, False, False, 0)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Insert as first root level item")
        button1.connect("toggled", self.on_button_toggled, 0)
        if displayToggledOnlyModeOn:
            button1.set_sensitive(False)
        else:
            # Make sure that the initially selected option is one of the sensitive options
            # In this specific case, the first two lines are redundant since self.selectedOption the first time is None and by default the first radioButton gets toggled.
            if not self.selectedOption and self.selectedOption != 0:
                button1.set_active(True)
                self.selectedOption = 0

        areaContainer.pack_start(button1, False, False, 0)

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Insert as last root level item")
        button2.connect("toggled", self.on_button_toggled, 1)
        if displayToggledOnlyModeOn:
            button2.set_sensitive(False)
        else:
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button2.set_active(True)
                self.selectedOption = 1
        areaContainer.pack_start(button2, False, False, 0)

        button3 = Gtk.RadioButton.new_from_widget(button1)
        button3.set_label("Insert as first sibling of selected item")
        button3.connect("toggled", self.on_button_toggled, 2)
        if(isSingleSelection and isChildRow):
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button3.set_active(True)
                self.selectedOption = 2
        else:
            button3.set_sensitive(False)
        areaContainer.pack_start(button3, False, False, 0)

        button4 = Gtk.RadioButton.new_from_widget(button1)
        button4.set_label("Insert as last sibling of selected item")
        button4.connect("toggled", self.on_button_toggled, 3)
        if (isSingleSelection and isChildRow):
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button4.set_active(True)
                self.selectedOption = 3
        else:
            button4.set_sensitive(False)
        areaContainer.pack_start(button4, False, False, 0)

        # normalDisplayMode: ACTIVE if isSingleSelection and orderBy == custom_order
        # displayToggledOnlyModeOn: ACTIVE if isSingleSelection and isChildRow and orderBy == custom_order
        button5 = Gtk.RadioButton.new_from_widget(button1)
        button5.set_label("Insert before selected item")
        button5.connect("toggled", self.on_button_toggled, 4)
        if orderByColumn == 0 and isSingleSelection and ((not displayToggledOnlyModeOn) or (displayToggledOnlyModeOn and isChildRow)):
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button5.set_active(True)
                self.selectedOption = 4
        else:
            button5.set_sensitive(False)
        areaContainer.pack_start(button5, False, False, 0)

        # normalDisplayMode: ACTIVE if isSingleSelection and orderBy == custom_order
        # displayToggledOnlyModeOn: ACTIVE if isChildRow and orderBy == custom_order
        button6 = Gtk.RadioButton.new_from_widget(button1)
        button6.set_label("Insert after selected item")
        button6.connect("toggled", self.on_button_toggled, 5)
        if orderByColumn == 0 and isSingleSelection and ((not displayToggledOnlyModeOn) or (displayToggledOnlyModeOn and isChildRow)):
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button6.set_active(True)
                self.selectedOption = 5
        else:
            button6.set_sensitive(False)
        areaContainer.pack_start(button6, False, False, 0)

        button7 = Gtk.RadioButton.new_from_widget(button1)
        button7.set_label("Insert as child of selected item")
        button7.connect("toggled", self.on_button_toggled, 6)
        if isSingleSelection:
            # Make sure that the initially selected option is one of the sensitive options
            if not self.selectedOption and self.selectedOption != 0:
                button7.set_active(True)
                self.selectedOption = 6
        else:
            button7.set_sensitive(False)
        areaContainer.pack_start(button7, False, False, 0)

        self.show_all()

    def on_button_toggled(self, button, optionValue):
        if button.get_active():
            self.selectedOption = optionValue

    def get_selected_option(self):
        return self.selectedOption


