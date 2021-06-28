from peewee import *
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GtkSource
import math
import datetime
import sternBrocotGr as sternBrocot
import json
import collections

db = SqliteDatabase(None)

class BaseModel(Model):
    class Meta:
        database = db

class Note(BaseModel):
    title = CharField()
    description = CharField()
    content = TextField()
    parent = ForeignKeyField('self', backref='children', null=True, on_delete='CASCADE')
    custom_order = FloatField()
    fraction_num = IntegerField()
    fraction_denom = IntegerField(default=1)
    created = DateTimeField(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_updated = DateTimeField(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class Snippet(BaseModel):
    title = CharField()
    code = TextField()
    owner = ForeignKeyField(Note, backref='snippets', on_delete='CASCADE')

# db.connect()

def createNewFromNote(sourceNoteDbId, newParentId, newCustomOrder, newNum, newDenom):
    sourceNote = findNoteByDbId(sourceNoteDbId)
    newNote = Note.create(title=sourceNote.title, description=sourceNote.description, content=sourceNote.content, parent=newParentId, custom_order=newCustomOrder, fraction_num=newNum, fraction_denom=newDenom)
    return newNote

def createCopyFromNote(sourceNoteDbId, newParentDbId):
    sourceNote = findNoteByDbId(sourceNoteDbId)
    newNote = Note.create(title=sourceNote.title, description=sourceNote.description, content=sourceNote.content, parent=newParentDbId, custom_order=sourceNote.custom_order, fraction_num=sourceNote.fraction_num, fraction_denom=sourceNote.fraction_denom)
    return newNote

def updateNoteAfterDrag(sourceNoteDbId, newParentId, newCustomOrder, newNum, newDenom):
    sourceNote = findNoteByDbId(sourceNoteDbId)
    sourceNote.parent = newParentId
    sourceNote.custom_order = newCustomOrder
    sourceNote.fraction_num = newNum
    sourceNote.fraction_denom = newDenom
    sourceNote.save()
    return sourceNote

def findOrderParamForFirstSibling(parentDbId):
    query = Note.select().where(Note.parent == parentDbId).order_by(Note.custom_order).limit(1)
    firstSibling = query[0]
    custom_order = firstSibling.custom_order
    if (custom_order > 1):
        if custom_order.is_integer():
            num = custom_order - 1
        else:
            num = math.floor(firstSibling.custom_order)

        denom = 1

    else:
        sternBrocotRoot = sternBrocot.SBNode()
        trg_frac = (firstSibling.fraction_num, firstSibling.fraction_denom)
        insert_after = False
        new_frac = sternBrocotRoot.find_next_fraction(trg_frac, insert_after)
        num = new_frac[0]
        denom = new_frac[1]

    return {"num": num, "denom": denom}

def findOrderParamForLastSibling(parentDbId):
    query = Note.select().where(Note.parent == parentDbId).order_by(Note.custom_order.desc()).limit(1)
    if(query.count() != 0):
        lastSibling = query[0]
        custom_order = lastSibling.custom_order
        newNoteCustomOrder = math.ceil(custom_order) + 1
        return {"num": newNoteCustomOrder, "denom": 1}

    else:
        return {"num": 1, "denom": 1}

def findLastResultsPageNum(resultsPerPage, displayToggledOnlyModeOn = False, displaySearchTermModeOn = False, toggledRowsDict = dict(), searchTerm = ''):
    if displayToggledOnlyModeOn:
        totalNotesNum = len(toggledRowsDict)
    elif displaySearchTermModeOn:
        totalNotesNum = Note.select().where(Note.title.contains(searchTerm)).count()
    else:
        totalNotesNum = Note.select().where(Note.parent == None).count()
    lastResultsPageNum = math.ceil(totalNotesNum / resultsPerPage)
    return lastResultsPageNum

def findOrderParamForLastRootItem():
    query = Note.select().where(Note.parent == None).order_by(Note.custom_order.desc()).limit(1)
    lastRootItem = query[0]
    newNoteCustomIndex = math.ceil(lastRootItem.custom_order) + 1
    return {"num": newNoteCustomIndex, "denom": 1}

def findOrderParamForFirstRootItem():
    query = Note.select().where(Note.parent == None).order_by(Note.custom_order).limit(1)
    firstRootItem = query[0]
    custom_order = firstRootItem.custom_order
    if (custom_order > 1):
        if custom_order.is_integer():
            num = custom_order - 1
        else:
            num = math.floor(firstRootItem.custom_order)

        denom = 1

    else:
        sternBrocotRoot = sternBrocot.SBNode()
        trg_frac = (firstRootItem.fraction_num, firstRootItem.fraction_denom)
        insert_after = False
        new_frac = sternBrocotRoot.find_next_fraction(trg_frac, insert_after)
        num = new_frac[0]
        denom = new_frac[1]

    return {"num": num, "denom": denom}

def findPreviousNoteDbIdByCustomOrder(refNoteCustomOrder):
    query = Note.select().where((Note.parent == None) & (Note.custom_order < refNoteCustomOrder)).order_by(Note.custom_order.desc()).limit(1)
    previousNote = query[0]
    return previousNote.id

def findNextNoteDbIdByCustomOrder(refNoteCustomOrder):
    query = Note.select().where((Note.parent == None) & (Note.custom_order > refNoteCustomOrder)).order_by(Note.custom_order).limit(1)
    nextNote = query[0]
    return nextNote.id

def findOrderParamsBetweenTwoNotes(NoteDbId,refNoteNum,refNoteDenom):
    # This function will work for both insert_before AND insert_after scenarios, by checking if noteDb custom_order is > or < than refNote custom_order
    noteDb = findNoteByDbId(NoteDbId)
    noteDbNum = noteDb.fraction_num
    noteDbDenom = noteDb.fraction_denom

    sternBrocotRoot = sternBrocot.SBNode()
    if(noteDbNum/noteDbDenom < refNoteNum/refNoteDenom):
        # insert_before scenario
        lower_frac = (noteDbNum, noteDbDenom)
        upper_frac = (refNoteNum, refNoteDenom)
    else:
        lower_frac = (refNoteNum, refNoteDenom)
        upper_frac = (noteDbNum, noteDbDenom)

    new_frac = sternBrocotRoot.find_intermediate_fraction(lower_frac, upper_frac)
    num = new_frac[0]
    denom = new_frac[1]

    return {"num": num, "denom": denom}

def findNextResults(orderByColumn, orderAsc, lastItemDbId, limit, displayToggledOnlyModeOn = False, displaySearchTermModeOn = False, toggledRowsDict = dict(), searchTerm = ''):
    # Retrieving rows to append to trevieew after drag & drop changes
    # Note: orderByColumn 0 = customOrder, 1 = title, 2 = created, 3 = lastUpdated

    if orderByColumn == 0:
        columnX = Note.custom_order
    elif orderByColumn == 1:
        columnX = fn.Lower(Note.title)
    elif orderByColumn == 2:
        columnX = Note.created
    elif orderByColumn == 3:
        columnX = Note.last_updated
    else:
        columnX = Note.custom_order

    lastTreeviewItemColumnXValue = Note.select(columnX).where(Note.id == lastItemDbId)

    # # Displaying user search results by searchTerm
    # elif displaySearchTermModeOn:
    #     if orderByColumn == 0:
    #         parentsIdList = Note.select(Note.id).where(Note.title.contains(searchTerm)).offset(offset).limit(limit)
    #     else:
    #         parentsIdList = Note.select(Note.id).where(Note.title.contains(searchTerm)).order_by(orderByColumnPeewee).offset(offset).limit(limit)

    if displayToggledOnlyModeOn:
        custom_order_case = Case(Note.parent.is_null(), [(True, Note.custom_order)], 1)
        if orderAsc == True:
            queryDictList = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.id.in_(list(toggledRowsDict.keys()))) & ((columnX > lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id > lastItemDbId)))).order_by(columnX, Note.id).limit(limit).dicts()
            parentsIdList = [dictItem['id'] for dictItem in queryDictList]
        else:
            queryDictList = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.id.in_(list(toggledRowsDict.keys()))) & ((columnX < lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id < lastItemDbId)))).order_by(columnX.desc(), Note.id.desc()).limit(limit).dicts()
            parentsIdList = [dictItem['id'] for dictItem in queryDictList]
    elif displaySearchTermModeOn:
        custom_order_case = Case(Note.parent.is_null(), [(True, Note.custom_order)], 1)
        if orderAsc == True:
            queryDictList = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.title.contains(searchTerm)) & ((columnX > lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id > lastItemDbId)))).order_by(columnX, Note.id).limit(limit).dicts()
            parentsIdList = [dictItem['id'] for dictItem in queryDictList]
        else:
            queryDictList = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.title.contains(searchTerm)) & ((columnX < lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id < lastItemDbId)))).order_by(columnX.desc(), Note.id.desc()).limit(limit).dicts()
            parentsIdList = [dictItem['id'] for dictItem in queryDictList]
    else:
        if orderAsc == True:
            parentsIdList = Note.select(Note.id).where((Note.parent.is_null()) & ((columnX > lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id > lastItemDbId)))).order_by(columnX, Note.id).limit(limit)
        else:
            parentsIdList = Note.select(Note.id).where((Note.parent.is_null()) & ((columnX < lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id < lastItemDbId)))).order_by(columnX.desc(), Note.id.desc()).limit(limit)

    # Direct SQLite query: SELECT Note.id, Note.title FROM Note WHERE (Note.parent_id IS NULL and LOWER(Note.title) <= 'benjamin') ORDER BY Note.title DESC LIMIT 2

    return retrieveAllFromIdList(orderByColumn, orderAsc, parentsIdList, displayToggledOnlyModeOn, displaySearchTermModeOn)

    # This method should work BUT uses SQLite "Window Function" RANK() which is available only since version 3.25.
    # targetId = 5 # Note: Change this value based on db data (it's just a random example)
    # noteAlias = Note.alias()
    # subquery = (noteAlias.select(noteAlias.id, fn.RANK().over(partition_by=[noteAlias.title], order_by=[noteAlias.title]).alias('rank')).where(noteAlias.parent.is_null()).alias('subq')) # Should work even withour partition_by param
    # query = (Note.select(subquery.c.id, subquery.c.rank).from_(subquery).where(subquery.c.id == targetId))
    # item = query[0]
    # itemRank = item.rank
    # print("DEBUG - Rank of item is: " + str(itemRank))
    # query = Note.select(subquery.c.id, subquery.c.rank).from_(subquery).where(subquery.c.rank > itemRank).limit(2)

def findAllResults(orderByColumn, orderAsc, limit, offset = 0, displayToggledOnlyModeOn = False, displaySearchTermModeOn = False, toggledRowsDict = dict(), searchTerm = ''):
    # Note: orderByColumn 0 = customOrder, 1 = title, 2 = created, 3 = lastUpdated
    # Note: search for flagged notes (displayToggledOnlyModeOn = True) will take precedence over search by keyword (displaySearchTermModeOn = True)
    # displayToggledOnlyModeOn should be set to True only if toggledRowsDict is not empty; displaySearchTermModeOn should be set to True only if searchTerm is not an empty string [len(searchTerm) > 0]

    if orderByColumn == 0:
        # Order notes by customOrder
        orderByColumnPeewee = Note.custom_order

    elif orderByColumn == 1:
        # Order notes by title
        orderByColumnPeewee = Note.title

    elif orderByColumn == 2:
        # Order notes by created date
        orderByColumnPeewee = Note.created

    elif orderByColumn == 3:
        # Order notes by lastUpdated date
        orderByColumnPeewee = Note.last_updated
    else:
        # Fallback to order notes by customOrder
        orderByColumnPeewee = Note.custom_order

    secondaryOrderParam = Note.id

    if orderAsc == False:
        orderByColumnPeewee = orderByColumnPeewee.desc()
        secondaryOrderParam = secondaryOrderParam.desc()

    # Displaying user search results by toggled rows - No additional search needed
    if displayToggledOnlyModeOn:
        custom_order_case = Case(Note.parent.is_null(), [(True, Note.custom_order)], 1)
        queryDictList = Note.select(Note.id, custom_order_case.alias('custom_order')).where(Note.id.in_(list(toggledRowsDict.keys()))).order_by(orderByColumnPeewee, secondaryOrderParam).offset(offset).limit(limit).dicts()
        parentsIdList = [dictItem['id'] for dictItem in queryDictList]
    # Displaying user search results by searchTerm
    elif displaySearchTermModeOn:
        custom_order_case = Case(Note.parent.is_null(), [(True, Note.custom_order)], 1)
        queryDictList = Note.select(Note.id, Note.parent, Note.title, custom_order_case.alias('custom_order')).where(Note.title.contains(searchTerm)).order_by(orderByColumnPeewee, secondaryOrderParam).offset(offset).limit(limit).dicts()
        parentsIdList = [dictItem['id'] for dictItem in queryDictList]
    # Default display
    else:
        parentsIdList = Note.select(Note.id).where(Note.parent.is_null()).order_by(orderByColumnPeewee, secondaryOrderParam).offset(offset).limit(limit)

    return retrieveAllFromIdList(orderByColumn, orderAsc, parentsIdList, displayToggledOnlyModeOn, displaySearchTermModeOn)


def retrieveAllFromIdList(orderByColumn, orderAsc, parentsIdList, displayToggledOnlyModeOn = False, displaySearchTermModeOn = False):
    # Define the base case of our recursive CTE. This will be items that have a null parent foreign-key.
    Base = Note.alias()
    path = Base.id.alias('path')
    level = Value(1).alias('level')
    base_case = (Base.select(Base, path, level).where(Base.id.in_(parentsIdList)).cte('base', recursive=True))

    # Define the recursive terms.
    RTerm = Note.alias()
    rpath = base_case.c.path.concat(',').concat(RTerm.id).alias('path')
    rlevel = (base_case.c.level + 1).alias('level')
    recursive = (RTerm.select(RTerm, rpath, rlevel).join(base_case, on=(RTerm.parent == base_case.c.id)))

    # The recursive CTE is created by taking the base case and UNION ALL with the recursive term.
    cte = base_case.union_all(recursive)

    if(orderByColumn == 0):
        orderByColumnPeewee = cte.c.custom_order
    elif(orderByColumn == 1):
        orderByColumnPeewee = cte.c.title
    elif (orderByColumn == 2):
        orderByColumnPeewee = cte.c.created
    elif (orderByColumn == 3):
        orderByColumnPeewee = cte.c.last_updated
    else:
        orderByColumnPeewee = cte.c.custom_order

    secondaryOrderParam = cte.c.id
    if orderAsc == False:
        orderByColumnPeewee = orderByColumnPeewee.desc()
        secondaryOrderParam = secondaryOrderParam.desc()

    # We will now query from the CTE
    # Note: I added a final orderBy cte.c.id to make sure that order will always be unique (since note id is unique) even when the main orderBy param is equal (for example custom order for user searches);
    # otherwise there could be severe issues in the findNextResults result (for example after deleting a record in displayToggledOnlyModeOn)
    # Displaying all results
    if not displayToggledOnlyModeOn and not displaySearchTermModeOn:
        query = cte.select_from(cte.c.id, cte.c.title, cte.c.description, cte.c.parent_id, cte.c.custom_order, cte.c.fraction_num, cte.c.fraction_denom, cte.c.created, cte.c.last_updated, cte.c.path, cte.c.level).order_by(cte.c.level, orderByColumnPeewee, secondaryOrderParam)
    # Displaying user search results (either by toggledRowsDict or searchTerm)
    # In this case custom order parameters should all be changed to be equal to avoid random reordering caused by children items being displayed at the root level
    else:
        custom_order_case = Case(cte.c.level, [(1, 1.0)], cte.c.custom_order)
        fraction_num_case = Case(cte.c.level, [(1, 1)], cte.c.fraction_num)
        fraction_denom_case = Case(cte.c.level, [(1, 1)], cte.c.fraction_denom)
        query = cte.select_from(cte.c.id, cte.c.title, cte.c.description, cte.c.parent_id, custom_order_case.alias('custom_order'), fraction_num_case.alias('fraction_num'), fraction_denom_case.alias('fraction_denom'), cte.c.created, cte.c.last_updated, cte.c.path, cte.c.level).order_by(cte.c.level, orderByColumnPeewee, secondaryOrderParam)

    # DEBUG: print the query sql to the console
    # print(query.sql())

    # DEBUG: print the db query results to the console
    # queryDebug = query.dicts()
    # print(json.dumps(list(queryDebug), indent=4))

    my_dict = collections.OrderedDict()

    for row in query:
        data = {'id': row.id, 'title':row.title, 'description':row.description, 'custom_order':row.custom_order, 'fraction_num':row.fraction_num, 'fraction_denom':row.fraction_denom, 'created':row.created, 'last_updated':row.last_updated}
        if not row.parent_id or len(str(row.path)) <= 2:
            my_dict[row.id] = data
        else:
            keysList = row.path.split(",")[:-1]
            parentItem = my_dict
            # i = 1
            for key in keysList:
                parentItem = parentItem[int(key)]
                if not 'children' in parentItem:
                    # parentItem['children'] = {}
                    parentItem['children'] = collections.OrderedDict()
                parentItem = parentItem['children']

            parentItem[row.id] = data

    # This is probably a working ALTERNATIVE, but more elaborated.
    # final_dict = collections.OrderedDict()
    # my_dict = collections.OrderedDict()
    # for row in query:
    #     my_dict[row.id] = {'id': row.id, 'title':row.title, 'description':row.description, 'custom_order':row.custom_order, 'fraction_num':row.fraction_num, 'fraction_denom':row.fraction_denom, 'created':row.created, 'last_updated':row.last_updated}
    #     if row.parent_id:
    #         if not 'children' in my_dict[row.parent_id]:
    #             my_dict[row.parent_id]['children'] = {}
    #         my_dict[row.parent_id]['children'][row.id] = my_dict[row.id]
    #     else:
    #         final_dict[row.id] = my_dict[row.id]
    #
    # DEBUG: print the dictionary content to the console
    # print(json.dumps(my_dict, indent=4))

    return my_dict

# Note: can't find any reference to this method. Probably can be deleted after testing that everything works fine when commented out.
# def findDictItem(dict, keysList):
#     if len(keysList) > 1:
#         return findDictItem(dict[keysList[0]], keysList[:-1])
#     else:
#         return dict[keysList[0]]

def populateTreestore(treestore, notesDict, toggledRowsDict, ancestor = None):
    for note in notesDict.values():
        noteToggledValue = checkNoteToggledValue(note['id'], toggledRowsDict)
        if not ancestor:
            newAncestor = treestore.append(None, [note['id'], noteToggledValue, note['title'], note['description'], note['custom_order'], note['fraction_num'], note['fraction_denom'], note['created'], note['last_updated']])
        else:
            newAncestor = treestore.append(ancestor, [note['id'], noteToggledValue, note['title'], note['description'], note['custom_order'], note['fraction_num'], note['fraction_denom'], note['created'], note['last_updated']])
        if 'children' in note:
            for child in note['children'].values():
                noteToggledValue = checkNoteToggledValue(child['id'], toggledRowsDict)
                descendant = treestore.append(newAncestor, [child['id'], noteToggledValue, child['title'], child['description'], child['custom_order'], child['fraction_num'], child['fraction_denom'], child['created'], child['last_updated']])
                if 'children' in child:
                    populateTreestore(treestore, child['children'], toggledRowsDict, ancestor = descendant)
                    
    return treestore

def checkNoteToggledValue(noteId, toggledRowsDict):
    if noteId in toggledRowsDict:
        return True
    else:
        return False

def findNoteByDbId(noteDbId):
    note = Note.get_by_id(noteDbId)
    return note

def findRecursivePathByDbId(noteDbId):
    # Define the base case of our recursive CTE. This will be items that have a null parent foreign-key.
    Base = Note.alias()
    path = Base.id.alias('path')
    level = Value(1).alias('level')
    base_case = (Base.select(Base, path, level).where(Base.id == noteDbId).cte('base', recursive=True))

    # Define the recursive terms.
    RTerm = Note.alias()
    rpath = base_case.c.path.concat(',').concat(RTerm.id).alias('path')
    rlevel = (base_case.c.level + 1).alias('level')
    recursive = (RTerm.select(RTerm, rpath, rlevel).join(base_case, on=(RTerm.id == base_case.c.parent_id)))

    # The recursive CTE is created by taking the base case and UNION ALL with the recursive term.
    cte = base_case.union_all(recursive)

    # We will now query from the CTE
    # query = cte.select_from(cte.c.id, cte.c.parent_id, cte.c.path, cte.c.level).order_by(cte.c.level)
    query = cte.select_from(cte.c.id, cte.c.title).order_by(cte.c.level.desc())

    result = list(query.dicts())

    # Result example. Note: results are ordered from root parent (top) to last child (bottom).
    # [
    #     {
    #         "id": 6,
    #         "title": "David"
    #     },
    #     {
    #         "id": 17,
    #         "title": "Malcom"
    #     }
    # ]

    # DEBUG: print the db query results to the console
    # queryDebug = query.dicts()
    # print(json.dumps(list(queryDebug), indent=4))

    return result

def findAllChildrenDbIds(parentDbId):
    # Define the base case of our recursive CTE. This will be items that have a null parent foreign-key.
    Base = Note.alias()
    path = Base.id.alias('path')
    level = Value(1).alias('level')
    base_case = (Base.select(Base, path, level).where(Base.id == parentDbId).cte('base', recursive=True))

    # Define the recursive terms.
    RTerm = Note.alias()
    rpath = base_case.c.path.concat(',').concat(RTerm.id).alias('path')
    rlevel = (base_case.c.level + 1).alias('level')
    recursive = (RTerm.select(RTerm, rpath, rlevel).join(base_case, on=(RTerm.parent == base_case.c.id)))

    # The recursive CTE is created by taking the base case and UNION ALL with the recursive term.
    cte = base_case.union_all(recursive)

    # We will now query from the CTE
    query = cte.select_from(cte.c.id, cte.c.parent_id, cte.c.path, cte.c.level).order_by(cte.c.level)

    dbIdsSet = set()

    for row in query:
        dbIdsSet.add(row.id)

    return dbIdsSet

def saveNote(treestore, currentTab, resultsPerPage, resultsPageNum):
    noteTitle = currentTab.titleString
    noteDescription = currentTab.descriptionString
    sourceviewBuffer = currentTab.sourceview.get_buffer()
    startIter = sourceviewBuffer.get_start_iter()
    endIter = sourceviewBuffer.get_end_iter()
    noteContent = sourceviewBuffer.get_text(startIter, endIter, True)
    if currentTab.refNoteDbId:
        refNoteObj = Note.get_by_id(currentTab.refNoteDbId)

    if currentTab.noteDbId:
        noteDbId = currentTab.noteDbId
        note = findNoteByDbId(noteDbId)
        note.title = noteTitle
        note.description = noteDescription
        note.content = noteContent
        note.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note.save()
        return note.id
    else:
        if(currentTab.position == 0): # first root item
            query = Note.select().where(Note.parent == None).order_by(Note.custom_order).limit(1)
            firstRootItem = query[0]
            custom_order = firstRootItem.custom_order
            if (custom_order > 1):
                if custom_order.is_integer():
                    num = custom_order - 1
                else:
                    num = math.floor(firstRootItem.custom_order)

                denom = 1

            else:
                sternBrocotRoot = sternBrocot.SBNode()
                trg_frac = (firstRootItem.fraction_num, firstRootItem.fraction_denom)
                insert_after = False
                new_frac = sternBrocotRoot.find_next_fraction(trg_frac, insert_after)
                num = new_frac[0]
                denom = new_frac[1]

            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=None,
                               custom_order=num / denom, fraction_num=num, fraction_denom=denom)

            return note.id

        elif(currentTab.position == 1): #last root item
            query = Note.select().where(Note.parent == None).order_by(Note.custom_order.desc()).limit(1)
            lastRootItem = query[0]
            newNoteCustomIndex = math.ceil(lastRootItem.custom_order) + 1
            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=None,
                               custom_order=newNoteCustomIndex, fraction_num=newNoteCustomIndex)

            return note.id

        elif (currentTab.position == 2): #first sibling
            refNoteParentDbId = findParentDbId(currentTab.refNoteDbId)
            query = Note.select().where(Note.parent == refNoteParentDbId).order_by(Note.custom_order).limit(1)
            firstSibling = query[0]
            custom_order = firstSibling.custom_order
            if (custom_order > 1):
                if custom_order.is_integer():
                    num = custom_order-1
                else:
                    num = math.floor(firstSibling.custom_order)

                denom = 1

            else:
                sternBrocotRoot = sternBrocot.SBNode()
                trg_frac = (firstSibling.fraction_num, firstSibling.fraction_denom)
                insert_after = False
                new_frac = sternBrocotRoot.find_next_fraction(trg_frac, insert_after)
                num = new_frac[0]
                denom = new_frac[1]

            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=refNoteParentDbId,
                               custom_order=num/denom, fraction_num=num, fraction_denom=denom)

            return note.id

        elif (currentTab.position == 3): #last sibling
            refNoteParentDbId = findParentDbId(currentTab.refNoteDbId)
            query = Note.select().where(Note.parent == refNoteParentDbId).order_by(Note.custom_order.desc()).limit(1)
            lastSibling = query[0]
            custom_order = lastSibling.custom_order
            newNoteCustomOrder = math.ceil(custom_order) + 1
            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=refNoteParentDbId,
                               custom_order=newNoteCustomOrder, fraction_num=newNoteCustomOrder, fraction_denom=1)

            return note.id

        elif (currentTab.position == 4): #insert before
            # ParentDbId can be int or None (if root item)
            refNoteParentDbId = findParentDbId(currentTab.refNoteDbId)
            # Compare refNote custom_order with the custom_order of the first child of parentDbId
            query = Note.select().where(Note.parent == refNoteParentDbId).order_by(Note.custom_order).limit(1)
            firstItem = query[0]
            firstItemCustomOrder = firstItem.custom_order
            refNoteCustomOrder = refNoteObj.custom_order

            if (refNoteCustomOrder == firstItemCustomOrder and refNoteCustomOrder > 1):
                if float(refNoteCustomOrder).is_integer():
                    num = refNoteCustomOrder - 1
                else:
                    num = math.floor(refNoteCustomOrder)

                denom = 1

            elif(refNoteCustomOrder == firstItemCustomOrder and refNoteCustomOrder <= 1):
                refNoteNum = refNoteObj.fraction_num
                refNoteDenom = refNoteObj.fraction_denom
                sternBrocotRoot = sternBrocot.SBNode()
                trg_frac = (refNoteNum, refNoteDenom)
                insert_after = False
                new_frac = sternBrocotRoot.find_next_fraction(trg_frac, insert_after)
                num = new_frac[0]
                denom = new_frac[1]

            else:
                refNoteNum = refNoteObj.fraction_num
                refNoteDenom = refNoteObj.fraction_denom
                query = Note.select().where((Note.parent == refNoteParentDbId) & (Note.custom_order < refNoteCustomOrder)).order_by(Note.custom_order.desc()).limit(1)
                prevItem = query[0]
                prevItemNum = prevItem.fraction_num
                prevItemDenom = prevItem.fraction_denom
                sternBrocotRoot = sternBrocot.SBNode()
                upper_frac = (refNoteNum, refNoteDenom)
                lower_frac = (prevItemNum, prevItemDenom)
                new_frac = sternBrocotRoot.find_intermediate_fraction(lower_frac, upper_frac)
                num = new_frac[0]
                denom = new_frac[1]

            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=refNoteParentDbId,
                               custom_order=num / denom, fraction_num=num, fraction_denom=denom)

            return note.id

        elif (currentTab.position == 5): #insert after
            # ParentDbId can be int or None (if root item)
            refNoteParentDbId = findParentDbId(currentTab.refNoteDbId)
            # Compare refNote custom_order with the custom_order of the first child of parentDbId
            query = Note.select().where(Note.parent == refNoteParentDbId).order_by(Note.custom_order.desc()).limit(1)
            lastItem = query[0]
            lastItemCustomOrder = lastItem.custom_order
            refNoteCustomOrder = refNoteObj.custom_order

            if(refNoteCustomOrder == lastItemCustomOrder):
                if float(refNoteCustomOrder).is_integer():
                    num = math.ceil(refNoteCustomOrder) + 1
                else:
                    num = math.ceil(refNoteCustomOrder)

                denom = 1

            else:
                refNoteNum = refNoteObj.fraction_num
                refNoteDenom = refNoteObj.fraction_denom
                query = Note.select().where((Note.parent == refNoteParentDbId) & (Note.custom_order > refNoteCustomOrder)).order_by(Note.custom_order).limit(1)
                nextItem = query[0]
                nextItemNum = nextItem.fraction_num
                nextItemDenom = nextItem.fraction_denom
                sternBrocotRoot = sternBrocot.SBNode()
                lower_frac = (refNoteNum, refNoteDenom)
                upper_frac = (nextItemNum, nextItemDenom)
                #insert_after = False
                new_frac = sternBrocotRoot.find_intermediate_fraction(lower_frac, upper_frac)
                num = new_frac[0]
                denom = new_frac[1]

            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=refNoteParentDbId,
                               custom_order=num / denom, fraction_num=num, fraction_denom=denom)

            return note.id

        elif (currentTab.position == 6): #insert as child
            query = Note.select().where(Note.parent == currentTab.refNoteDbId).order_by(Note.custom_order.desc()).limit(1)
            if(len(query) == 1):
                lastSibling = query[0]
                custom_order = lastSibling.custom_order
                if float(custom_order).is_integer():
                    newNoteCustomOrder = math.ceil(custom_order) + 1
                else:
                    newNoteCustomOrder = math.ceil(custom_order)
            else:
                newNoteCustomOrder = 1

            note = Note.create(title=noteTitle, description=noteDescription, content=noteContent, parent=currentTab.refNoteDbId,
                               custom_order=newNoteCustomOrder, fraction_num=newNoteCustomOrder, fraction_denom=1)

            return note.id

        else:
            pass
    pass

def findPreviousRecordsCountByDbId(orderByColumn, orderAsc, refItemDbId, displayToggledOnlyModeOn = False, toggledRowsDict = dict()):
    # This method is useful to decide if a newly saved note should be added / displayed in the current treeview

    # Note: orderByColumn 0 = customOrder, 1 = title, 2 = created, 3 = lastUpdated
    if orderByColumn == 0:
        columnX = Note.custom_order
    elif orderByColumn == 1:
        columnX = fn.Lower(Note.title)
    elif orderByColumn == 2:
        columnX = Note.created
    elif orderByColumn == 3:
        columnX = Note.last_updated
    else:
        columnX = Note.custom_order

    lastTreeviewItemColumnXValue = Note.select(columnX).where(Note.id == refItemDbId)

    if displayToggledOnlyModeOn:
        custom_order_case = Case(Note.parent.is_null(), [(True, Note.custom_order)], 1)
        if orderAsc == True:
            previousRecordsCount = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.id.in_(list(toggledRowsDict.keys()))) & ((columnX < lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id < refItemDbId)))).order_by(columnX, Note.id).count()
        else:
            previousRecordsCount = Note.select(Note.id, custom_order_case.alias('custom_order')).where((Note.id.in_(list(toggledRowsDict.keys()))) & ((columnX > lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id > refItemDbId)))).order_by(columnX.desc(), Note.id.desc()).count()
    else:
        if orderAsc == True:
            previousRecordsCount = Note.select(Note.id).where((Note.parent.is_null()) & ((columnX < lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id < refItemDbId)))).order_by(columnX, Note.id).count()
        else:
            previousRecordsCount = Note.select(Note.id).where((Note.parent.is_null()) & ((columnX > lastTreeviewItemColumnXValue) | ((columnX == lastTreeviewItemColumnXValue) & (Note.id > refItemDbId)))).order_by(columnX.desc(), Note.id.desc()).count()

    return previousRecordsCount

# This method returns an int or None
def findParentDbId(childDbId):
    Child = Note.alias()
    query = Note.select(Note.id).join(Child, on=(Note.id == Child.parent)).where(Child.id == childDbId)
    if query:
        parentDbId = query[0].id
    else:
        parentDbId = None
    return parentDbId




