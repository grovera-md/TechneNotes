import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import dbRepository as dbRepo
import sternBrocotGr as sternBrocot
import datetime as datetime

## IN SOSPESO: connect() passare custom parameter treeview a button press


TARGETS = [('MY_TREE_MODEL_ROW', Gtk.TargetFlags.SAME_WIDGET, 0), ('text/plain', 0, 1), ('TEXT', 0, 2), ('STRING', 0, 3)]

def rowSelectionFunction(selection, model, path, is_selected, data):
    new_sel_iter = model.get_iter(path)
    model, pathlist = selection.get_selected_rows()
    is_allowed = True
    for path_i in pathlist:
        iter = model.get_iter(path_i)
        # Check if iter in pathlist is_ancestor of the new_sel_iter
        if model.is_ancestor(iter, new_sel_iter) or model.is_ancestor(new_sel_iter, iter):
            is_allowed = False
            break
    return is_allowed

def enableDnd(treeview):
    treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, TARGETS, Gdk.DragAction.DEFAULT|Gdk.DragAction.MOVE)
    treeview.enable_model_drag_dest(TARGETS, Gdk.DragAction.DEFAULT) #Gdk.DragAction.MOVE)
    treeview.drag_dest_add_text_targets()
    treeview.drag_source_add_text_targets()

def disableDnd(treeview):
    treeview.unset_rows_drag_source()
    treeview.unset_rows_drag_dest()

def dragDataGet(treeview, context, selection, target_id, etime):
    treeselection = treeview.get_selection()
    model, pathlist = treeselection.get_selected_rows()

    #Notes
    #path = model.get_path(iter)
    #print("Get data method - Path is " + str(path))
    #data = bytes(str(path), "utf-8")
    #selection.set(selection.get_target(), 8, data)

    array = []
    for path_i in pathlist:
        array.append(str(path_i))

    data = json.dumps(array)
    data = bytes(data, "utf-8")

    selection.set(selection.get_target(), 8, data)

def moveChildRows(treestore, from_parent, to_parent, move_flag, toggledRowsDict, toggledStatusAvailable):
    debug = False

    newParentDbId = treestore[to_parent][0]
    n_columns = treestore.get_n_columns()
    iter = treestore.iter_children(from_parent)
    counter = 0
    while iter:
        values = treestore.get(iter, *range(n_columns))
        values = list(values)

        # Update children in db ONLY if you are copying rows, and not moving them
        if not move_flag:
            sourceNoteDbId = treestore[iter][0]
            # newParentDbId = treestore[to_parent][0]
            copiedNote = dbRepo.createCopyFromNote(sourceNoteDbId, newParentDbId)

            values[0] = copiedNote.id
            values[7] = copiedNote.created
            values[8] = copiedNote.last_updated

        # If item is toggled, check if the toggled status can be allowed in the new treestore destination
        # Note: by definition there won't be any conflict between the toggled items in the d&d rows (all the appropriate checks have been executed when the items where originally toggled).
        # So either all the toggled items are allowed or all are to be rejected.
        if values[1] == True:
            if toggledStatusAvailable:
                # Leave the toggled status True
                # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the recursivePathDbIdList item has to be updated. Either case the code is the same.
                recursiveDbIdPath = dbRepo.findRecursivePathByDbId(values[0])
                recursivePathDbIdList = [subdict["id"] for subdict in recursiveDbIdPath]
                toggledRowsDict[values[0]] = recursivePathDbIdList
            else:
                # Disable the toggled state
                values[1] = False
                # If new item is copied, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                if move_flag:
                    toggledRowsDict.pop(values[0])

        copied_iter = treestore.append(to_parent, values)
        if treestore.iter_has_child(iter):
            moveChildRows(treestore, iter, copied_iter, move_flag, toggledRowsDict, toggledStatusAvailable)
        # The following two lines seem to be unnecessary
        # if move_flag:
            # treestore.remove(iter)
        counter += 1
        iter = treestore.iter_next(iter)

    if debug:
        print("Number of children copied: " + str(counter))

    return

def dragDataReceived(treeview, context, x, y, selection, info, etime, defer_select, orderByColumn, orderAsc, resultsPageNum, resultsPerPage, displayToggledOnlyModeOn = False, displaySearchTermModeOn = False, toggledRowsDict = dict(), searchTerm = ''):

    #NOTE: Turn DFEBUG mode on or off
    debug = False

    model = treeview.get_model()
    n_columns = model.get_n_columns()
    pathlist = json.loads(selection.get_data().decode("utf-8"))
    #print("Pathlist" + str(pathlist))
    drop_info = treeview.get_dest_row_at_pos(x, y)

    movedItemsDbIdList = []

    if drop_info:
        drop_path, position = drop_info
        drop_path_ref = Gtk.TreeRowReference.new(model, drop_path)
        drop_iter_or = model.get_iter(drop_path)
        
        #drop_path_upd = drop_path_ref.get_path()
        #dest_path = str(drop_path_upd)
        #iter = model.get_iter(drop_path_upd)

    for source_path in pathlist:
        #convert source_path from string to Gtk.Path instance
        source_path = Gtk.TreePath(source_path.split(":"))
        source_iter = model.get_iter(source_path)

        if drop_info:
            if str(source_path) == str(drop_path):
                if debug:
                    print("Alert: dropping on one of the selected elements. Drag & drop aborted")
                defer_select = exitDndUndoSelection(treeview, defer_select)
                return {"defer_select": defer_select, "balance": 0, "movedItemsDbIdList": movedItemsDbIdList}

            #Note: is_ancestor(iter, descendant) returns True if iter is ancestor of descendant. Equals = you can't d&d a parent item on any of its children
            if model.is_ancestor(source_iter, drop_iter_or):
                if debug:
                    print("Alert: one of the selected elements is a parent of the drop destination item. Drag & drop aborted")
                defer_select = exitDndUndoSelection(treeview, defer_select)
                return {"defer_select": defer_select, "balance": 0, "movedItemsDbIdList": movedItemsDbIdList}

        # If orderByColumn is different than customOrder, then Drag & drop (with move context) inside the same parent should be stopped (because it would be a simple rearrangment of the customOrder params with no clear intention from the user)
        if orderByColumn != 0:
            if context.get_actions() == Gdk.DragAction.MOVE:
                if drop_info and (position == Gtk.TreeViewDropPosition.BEFORE or position == Gtk.TreeViewDropPosition.AFTER) and haveSameParent(source_path, drop_path):
                    if debug:
                        print("Alert: moving element inside the same parent with orderByColumn different than customOrder. Drag & drop aborted")
                    defer_select = exitDndUndoSelection(treeview, defer_select)
                    return {"defer_select": defer_select, "balance": 0, "movedItemsDbIdList": movedItemsDbIdList}

                elif not drop_info and len(source_path) == 1:
                    if debug:
                        print("Alert: moving element inside the same parent with orderByColumn different than customOrder. Drag & drop aborted")
                    defer_select = exitDndUndoSelection(treeview, defer_select)
                    return {"defer_select": defer_select, "balance": 0, "movedItemsDbIdList": movedItemsDbIdList}
                else:
                    pass
    
    source_path_ref_list = []
    for source_path in pathlist:
        #convert source_path from string to Gtk.Path instance
        source_path = Gtk.TreePath(source_path.split(":"))

        new_row_reference = Gtk.TreeRowReference.new(model, source_path)
        source_path_ref_list.append(new_row_reference)

    #print("Ref list length: " + str(len(source_path_ref_list)))

    # Check 1 - Check if the current item is the parent of an already-toggled item - This condition can never happen in a d&d context
    # Check 2 - Check if one of the parents of the drop_item is already toggled - By definition this is only useful for non-root items.
    # The recursivePathDbIdList created now will contain only all the parents items of the d&d items; remember to add the d&d item dbId to the list before saving it in the toggledRowsDict dictionary.
    if drop_info:
        dropIterParentIter = model.iter_parent(drop_iter_or)
        if not dropIterParentIter and (position == Gtk.TreeViewDropPosition.BEFORE or position == Gtk.TreeViewDropPosition.AFTER):
            recursivePathDbIdList = []
            toggledStatusAvailable = True
        elif not dropIterParentIter and (position != Gtk.TreeViewDropPosition.BEFORE and position != Gtk.TreeViewDropPosition.AFTER):
            recursivePathDbIdList = [model[drop_iter_or][0]]
            if not model[drop_iter_or][1]:
                toggledStatusAvailable = True
            else:
                toggledStatusAvailable = False
        else:
            if position == Gtk.TreeViewDropPosition.BEFORE or position == Gtk.TreeViewDropPosition.AFTER:
                recursiveDbIdPath = dbRepo.findRecursivePathByDbId(model[dropIterParentIter][0])
            else:
                recursiveDbIdPath = dbRepo.findRecursivePathByDbId(model[drop_iter_or][0])

            recursivePathDbIdList = [subdict["id"] for subdict in recursiveDbIdPath]

            if len(toggledRowsDict) > 0:
                if not set(recursivePathDbIdList) & set(toggledRowsDict.keys()):
                    toggledStatusAvailable = True
                else:
                    toggledStatusAvailable = False
            else:
                toggledStatusAvailable = True
    else:
        recursivePathDbIdList = []
        toggledStatusAvailable = True

    rootItemsNetBalance = 0

    # If treeview rows are ordered by customOrder
    if orderByColumn == 0:

        if drop_info and position == Gtk.TreeViewDropPosition.AFTER:
            #reverse items order
            source_path_ref_list.reverse()

        for source_path_ref in source_path_ref_list:
            #convert source_path from string to Gtk.Path instance
            source_path_upd = source_path_ref.get_path()
            source_iter_upd = model.get_iter(source_path_upd)
            sourceIterUpdParentIter = model.iter_parent(source_iter_upd)
            if (sourceIterUpdParentIter):
                sourceItemIsRootItem = False
            else:
                sourceItemIsRootItem = True
            values = model.get(source_iter_upd, *range(n_columns))
            values = list(values)
            sourceNoteDbId = values[0]
            # sourceNote = dbRepo.findNoteByDbId(sourceNoteDbId)
            # print("Copying values: " + str(values))

            if drop_info:
                drop_path_upd = drop_path_ref.get_path()
                drop_iter_upd = model.get_iter(drop_path_upd)
                refNoteCustomOrder = model[drop_iter_upd][4]
                refNoteNum = model[drop_iter_upd][5]
                refNoteDenom = model[drop_iter_upd][6]
                dropIterUpdParentIter = model.iter_parent(drop_iter_upd)
                if(dropIterUpdParentIter):
                    newParentId = model[dropIterUpdParentIter][0]
                else:
                    newParentId = None

                # If displayToggledOnlyModeOn, moving (not copying) root items before/after another root item should do nothing (otherwise the only effect would be changing the custom_order of  the moved root item to that of the lastRootItem)
                if displayToggledOnlyModeOn and context.get_actions() == Gdk.DragAction.MOVE and (position == Gtk.TreeViewDropPosition.BEFORE or position == Gtk.TreeViewDropPosition.AFTER) and sourceItemIsRootItem and not newParentId:
                    continue

                if position == Gtk.TreeViewDropPosition.BEFORE:
                    if debug:
                        print("Insert BEFORE Ref node: id = " + str(model[drop_iter_upd][0]) + " - custom order: " + str(model[drop_iter_upd][4]))

                    if(model.iter_previous(drop_iter_upd)):
                        # iter_previous is not None. Simple drag and drop between two rows in treeview

                        # If displayOnlyToggledOn, check if we are at root level; if so, add as new last root item
                        if displayToggledOnlyModeOn and not newParentId:
                            orderParams = dbRepo.findOrderParamForLastRootItem()
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                        else:
                            prevNoteIter = model.iter_previous(drop_iter_upd)
                            prevNoteDbId = model[prevNoteIter][0]
                            orderParams = dbRepo.findOrderParamsBetweenTwoNotes(prevNoteDbId, refNoteNum, refNoteDenom)
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                    else:
                        if newParentId:
                            # iter_previous is None because ref_iter is already the first child of a parent
                            orderParams = dbRepo.findOrderParamForFirstSibling(newParentId)
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                        else:
                            # iter_previous is None because ref_iter is first root item

                            # If displayOnlyToggledOn then add as new last root item
                            if displayToggledOnlyModeOn:
                                orderParams = dbRepo.findOrderParamForLastRootItem()
                                num = orderParams["num"]
                                denom = orderParams["denom"]

                            # Default display mode
                            else:

                                if resultsPageNum == 1:
                                    # PageNum = 1 so we are creating a real new first root item
                                    orderParams = dbRepo.findOrderParamForFirstRootItem()
                                    num = orderParams["num"]
                                    denom = orderParams["denom"]

                                else:
                                    # PageNum != 1 so fetch from db (where parent == None & custom_order < refNote custom_order, limit 1)
                                    prevNoteDbId = dbRepo.findPreviousNoteDbIdByCustomOrder(refNoteCustomOrder)
                                    orderParams = dbRepo.findOrderParamsBetweenTwoNotes(prevNoteDbId, refNoteNum, refNoteDenom)
                                    num = orderParams["num"]
                                    denom = orderParams["denom"]

                    # Update the sqlite db
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        # Update existing db record
                        newNote = dbRepo.updateNoteAfterDrag(sourceNoteDbId, newParentId, num / denom, num, denom)
                    else:
                        # Create new db record from existing one
                        newNote = dbRepo.createNewFromNote(sourceNoteDbId, newParentId, num / denom, num, denom)

                    # Update the values array before inserting a new record in the treemodel
                    values[4] = newNote.custom_order
                    values[5] = newNote.fraction_num
                    values[6] = newNote.fraction_denom
                    if context.get_actions() != Gdk.DragAction.MOVE:
                        values[0] = newNote.id
                        values[7] = newNote.created
                        values[8] = newNote.last_updated

                    if values[1] == True:
                        if toggledStatusAvailable:
                            # Leave the item toggled and update the toggledRowsDict
                            # Add the current item dbId to the recursivePathDbIdList
                            recursivePathDbIdList = recursivePathDbIdList.insert(0, values[0])
                            # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the rootParent item has to be updated. Either case the code is the same.
                            toggledRowsDict[values[0]] = recursivePathDbIdList
                        else:
                            # Remove the toggled status and update the toggledRowsDict accordingly
                            values[1] = False
                            # If new item is a copy, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                            if context.get_actions() == Gdk.DragAction.MOVE:
                                toggledRowsDict.pop(values[0])

                    new_node_iter = model.insert_before(None, drop_iter_upd, values)

                elif position == Gtk.TreeViewDropPosition.AFTER:
                    if debug:
                        print("Insert AFTER Ref node: id = " + str(model[drop_iter_upd][0]) + " - custom order: " + str(model[drop_iter_upd][4]))

                    if (model.iter_next(drop_iter_upd)):
                        # iter_next is not None. Simple drag and drop between two rows in treeview

                        # If displayOnlyToggledOn, check if we are at root level; if so, add as new last root item
                        if displayToggledOnlyModeOn and not newParentId:
                            orderParams = dbRepo.findOrderParamForLastRootItem()
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                        else:
                            nextNoteIter = model.iter_next(drop_iter_upd)
                            nextNoteDbId = model[nextNoteIter][0]
                            orderParams = dbRepo.findOrderParamsBetweenTwoNotes(nextNoteDbId, refNoteNum, refNoteDenom)
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                    else:
                        if newParentId:
                            # iter_next is None because ref_iter is already the last child of a parent
                            orderParams = dbRepo.findOrderParamForLastSibling(newParentId)
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                        else:
                            # iter_next is None because ref_iter is last root item

                            # If displayOnlyToggledOn then add as new last root item
                            if displayToggledOnlyModeOn:
                                orderParams = dbRepo.findOrderParamForLastRootItem()
                                num = orderParams["num"]
                                denom = orderParams["denom"]

                            # Default display mode
                            else:
                                lastResultsPageNum = dbRepo.findLastResultsPageNum(resultsPerPage, displayToggledOnlyModeOn, displaySearchTermModeOn, toggledRowsDict, searchTerm)

                                if resultsPageNum == lastResultsPageNum:
                                    # PageNum = last_results_page so we are creating a real new last root item
                                    orderParams = dbRepo.findOrderParamForLastRootItem()
                                    num = orderParams["num"]
                                    denom = orderParams["denom"]

                                else:
                                    # PageNum != last_results_page so fetch from db (where parent == None & custom_order > refNote custom_order, limit 1)
                                    nextNoteDbId = dbRepo.findNextNoteDbIdByCustomOrder(refNoteCustomOrder)
                                    orderParams = dbRepo.findOrderParamsBetweenTwoNotes(nextNoteDbId, refNoteNum, refNoteDenom)
                                    num = orderParams["num"]
                                    denom = orderParams["denom"]

                    # Update the sqlite db
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        # Update existing db record
                        newNote = dbRepo.updateNoteAfterDrag(sourceNoteDbId, newParentId, num / denom, num, denom)
                    else:
                        # Create new db record from existing one
                        newNote = dbRepo.createNewFromNote(sourceNoteDbId, newParentId, num / denom, num, denom)

                    # Update the values array before inserting a new record in the treemodel
                    values[4] = newNote.custom_order
                    values[5] = newNote.fraction_num
                    values[6] = newNote.fraction_denom
                    if context.get_actions() != Gdk.DragAction.MOVE:
                        values[0] = newNote.id
                        values[7] = newNote.created
                        values[8] = newNote.last_updated

                    if values[1] == True:
                        if toggledStatusAvailable:
                            # Leave the item toggled and update the toggledRowsDict
                            # Add the current item dbId to the recursivePathDbIdList
                            recursivePathDbIdList = recursivePathDbIdList.insert(0, values[0])
                            # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the rootParent item has to be updated. Either case the code is the same.
                            toggledRowsDict[values[0]] = recursivePathDbIdList
                        else:
                            # Remove the toggled status and update the toggledRowsDict accordingly
                            values[1] = False
                            # If new item is a copy, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                            if context.get_actions() == Gdk.DragAction.MOVE:
                                toggledRowsDict.pop(values[0])

                    new_node_iter = model.insert_after(None, drop_iter_upd, values)

                else:
                    # Dropping over a row = add as a child (last sibling)
                    dropIterUpdDbId = model[drop_iter_upd][0]
                    newParentId = dropIterUpdDbId
                    orderParams = dbRepo.findOrderParamForLastSibling(newParentId)
                    num = orderParams["num"]
                    denom = orderParams["denom"]

                    # Update the sqlite db
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        # Update existing db record
                        newNote = dbRepo.updateNoteAfterDrag(sourceNoteDbId, newParentId, num / denom, num, denom)
                    else:
                        # Create new db record from existing one
                        newNote = dbRepo.createNewFromNote(sourceNoteDbId, newParentId, num / denom, num, denom)

                    # Update the values array before inserting a new record in the treemodel
                    values[4] = newNote.custom_order
                    values[5] = newNote.fraction_num
                    values[6] = newNote.fraction_denom
                    if context.get_actions() != Gdk.DragAction.MOVE:
                        values[0] = newNote.id
                        values[7] = newNote.created
                        values[8] = newNote.last_updated

                    if values[1] == True:
                        if toggledStatusAvailable:
                            # Leave the item toggled and update the toggledRowsDict
                            # Add the current item dbId to the recursivePathDbIdList
                            recursivePathDbIdList = recursivePathDbIdList.insert(0, values[0])
                            # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the rootParent item has to be updated. Either case the code is the same.
                            toggledRowsDict[values[0]] = recursivePathDbIdList
                        else:
                            # Remove the toggled status and update the toggledRowsDict accordingly
                            values[1] = False
                            # If new item is a copy, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                            if context.get_actions() == Gdk.DragAction.MOVE:
                                toggledRowsDict.pop(values[0])

                    new_node_iter = model.append(drop_iter_upd, values)

                if not newParentId:
                    rootItemsNetBalance += 1
                    if debug:
                        print("rootItemsNetBalance + 1")

                #if dragging a SUBTREE
                if(model.iter_has_child(source_iter_upd)):
                    if debug:
                        print("Creating subtree children")
                    #create children
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        move_flag = True
                    else:
                        move_flag = False
                    moveChildRows(model, source_iter_upd, new_node_iter, move_flag, toggledRowsDict, toggledStatusAvailable)

            else:
                if debug:
                    print("Appending new value")
                last_root_item_num = len(model)-1
                if (len(source_path_upd) == 1 and int(str(source_path_upd)) == last_root_item_num and context.get_actions() == Gdk.DragAction.MOVE):
                    if debug:
                        print("Moved element is already in last position of root level. No action taken.")
                    # The following two lines should NOT be needed because we aren't managing a single item but we are inside a for loop. So, simply skip the item
                    # defer_select = exitDndUndoSelection(treeview, defer_select)
                    # return {"defer_select": defer_select, "balance": 0, "movedItemsDbIdList": movedItemsDbIdList}

                    # Remove source_path_ref from the source_path_ref_list
                    source_path_ref_list.remove(source_path_ref)

                else:
                    # If displayOnlyToggledOn then add as new last root item
                    if displayToggledOnlyModeOn:
                        orderParams = dbRepo.findOrderParamForLastRootItem()
                        num = orderParams["num"]
                        denom = orderParams["denom"]

                    # Default display mode
                    else:
                        lastResultsPageNum = dbRepo.findLastResultsPageNum(resultsPerPage, displayToggledOnlyModeOn, displaySearchTermModeOn, toggledRowsDict, searchTerm)

                        if resultsPageNum == lastResultsPageNum:
                            # PageNum = last_results_page so we are creating a real new last root item
                            orderParams = dbRepo.findOrderParamForLastRootItem()
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                        else:
                            # PageNum != last_results_page so fetch from db (where parent == None & custom_order > "currentPage lastNote custom_order", limit 1)
                            lastRowPath = Gtk.TreePath([last_root_item_num])
                            lastRowIter = model.get_iter(lastRowPath)
                            refNoteCustomOrder = model[lastRowIter][4]
                            refNoteNum = model[lastRowIter][5]
                            refNoteDenom = model[lastRowIter][6]
                            nextNoteDbId = dbRepo.findNextNoteDbIdByCustomOrder(refNoteCustomOrder)
                            orderParams = dbRepo.findOrderParamsBetweenTwoNotes(nextNoteDbId, refNoteNum, refNoteDenom)
                            num = orderParams["num"]
                            denom = orderParams["denom"]

                    # Update the sqlite db
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        # Update existing db record
                        newNote = dbRepo.updateNoteAfterDrag(sourceNoteDbId, None, num / denom, num, denom)
                    else:
                        # Create new db record from existing one
                        newNote = dbRepo.createNewFromNote(sourceNoteDbId, None, num / denom, num, denom)

                    # Update the values array before inserting a new record in the treemodel
                    values[4] = newNote.custom_order
                    values[5] = newNote.fraction_num
                    values[6] = newNote.fraction_denom
                    if context.get_actions() != Gdk.DragAction.MOVE:
                        values[0] = newNote.id
                        values[7] = newNote.created
                        values[8] = newNote.last_updated

                    if values[1] == True:
                        if toggledStatusAvailable:
                            # Leave the item toggled and update the toggledRowsDict
                            # Add the current item dbId to the recursivePathDbIdList
                            recursivePathDbIdList = recursivePathDbIdList.insert(0, values[0])
                            # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the rootParent item has to be updated. Either case the code is the same.
                            toggledRowsDict[values[0]] = recursivePathDbIdList
                        else:
                            # Remove the toggled status and update the toggledRowsDict accordingly
                            values[1] = False
                            # If new item is a copy, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                            if context.get_actions() == Gdk.DragAction.MOVE:
                                toggledRowsDict.pop(values[0])

                    new_node_iter = model.append(None, values)

                    rootItemsNetBalance += 1
                    if debug:
                        print("rootItemsNetBalance + 1")

                    # print("New row was appended: lenght of model is " + str(len(model)))
                    if(model.iter_has_child(source_iter_upd)):
                        #create children
                        if context.get_actions() == Gdk.DragAction.MOVE:
                            move_flag = True
                        else:
                            move_flag = False
                        moveChildRows(model, source_iter_upd, new_node_iter, move_flag, toggledRowsDict, toggledStatusAvailable)

        #NOTE: Freeing references may not be necessary since rows get eliminated

    # --------------------------------------------------------------

    else: # = If treeview rows are NOT ordered by customOrder (anything else is fine)

        # All cases should behave like "Append to the end"
        # By default the parent of the newly appended item should be the same parent of the dropIter.
        # The only exception is if you drop an item onto another item (position = None); in that case the parent of the newly appended item should be the dropIter itself.
        if drop_info:
            drop_path_upd = drop_path_ref.get_path()
            drop_iter_upd = model.get_iter(drop_path_upd)

            if position != Gtk.TreeViewDropPosition.BEFORE and position != Gtk.TreeViewDropPosition.AFTER:
                newParentId = model[drop_iter_upd][0]

            else:
                dropIterUpdParentIter = model.iter_parent(drop_iter_upd)
                if (dropIterUpdParentIter):
                    newParentId = model[dropIterUpdParentIter][0]
                    drop_iter_upd = dropIterUpdParentIter
                else:
                    newParentId = None

        else:
            newParentId = None

        # Now append as last element of either root level or N-level (only two cases)

        for source_path_ref in source_path_ref_list:
            source_path_upd = source_path_ref.get_path()
            source_iter_upd = model.get_iter(source_path_upd)
            values = model.get(source_iter_upd, *range(n_columns))
            values = list(values)
            sourceNoteDbId = values[0]

            if newParentId:
                orderParams = dbRepo.findOrderParamForLastSibling(newParentId)
                num = orderParams["num"]
                denom = orderParams["denom"]

            else:
                orderParams = dbRepo.findOrderParamForLastRootItem()
                num = orderParams["num"]
                denom = orderParams["denom"]

            # Update the sqlite db
            if context.get_actions() == Gdk.DragAction.MOVE:
                # Update existing db record
                newNote = dbRepo.updateNoteAfterDrag(sourceNoteDbId, newParentId, num / denom, num, denom)
            else:
                # Create new db record from existing one
                newNote = dbRepo.createNewFromNote(sourceNoteDbId, newParentId, num / denom, num, denom)

            # Update the values array before inserting a new record in the treemodel
            values[4] = newNote.custom_order
            values[5] = newNote.fraction_num
            values[6] = newNote.fraction_denom
            if context.get_actions() != Gdk.DragAction.MOVE:
                values[0] = newNote.id
                values[7] = newNote.created
                values[8] = newNote.last_updated

            if values[1] == True:
                if toggledStatusAvailable:
                    # Leave the item toggled and update the toggledRowsDict
                    # Add the current item dbId to the recursivePathDbIdList
                    recursivePathDbIdList = recursivePathDbIdList.insert(0, values[0])
                    # If the item is copied than a new entry has to be added to the toggledRowsDict with its new dbId; if it is moved the rootParent item has to be updated. Either case the code is the same.
                    toggledRowsDict[values[0]] = recursivePathDbIdList
                else:
                    # Disable the toggled state
                    values[1] = False
                    # If new item is a copy, do nothing; otherwise remove entry from the toggledRowsDict dictionary
                    if context.get_actions() == Gdk.DragAction.MOVE:
                        toggledRowsDict.pop(values[0])

            if newParentId:
                new_node_iter = model.append(drop_iter_upd, values)
            else:
                new_node_iter = model.append(None, values)

            if not newParentId:
                rootItemsNetBalance += 1
                if debug:
                    print("rootItemsNetBalance + 1")

            # if dragging a SUBTREE
            if (model.iter_has_child(source_iter_upd)):
                if debug:
                    print("Creating subtree children")
                # create children
                if context.get_actions() == Gdk.DragAction.MOVE:
                    move_flag = True
                else:
                    move_flag = False
                moveChildRows(model, source_iter_upd, new_node_iter, move_flag, toggledRowsDict, toggledStatusAvailable)


    #THIS CODE SHOULD BE EXECUTED INDEPENDENTLY FROM THE orderByColumn VALUE
    
    if context.get_actions() == Gdk.DragAction.MOVE and len(source_path_ref_list) > 0:
        for source_path_ref in source_path_ref_list:
            if source_path_ref.valid():
                source_iter_upd = model.get_iter(source_path_ref.get_path())
                # Add item's dbId to the movedItemsDbIdList - This will be useful to (eventually) update the Path displayed in the CustomNotebookTab's revealer section of any opened notes whose parent has been d&d
                movedItemsDbIdList.append(model[source_iter_upd][0])
                # Check if a root element was removed
                if len(str(source_path_ref.get_path())) == 1:
                    rootItemsNetBalance -= 1
                    if debug:
                        print("rootItemsNetBalance - 1")
                #source_path_ref.free()
                model.remove(source_iter_upd)
                if source_path_ref.valid():
                    source_path_ref.get_path().free()

        #context.finish(True, True, etime)

    # Remove extra treeview rows (if num_rows > resultsPerPage)
    if (len(model) > resultsPerPage):
        for x in range(len(model) - 1, resultsPerPage - 1, -1):
            rowPath = Gtk.TreePath([x])
            rowIter = model.get_iter(rowPath)
            model.remove(rowIter)

    # Add rows if len of model < resultsPerPage
    if (len(model) < resultsPerPage):
        diffNum = resultsPerPage - len(model)
        lastRootItemNum = len(model)-1
        lastRootItemPath = Gtk.TreePath([lastRootItemNum])
        lastRootItemIter = model.get_iter(lastRootItemPath)
        lastRootItemDbId = model[lastRootItemIter][0]
        dbRepo.populateTreestore(model, dbRepo.findNextResults(orderByColumn, orderAsc, lastRootItemDbId, diffNum, displayToggledOnlyModeOn, displaySearchTermModeOn, toggledRowsDict, searchTerm), toggledRowsDict)
    
    if defer_select is not False:
        treeview.get_selection().set_select_function(rowSelectionFunction, None)
        defer_select=False

    #Unselect all rows
    treeview.get_selection().unselect_all()

    if debug:
        print("Total rootItemsNetBalance: " + str(rootItemsNetBalance))

    return {"defer_select": defer_select, "balance": rootItemsNetBalance, "movedItemsDbIdList": movedItemsDbIdList}


def onButtonPress(widget, event, treeview, defer_select):
    debug = False
    if debug:
        print(datetime.datetime.now().strftime("%H:%M:%S") + " Button pressed event triggered")
    # Here we intercept mouse clicks on selected items so that we can
    # drag multiple items without the click selecting only one
    target = treeview.get_path_at_pos(int(event.x), int(event.y))
    if (target
        and event.type == Gdk.EventType.BUTTON_PRESS
        and not (event.state & (Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK))
        and target[1].get_title() != 'Toggle'
        and treeview.get_selection().path_is_selected(target[0])):
            # disable selection
            # print("Selection function will be temporarily disabled")
            treeview.get_selection().set_select_function(lambda *ignore: False)
            defer_select = target[0]

    return defer_select
		
def onButtonRelease(widget, event, treeview, defer_select):
    debug = False
    if debug:
        print(datetime.datetime.now().strftime("%H:%M:%S") + " Button released event triggered")

    target = treeview.get_path_at_pos(int(event.x), int(event.y))
    if (defer_select # and target
        # and defer_select == target[0]
        and not (event.x==0 and event.y==0)): # certain drag and drop
            # print("Selection function re-enabled")
            treeview.get_selection().set_select_function(rowSelectionFunction, None)  # (lambda *ignore: True)
            if target:
                treeview.set_cursor(target[0], None, False) # treeview.set_cursor(target[0], target[1], False) if you want to focus a specific column (like target[1])

    defer_select = False

    return defer_select

def getParentPathAsString(treePath):
    treePathString = str(treePath)

    if len(treePathString) >= 3:
        parentTreePathString = treePathString[0:-2]
    else:
        parentTreePathString = None

    return parentTreePathString


def haveSameParent(sourcePath, dropPath):
        if getParentPathAsString(sourcePath) == getParentPathAsString(dropPath):
            return True
        else:
            return False

def exitDndUndoSelection(treeview, defer_select):
    #Set defer_select value
    if defer_select is not False:
        treeview.get_selection().set_select_function(rowSelectionFunction, None)
        defer_select = False

    #Unselect all rows
    treeview.get_selection().unselect_all()

    return defer_select