import json
import pickle
import time
import requests
import pytesseract
from PIL import Image
from imgPreprocessing import drawLinesFor

# Username and license code
LicenseCode = '8AB88B09-7C85-4B88-A280-46042E1F0FBF'
UserName = 'ROBOHT'

"""
WARNING!

The account used for this program can only ocr 25 images per day and is completely INSUFFICIENT for this program to run 
even once.
For this program to properly function, please charge about $40 into this account for 1000 pages of OCRs.
The username is RobOHt and the password is 770f9cd2. The website is onlineocr.net.

As this account is opened to public, I highly recommend creating an account of your own before charging any money, 
for otherwise anyone else could use this $40 OCR opportunity without spending money themselves.
"""


def buildOCR(filename):
    strOCR = pytesseract.image_to_string(Image.open(filename))
    posOCR = pytesseract.image_to_boxes(Image.open(filename))
    jobj = json.dumps([strOCR, posOCR])

    new_OCRname = f'./ocr_papers/paper-{time.time()}_OCR.pickle'
    with open(new_OCRname, 'wb') as f:
        pickle.dump(jobj, f)
    return new_OCRname


'''buildOCR() usage: '''
if __name__ == "__main__":
    name = drawLinesFor("./img_papers/paper-1577179078.png")
    buildOCR(name)
