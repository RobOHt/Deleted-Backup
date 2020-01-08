import cv2
import numpy as np
from PIL import Image
import time
import os
from shutil import copyfile
import statistics


def drawLinesFor(filename):
    """
    Draws lines for blank pixel rows of an image.
    This proves to increase OCR accuracy considerably in some cases.
    :param filename: the image to get added lines.
    :return: file name of newly lined image. Returning this allows use of this image later.
    """
    whiteThreshold = 150
    im = cv2.imread(filename)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gray = gray.tolist()
    width = len(gray[0])
    whiteStart, whiteEnd = 0, 0
    whiteStartCount = True

    def drawALine(start, end):
        # thickness = int(0.001 * len(gray))  # Static line width
        thickness = 10
        midPoint = (start + end) / 2
        starter = midPoint - thickness
        for j in range(0, thickness * 2):
            try:
                gray[int(starter + j)] = [0 for nums in range(width)]
            except IndexError:
                pass

    for i in range(0, len(gray)):
        if whiteStartCount and min(gray[i]) >= whiteThreshold:
            whiteStart = i
            whiteStartCount = False
        elif not whiteStartCount and (min(gray[i]) <= whiteThreshold or i == len(gray) - 1):
            whiteEnd = i - 1
            whiteStartCount = True
            drawALine(whiteStart, whiteEnd)

    linedImg = (np.array(gray)).astype(np.uint8)
    img = Image.fromarray(linedImg)
    # img.show()
    name = f'./lined_img_papers/lined_paper-{int(time.time())}.png'
    img.save(name)
    return name


def enhanceFor(filename):
    img = cv2.imread(filename)
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    os.remove(filename)
    cv2.imwrite(filename, img)


def cutTailFor(filename):
    whiteThreshold = 244
    im = cv2.imread(filename)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gray = gray.tolist()
    width = len(gray[0])
    whiteStart, whiteEnd = 0, 0
    whiteStartCount = True

    # Cut top
    for i in range(0, len(gray)):
        if whiteStartCount and statistics.mean(gray[i]) <= whiteThreshold:
            gray = gray[i:]
            break
    Cutted_Img = (np.array(gray)).astype(np.uint8)
    img = Image.fromarray(Cutted_Img)

    # Cut tail
    # for i in range(0, len(gray)):
    #     if whiteStartCount and statistics.mean(gray[i]) >= whiteThreshold:
    #         # This row is white; start counting
    #         whiteStart = i
    #         whiteStartCount = False
    #     elif not whiteStartCount and statistics.mean(gray[i]) <= whiteThreshold:
    #         whiteStartCount = True
    #     elif not whiteStartCount and i == len(gray) - 1:
    #         # This row is at the end of the page and is still white. Remove this white tail.
    #         gray = gray[0:whiteStart]
    # Cutted_Img = (np.array(gray)).astype(np.uint8)
    # img = Image.fromarray(Cutted_Img)
    # img.show()
    os.remove(filename)
    img.save(filename)


def int_to_roman(input):
    """ Convert an integer to a Roman numeral. """

    if not isinstance(input, type(1)):
        raise TypeError("expected integer, got %s" % type(input))
    if not 0 < input < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = []
    for i in range(len(ints)):
        count = int(input / ints[i])
        result.append(nums[i] * count)
        input -= ints[i] * count
    return ''.join(result)


def load_0103_to_papers():
    o1o3 = "./o1o3"
    try:
        for subject in [subject for subject in os.listdir(o1o3) if subject != ".DS_Store"]:
            for year in [year for year in os.listdir(os.path.join(o1o3, subject)) if year != ".DS_Store"]:
                for paper in [paper for paper in os.listdir(os.path.join(o1o3, subject, year)) if paper != ".DS_Store"]:
                    filename = os.path.join(o1o3, subject, year, paper)
                    copyfile(filename, os.path.join("./papers", paper))
    except NotADirectoryError:
        pass


'''drawLinesFor(filename) usage: '''
# print(drawLinesFor("./img_papers/paper-1577463609.png"))
'''enhanceFor(filename) usage: '''
# enhanceFor("./Results/question-1577463648.430978/question-1577463648.430978 copy 2.png")
'''cutTailFor(filename) usage: '''
# cutTailFor("./img_papers/paper-1578161164.png")
# load_0103_to_papers()
