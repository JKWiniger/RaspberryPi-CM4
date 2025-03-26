import cv2
from uiutils import *
import numpy as np
import pyzbar.pyzbar as pyzbar

button = Button()

fm = get_dog_type_cache()
result = fm[0]
dog_type = result

font = cv2.FONT_HERSHEY_SIMPLEX 
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

def cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=30):
    if (isinstance(img, np.ndarray)):  
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype(
        "/home/pi/model/msyh.ttc", textSize, encoding="utf-8")
    draw.text(position, text, textColor, font=fontStyle)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

 
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")

while(True):
    ret, img = cap.read() 
    img_ROI_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    barcodes = pyzbar.decode(img_ROI_gray) 
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        img=cv2AddChineseText(img,text, (10, 30),(0, 255, 0), 30)
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))

    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break
cap.release()
