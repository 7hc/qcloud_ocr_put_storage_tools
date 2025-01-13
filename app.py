import base64
import time
import cv2
from tkinter import Tk, Label, Button, Frame, Entry, StringVar, Image
from PIL import Image, ImageTk
from pydantic import BaseModel
import requests
import hashlib, hmac, json, time
from datetime import datetime

def qcloud_v3_post(SecretId,SecretKey,Service,bodyArray,headersArray):
    HTTPRequestMethod = "POST"
    CanonicalURI = "/"
    CanonicalQueryString = ""
    
    headersArray = dict(sorted(headersArray.items(), key=lambda x: x[0]))
    sortHeadersArray = headersArray
    
    SignedHeaders = ""
    CanonicalHeaders = ""
    
    
    for key in list(sortHeadersArray.keys()):
        SignedHeaders += key.lower() + ";"
    if SignedHeaders[-1] == ";":
        SignedHeaders = SignedHeaders[:-1]
    
    
    for key in list(sortHeadersArray.keys()):
        CanonicalHeaders += key.lower() + ":" + sortHeadersArray[key].lower() + "\n"
    
    
    HashedRequestPayload = hashlib.sha256(bytes(json.dumps(bodyArray),encoding="utf-8")).hexdigest()
    

    CanonicalRequest = HTTPRequestMethod + "\n" + CanonicalURI + "\n" + CanonicalQueryString + "\n" + CanonicalHeaders + "\n" + SignedHeaders + "\n" + HashedRequestPayload
    
    
    
    
    RequestTimestamp = str(int(time.time()))
    
    formattedDate = time.strftime("%Y-%m-%d", time.gmtime(int(RequestTimestamp)))
    Algorithm = "TC3-HMAC-SHA256"
    CredentialScope = formattedDate + "/" + Service + "/tc3_request"
    HashedCanonicalRequest = hashlib.sha256(bytes(CanonicalRequest,encoding="utf-8")).hexdigest()
    
    
    
    StringToSign = Algorithm + "\n" + RequestTimestamp + "\n" + CredentialScope + "\n" + HashedCanonicalRequest
    
    _SecretDate = hmac.new(key=bytes("TC3" + SecretKey,encoding="utf-8"),digestmod="sha256")
    _SecretDate.update(bytes(formattedDate,encoding="utf-8"))
    SecretDate = _SecretDate.digest()
    _SecretService = hmac.new(key=SecretDate,digestmod="sha256")
    _SecretService.update(bytes(Service,encoding="utf-8"))
    SecretService = _SecretService.digest()
    _SecretSigning = hmac.new(key=SecretService,digestmod="sha256")
    _SecretSigning.update(bytes("tc3_request",encoding="utf-8"))
    SecretSigning = _SecretSigning.digest()

    _Signature = hmac.new(key=SecretSigning,digestmod="sha256")
    _Signature.update(bytes(StringToSign,encoding="utf-8"))
    Signature = _Signature.hexdigest()
    
    
    Authorization = Algorithm + ' ' + 'Credential=' + SecretId + '/' + CredentialScope + ', ' + 'SignedHeaders=' + SignedHeaders + ', ' + 'Signature=' + Signature
    
    headersArray["X-TC-Timestamp"] = RequestTimestamp
    headersArray["Authorization"] = Authorization
    
    return headersArray


cap = cv2.VideoCapture(0)


root = Tk()
root.title("OCR入库辅助工具")
root.geometry("1000x400")








label = Label(root, width=450)
label.pack(side="left", fill="both", expand=True, padx=10, pady=10)  


right_frame = Label(root)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)


Label(right_frame, text="物料OCR结果").pack()


form_frame = Frame(right_frame)
form_frame.pack()

class entry_info(BaseModel):
    MPN:str = ""
    MFG:str = ""
    COO:str = ""
    SO:str = ""
    QTY:str = ""
    LPN:str = ""
    sub_order:str = ""

ei = entry_info()


vars_dict = {}


for field in ei.__fields__:
    vars_dict[field] = StringVar(value=ei.__fields__[field].default)


def create_label_entry(parent, label_text,value):
    frame = Frame(parent)
    frame.pack(anchor="w", fill="x", pady=(0, 5))
    Label(frame, text=label_text, anchor="e", width=20).pack(side="left")
    Entry(frame, textvariable=value).pack(side="left", fill="x", expand=True)



create_label_entry(form_frame, "制造商零件编号(MPN):", vars_dict['MPN'])
create_label_entry(form_frame, "制造商(MFG):", vars_dict['MFG'])
create_label_entry(form_frame, "原产地(CoO):", vars_dict['COO'])
create_label_entry(form_frame, "销售订单号(SO):", vars_dict['SO'])
create_label_entry(form_frame, "数量(QTY):", vars_dict['QTY'])
create_label_entry(form_frame, "LPN:", vars_dict['LPN'])
create_label_entry(form_frame, "分单号:", vars_dict['sub_order'])


def take_photo():
    image_filename = str(int(time.time()*1000)) + ".jpg"
    ret, frame = cap.read()  
    if ret:
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        label.imgtk = imgtk
        label.configure(image=imgtk)
        
        cv2.imwrite(image_filename, frame)
        return image_filename
    else:
        return None

def ocr(file_name:str):
    with open(file_name, "rb") as f:
        image_data = f.read()
    data = {
        "ImageBase64": base64.b64encode(image_data).decode(),
        "EnableCoord": False,
        "ConfigId": "General",
        "ItemNames": ["制造商零件编号(MPN)","描述(DESC)","制造商(MFG)","原产地(CoO)","销售订单号(SO)","数量(QTY)","库位(LOC)","LPN","LPN总数","DO"]
    }
    host = "ocr.tencentcloudapi.com"
    SecretId = ""
    SecretKey = ""
    headersArray = {
    'Host': host,
    'Content-Type': 'application/json',
    'X-TC-Action': 'SmartStructuralPro',
    'X-TC-Version': '2018-11-19',
    'X-TC-Region': 'ap-guangzhou',
    }
    Service = "ocr"
    headersPending = qcloud_v3_post(SecretId,SecretKey,Service,data,headersArray)
    apiurl = "https://" + host
    r = requests.post(apiurl, json=data, headers=headersPending)
    with open("k.json", 'w+',encoding="utf-8") as f:
        f.write(r.text)
    

result_data = {}

def format_d(dat):
    global result_data
    li = dat["Response"]["StructuralList"]
    for ii in li:
        ke = ii["Groups"][0]["Lines"][0]["Key"]["AutoName"]
        va = ii["Groups"][0]["Lines"][0]["Value"]["AutoContent"]
        if ke == "DO":
            va = ke + va
        
        if ke.find("LPN") != -1:
            vars_dict["LPN"].set(va)
        elif ke.find("MPN") != -1:
            vars_dict["MPN"].set(va)
        elif ke.find("MFG") != -1:
            vars_dict["MFG"].set(va)
        elif ke.find("CoO") != -1:
            vars_dict["COO"].set(va)
        elif ke.find("SO") != -1:
            vars_dict["SO"].set(va)
        elif ke.find("QTY") != -1:
            vars_dict["QTY"].set(va)
        elif ke.find("DO") != -1:
            vars_dict["sub_order"].set(va)
    
    global ei
    
    ei_dict = {key: var.get() for key, var in vars_dict.items()}
    ei = entry_info(**ei_dict)  
    print(ei.__dict__)
    result_data = ei.__dict__

def try_ocr():
    filename = take_photo()
    if not filename:
        return
    print("-> 图片保存成功")
    print(ocr(filename))
    with open("k.json","r",encoding="utf-8") as f:
        format_d(json.load(f))

def upload_data():
    global result_data
    print(result_data)

    

def print_tag():
    global result_data
    
    tag_id = "xxxxxx"
    result_data["tag_id"] = tag_id



button_frame = Frame(right_frame)
button_frame.pack(pady=10)


submit_button = Button(button_frame, text="OCR", command=try_ocr)
submit_button.pack(side="left", padx=5)


print_button = Button(button_frame, text="打印入库标", command=print_tag)
print_button.pack(side="left", padx=5)


submit_record_button = Button(button_frame, text="提交入库记录", command=upload_data)
submit_record_button.pack(side="left", padx=5)


def update_frame():
    """更新摄像头画面"""
    ret, frame = cap.read()  
    if ret:
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        label.imgtk = imgtk
        label.configure(image=imgtk)
    
    root.after(30, update_frame)

update_frame()


root.mainloop()
