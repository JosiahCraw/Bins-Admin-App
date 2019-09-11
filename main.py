from tkinter import *
import signal

# FireBase Python
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import google.cloud.exceptions

fullNumber = 0
updateFull = True
moreBins = True
checkButtonsStates = dict()
running = True


def initFirebase():
    cred = credentials.Certificate('bins-5653b-firebase-adminsdk-w6hyh-33c31c1ceb.json')
    firebase_admin.initialize_app(cred, {'storageBucket': 'bins-5653b.appspot.com'})
    db = firestore.client()

    bucket = storage.bucket()

    return db, bucket


def signalHandler():
    global running
    running = False


def getEmptyBins(db, listBox):
    emptyBin = db.collection('fullBins').stream()
    global fullNumber
    listBox.delete(0, fullNumber)
    for bin in emptyBin:
        if bin.id != "Empty":
            listBox.insert(fullNumber, bin.id)
            fullNumber += 1


def getAllBins(db):
    bins = db.collection(u'bins').stream()
    return bins


def fullSnapshot(col_snapshot, changes, read_time):
    global updateFull
    updateFull = True


def binsChangedSnapshot(col_snapshot, changes, read_time):
    global moreBins
    moreBins = True


def getImages(storage):
    images = storage.list_blobs()
    return images


def addBinsToCheckList(db, top, storage):
    row = 2
    bins = getAllBins(db)
    global checkButtonsStates
    checkButtonsStates.clear()
    for bin in bins:
        checkButtonsStates[bin.id] = IntVar()
        checkButton = Checkbutton(text=bin.id, variable=checkButtonsStates[bin.id]).grid(row=row, column=2)
        row += 1

    selectLabel = Label(top, text="Select Image To deploy")
    selectLabel.grid(row=row, column=2)
    row+=1

    images = getImages(storage)

    radioButtonVar = StringVar()
    radioButtonVar.set("0")

    selected = list()

    def deployImage(imageName, db, bin):
        db.collection(u'bins').document(bin).update({u'image': imageName})

    def deployToBins():
        selected = list()
        for key, value in checkButtonsStates.items():
            print(key + ":" + str(value.get()))
            if value.get() == 1:
                selected.append(key)

        imageName = radioButtonVar.get()
        print(selected)
        print(imageName)
        for bin in selected:
            deployImage(imageName, db, bin)

    for image in images:
        radioButton = Radiobutton(top, text=image.name, variable=radioButtonVar, value=image.name)
        radioButton.grid(row=row, column=2)
        row += 1

    deployButton = Button(text="Deploy", command=deployToBins)
    deployButton.grid(row=row, column=2)
    row += 1


def dispClickedInfo(db, labelVar, binID):
    doc = db.collection(u'bins').document(binID)

    try:
        info = doc.get()
        infoDict = info.to_dict()
        name = infoDict["name"]
        location = infoDict["location"]
        print("Name: " + name + " Location: " + location)
        labelVar.set("Name: " + name + " Location: " + location)
    except google.cloud.exceptions.NotFound:
        print(u'Bin does not exist')



def main():
    signal.signal(signal.SIGINT, signalHandler)

    db, storage = initFirebase()
    top = Tk()
    top.geometry("950x1080")

    top.title("Bins Admin Panel")
    lbl = Label(top, text="Full Bins").grid(row=0, column=0)

    infoVar = StringVar()
    infoVar.set('Select A Bin')
    infoLabel = Label(top, textvariable=infoVar).grid(row=2, column=0)
    listbox = Listbox(top)
    listbox.grid(row=1, column=0)

    getEmptyBins(db, listbox)

    global updateFull
    if updateFull:
        getEmptyBins(db, listbox)
        updateFull = False

    topLabel = Label(top, text="Bins Select to deploy").grid(row=1, column=2)

    global moreBins
    if moreBins:
        addBinsToCheckList(db, top, storage)
        moreBins = False

    fullQuery = db.collection(u'fullBins').on_snapshot(fullSnapshot)

    binsQuery = db.collection(u'bins').on_snapshot(binsChangedSnapshot)

    def onClick(event):
        w = event.widget
        output = w.curselection()

        if len(output) <= 1:
            index = 0
        else:
            index = output[0]

        binID = w.get(index)
        dispClickedInfo(db, infoVar, binID)

    listbox.bind('<<ListboxSelect>>', onClick)

    global running

    while running:
        top.update_idletasks()
        top.update()

        if updateFull:
            getEmptyBins(db, listbox)
            updateFull = False

        if moreBins:
            addBinsToCheckList(db, top, storage)
            moreBins = False

    top.quit()

    fullQuery.unsubscribe()
    binsQuery.unsubscribe()


main()
