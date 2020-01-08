import pickle
import string
import PIL
from PIL import Image
from pdf2image import convert_from_path
from buildOCR import buildOCR
from imgPreprocessing import cutTailFor, drawLinesFor, enhanceFor, int_to_roman
from difflib import SequenceMatcher
import os
import time
import json
import sqlite3
import pandas as pd

ppr_Path = "./papers/"
Qs_Path = "./Results"
PIL.Image.MAX_IMAGE_PIXELS = 1.5e9


class Decomposer:

    def __init__(self, filename, pattern, ocr):
        if pattern == "Num":
            self.pattern = []
            for i in range(1, 100):
                self.pattern.append(str(i)+".")
                self.pattern.append(str(i) + ",")
                self.pattern.append(str(i) + "a")
                self.pattern.append(str(i) + "*")
                self.pattern.append(str(i) + "'")
                self.pattern.append(str(i) + ".-")
                self.pattern.append(str(i) + ".~")
                self.pattern.append(int_to_roman(i))
                self.pattern.append(int_to_roman(i) + ".")
                self.pattern.append(f"{int_to_roman(i)})")
                self.pattern.append(f"({int_to_roman(i)})")
        elif pattern == "Choice":
            self.pattern = [f"({crctr})" for crctr in string.ascii_lowercase]
            for crctr in string.ascii_lowercase:
                self.pattern.append(f"({crctr})")
                self.pattern.append(f"{crctr})")
                self.pattern.append(f"({crctr.swapcase()})")
                self.pattern.append(f"{crctr.swapcase()})")

        self.InputType = pattern

        self.filename = filename
        with open(ocr, 'rb') as f:
            jobj = pickle.load(f)
        lstobj = json.loads(jobj)
        self.strppr = str(lstobj[0])
        self.strpos = lstobj[1]
        print(f"Scanned Results for image {filename}")
        print("\n\n")
        print(self.strppr)
        print("\n\nstrpos:")
        print(self.strpos.replace('\n', '||||||||||||||||||||||'))

    @staticmethod
    def dfedOCR(stri):
        """
        ocr output to df
        :param stri: the str format ocr output file to be converted to df
        :return: df format ocr
        """

        lst = [[]]
        for crctr in stri:
            if crctr != "\n":
                lst[-1].append(crctr)
            else:
                # For each "\n", add a new line.
                lst.append([])
        dfstr = pd.DataFrame(lst)
        return dfstr

    def allocatePat(self):
        """
        this function allocates the preset pattern for a question mark and looks for its position
        in the paper (ppr).
        :return: The relative position of every question mark located in percentage.
        """
        print("Processing commence")

        try:
            dfppr = self.dfedOCR(self.strppr)
            lstpos = self.strpos.split("\n")
            lstpos = [row.split() for row in lstpos]
            lstpos = [row for row in lstpos if row[0] not in ['~']]
        except:
            return "return"
        print(lstpos)
        counter = 0
        validater = 0
        searchList = []
        posList = []

        # Count the amount of words in front of each question mark.
        for index, row in dfppr.iterrows():
            # Utils:
            RawlstRow = list(row)
            strRow = "".join([item for item in RawlstRow if item is not None])
            rowByWord = strRow.split()

            # Check if row starts with a question number.
            try:
                for questionMark in self.pattern:
                    wordInNum = ''.join([num for num in list(rowByWord[0])])
                    if SequenceMatcher(None, questionMark, wordInNum).ratio() >= 0.66:
                        print(rowByWord[0])
                        print(questionMark)
                        searchList.append(counter)
                        break
            except IndexError:
                pass

            for i in RawlstRow:
                if i is not None and i != " ":
                    counter = counter + 1

        for index in searchList:
            # coordinate outputs 0 occasionally; if happens, look for another coordinate util not 0
            correction = 1
            coordinates = lstpos[index]
            coordinate = coordinates[2]
            while int(coordinate) == 0:
                try:
                    coordinates = lstpos[index + correction]
                    coordinate = coordinates[2]
                    if int(coordinate) == 0:
                        coordinates = lstpos[index - correction]
                        coordinate = coordinates[2]

                except IndexError:
                    coordinates = lstpos[index - correction]
                    coordinate = coordinates[2]

                correction = correction + 1
            posList.append(coordinate)

        percentileSemblance = lstpos[0][2]
        correction = 1
        while int(percentileSemblance) == 0:
            percentileSemblance = lstpos[0 + correction][2]
            correction = correction + 1

        posList = [(int(percentileSemblance) - int(index)) / int(percentileSemblance) for index in posList]
        return posList

    def cutImage(self, InputType):
        error = 100  # Move this value up a certain pixel number for each cut. Empirical.
        cutTailFor(self.filename)
        imgppr = Image.open(self.filename)
        width, height = imgppr.size[0], imgppr.size[1]
        percentages = self.allocatePat()

        if percentages == "return":
            return

        for i in range(0, len(percentages) - 1):
            if percentages[i] < max(percentages[0:i]):
                percentages[i] = -1

        percentages = [num for num in percentages if num >= 0]

        print(percentages)
        for item in percentages:
            print(type(item))

        if len(percentages) == 0:
            # If no question marks, the entire page is a question.
            percentages = [0]
        elif len(percentages) < 3:
            return "Can't cut this."

        for i in range(0, len(percentages)):
            # Cut image
            try:
                # Convert the calculated percentages into image pixels that fit a cropper.
                upper = (percentages[i]) * height - error
                lower = (percentages[i+1]) * height - error
            except IndexError:
                upper = (percentages[i]) * height - error
                lower = height
            cropped = imgppr.crop((0, int(upper), width, int(lower)))

            # Save image
            if InputType == "ppr":
                timeStamp = float(time.time())
                os.makedirs(f"./Results/question-{timeStamp}")
                name = f"./Results/question-{timeStamp}/question-{timeStamp}.png"
                cropped.save(name)
                print(f"Cutted a question paper. Stored at {name}")
            elif InputType == "question":
                Qdirectory = self.filename
                Qdirectory = Qdirectory.split("/")[-1]
                Qdirectory = Qdirectory[0:-4]
                try:
                    os.makedirs(f"./Results/{Qdirectory}/Choices")
                except FileExistsError:
                    pass
                name = f"./Results/{Qdirectory}/Choices/Choice-{time.time()}.png"
                cropped.save(name)
                print(f"Cutted a question. Stored at {name}")

        return "Can cut this."


def RecordListToTable(IMG_CHOICE_list):
    with sqlite3.connect("IMG_CHOICE.db") as connection:
        c = connection.cursor()
        try:
            c.execute("""CREATE TABLE img_choice(image TEXT, A TEXT, B TEXT, C TEXT, D TEXT)""")
        except sqlite3.OperationalError:
            pass
        for dataSet in IMG_CHOICE_list:
            image = dataSet[0]
            choices = []
            for i in range(4):
                try:
                    choices.append(dataSet[-1][i])
                except TypeError and IndexError:
                    choices.append(None)
            c.execute('INSERT INTO img_choice VALUES(?, ?, ?, ?, ?)', (image,
                                                                       choices[0], choices[1], choices[2], choices[3]))


def CutPagesToQs():
    # Loop through every (pdf) file in /papers
    for ppr in os.listdir(ppr_Path):
        pages = convert_from_path(os.path.join(ppr_Path, ppr), 500)
        for page in pages:
            pic_Path = f'./img_papers/paper-{int(time.time())}.png'
            # Convert pdf to image
            page.save(pic_Path, 'PNG')
            # Convert image to underlined image
            lined_pic_Path = drawLinesFor(pic_Path)
            # OCR underlined image
            ocr_Path = buildOCR(lined_pic_Path)
            # Delete underlined image
            os.remove(lined_pic_Path)
            # Cut image into questions
            Decomposer(pic_Path, 'Num', ocr_Path).cutImage("ppr")


def CutQsToChoices():
    for QFolder in os.listdir(Qs_Path):
        try:
            for img in os.listdir(os.path.join(Qs_Path, QFolder)):
                if img != ".DS_Store":
                    Q_img_Path = os.path.join(Qs_Path, QFolder, img)
                    if not str(img).endswith(".png"):
                        print(img + "is not an img.")
                        continue
                    Q_ocr_Path = buildOCR(Q_img_Path)
                    TRY1 = Decomposer(Q_img_Path, 'Choice', Q_ocr_Path).cutImage("question")
                    if TRY1 == "Can cut this.":
                        print(TRY1, "__Attempt 1__")
                    else:
                        print("Problem occurred on attempt 1. I'll try again with the image underlined")
                        Q_lined_img_Path = drawLinesFor(Q_img_Path)
                        Q_ocr_Path = buildOCR(Q_lined_img_Path)
                        TRY2 = Decomposer(Q_lined_img_Path, 'Choice', Q_ocr_Path).cutImage("question")
                        if TRY2 == "Can cut this.":
                            print(TRY2, "__Attempt 2__")
                        else:
                            print("Problem occurred on attempt 2. I'll try again with the image enhanced")
                            enhanceFor(Q_lined_img_Path)
                            Q_ocr_Path = buildOCR(Q_lined_img_Path)
                            TRY3 = Decomposer(Q_lined_img_Path, 'Choice', Q_ocr_Path).cutImage("question")
                            if TRY3 == "Can cut this.":
                                print(TRY3, "__Attempt 3__")
                            else:
                                print(f"I can not cut question directory {Q_lined_img_Path} after THREE attempts!")

        except NotADirectoryError:
            pass


def RecordQs():
    IMG_CHOICE_list = []
    for QFolder in os.listdir(Qs_Path):
        if QFolder != ".DS_Store":
            imgPath, Choices = None, None
            for imgAndChoice in os.listdir(os.path.join(Qs_Path, QFolder)):
                if imgAndChoice.endswith(".png") and len(os.listdir(os.path.join(Qs_Path, QFolder))) == 2:
                    imgPath = imgAndChoice
                    Choices = []
                    OCR_path = buildOCR(os.path.join(Qs_Path, QFolder, imgAndChoice))
                    with open(OCR_path, 'rb') as f:
                        jobj = pickle.load(f)
                    strQuestion = str(jobj["OCRText"][0][0])
                    strQuestion.replace('\n', ' ').replace('\r', '')
                    Choices.append(strQuestion)
                elif imgAndChoice.endswith(".png"):
                    imgPath = imgAndChoice
                elif imgAndChoice == "Choices":
                    Choices = []
                    for choice in os.listdir(os.path.join(Qs_Path, QFolder, imgAndChoice)):
                        # We are finally in the correct directory.

                        OCR_path = buildOCR(os.path.join(Qs_Path, QFolder, imgAndChoice, choice))
                        with open(OCR_path, 'rb') as f:
                            jobj = pickle.load(f)
                        strChoice = str(jobj["OCRText"][0][0])
                        strChoice.replace('\n', ' ').replace('\r', '')
                        Choices.append(strChoice)
                        print(Choices)
            # Finished cycle for one "Question-xxx" folder. Load info in directory to list.
            IMG_CHOICE_list.append([imgPath, Choices])
            print(IMG_CHOICE_list)

    IMG_CHOICE_json = json.dumps(IMG_CHOICE_list)
    with open('IMG_CHOICE.json', 'w') as f:
        json.dump(IMG_CHOICE_json, f)

    RecordListToTable(IMG_CHOICE_list)


if __name__ == "__main__":
    CutPagesToQs()
    CutQsToChoices()
    RecordQs()

    '''For Test:'''
    # print(Decomposer('./img_papers/paper-1577448228.png', 'Num').cutImage())
