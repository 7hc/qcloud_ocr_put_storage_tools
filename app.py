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
    # 按 ASCII 升序进行排序
    headersArray = dict(sorted(headersArray.items(), key=lambda x: x[0]))
    sortHeadersArray = headersArray
    
    SignedHeaders = ""
    CanonicalHeaders = ""
    
    # 拼接键
    for key in list(sortHeadersArray.keys()):
        SignedHeaders += key.lower() + ";"
    if SignedHeaders[-1] == ";":
        SignedHeaders = SignedHeaders[:-1]
    
    # 拼接键
    for key in list(sortHeadersArray.keys()):
        CanonicalHeaders += key.lower() + ":" + sortHeadersArray[key].lower() + "\n"
    
    
    HashedRequestPayload = hashlib.sha256(bytes(json.dumps(bodyArray),encoding="utf-8")).hexdigest()
    

    CanonicalRequest = HTTPRequestMethod + "\n" + CanonicalURI + "\n" + CanonicalQueryString + "\n" + CanonicalHeaders + "\n" + SignedHeaders + "\n" + HashedRequestPayload
    
    
    # 时间戳
    RequestTimestamp = str(int(time.time()))
    # 获取年月日
    formattedDate = time.strftime("%Y-%m-%d", time.gmtime(int(RequestTimestamp)))
    Algorithm = "TC3-HMAC-SHA256"
    CredentialScope = formattedDate + "/" + Service + "/tc3_request"
    HashedCanonicalRequest = hashlib.sha256(bytes(CanonicalRequest,encoding="utf-8")).hexdigest()
    
    # ------
    
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

SecretId = ""
SecretKey = ""

template = {
    "制造商零件编号(MPN)":"MPN",
    "描述(DESC)":"DESC",
    "制造商(MFG)":"MFG",
    "原产地(CoO)":"COO",
    "销售订单号(SO)":"SO",
    "数量(QTY)":"QTY",
    "库位(LOC)":"LOC",
    "LPN":"LPN",
    "LPN总数":"LPN_Count",
    "DO":"DO"
}

kv_joint__list = ["DO"]

# 初始化摄像头
cap = cv2.VideoCapture(0)

# 创建主窗口
root = Tk()
root.title("OCR入库辅助工具")
root.geometry("1000x400")

# 创建一个Label用于显示摄像头画面
label = Label(root, width=450)
label.pack(side="left", fill="both", expand=True, padx=10, pady=10)  # 将Label放在窗口左侧

# 创建右侧框架
right_frame = Label(root)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# 在右侧框架添加表单标题
Label(right_frame, text="物料OCR结果").pack()

# 创建一个表单框架来组织标签和输入框
form_frame = Frame(right_frame)
form_frame.pack()

# 定义一个函数来创建标签和输入框对
def create_label_entry(parent, label_text,value):
    frame = Frame(parent)
    frame.pack(anchor="w", fill="x", pady=(0, 5))
    Label(frame, text=label_text, anchor="e", width=20).pack(side="left")
    Entry(frame, textvariable=value).pack(side="left", fill="x", expand=True)

kv_dict = {}

for i in template.keys():
    kv_dict[template[i]] = ""

# 初始化 StringVar 对象并设置初始值（都是空字符串）
vars_dict = {field: StringVar(value="") for field in kv_dict}

# 创建姓名标签和输入框
for la in template.keys():
    create_label_entry(form_frame, la, vars_dict[template[la]])

# 创建一个Button用于拍摄
def take_photo():
    image_filename = str(int(time.time()*1000)) + ".jpg"
    ret, frame = cap.read()  # 读取摄像头的一帧
    if ret:
        # 将OpenCV的BGR格式转换为RGB格式
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 使用PIL将图像转换为PhotoImage对象
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        # 更新Label显示的图片
        label.imgtk = imgtk
        label.configure(image=imgtk)
        # 保存图片到文件
        cv2.imwrite(image_filename, frame)
        return image_filename
    else:
        return None

def ocr(file_name:str):
    global template,SecretId,SecretKey

    with open(file_name, "rb") as f:
        image_data = f.read()
    data = {
        "ImageBase64": base64.b64encode(image_data).decode(),
        "EnableCoord": False,
        "ConfigId": "General",
        "ItemNames": list(template.keys()),
    }
    host = "ocr.tencentcloudapi.com"
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

def format_d(dat):
    global kv_joint__list, kv_dict
    li = dat["Response"]["StructuralList"]
    for ii in li:
        ke = ii["Groups"][0]["Lines"][0]["Key"]["AutoName"]
        va = ii["Groups"][0]["Lines"][0]["Value"]["AutoContent"]
        if ke in kv_joint__list:
            va = ke + va
        vars_dict[template[ke]].set(va)
    
    # 使用字典推导式从 StringVar 对象获取值并更新 kv_dict
    kv_dict = {key: var.get() for key, var in vars_dict.items()}
    print(kv_dict)

def try_ocr():
    filename = take_photo()
    if not filename:
        return
    print("-> 图片保存成功")
    print(ocr(filename))
    with open("k.json","r",encoding="utf-8") as f:
        format_d(json.load(f))

def upload_data():
    global kv_dict
    # 使用字典推导式从 StringVar 对象获取值并更新 kv_dict
    kv_dict = {key: var.get() for key, var in vars_dict.items()}

    print(kv_dict)

    # 这里对接的接口

def print_tag():
    global kv_dict
    # 这里对接的接口
    tag_id = "xxxxxx"
    kv_dict["tag_id"] = tag_id

# 提交按钮
# 创建一个按钮框架
button_frame = Frame(right_frame)
button_frame.pack(pady=10)

# 提交按钮
submit_button = Button(button_frame, text="OCR", command=try_ocr)
submit_button.pack(side="left", padx=5)

# 打印入库标按钮
print_button = Button(button_frame, text="打印入库标", command=print_tag)
print_button.pack(side="left", padx=5)

# 提交入库记录按钮
submit_record_button = Button(button_frame, text="提交入库记录", command=upload_data)
submit_record_button.pack(side="left", padx=5)

# 定义更新摄像头画面的函数
def update_frame():
    """更新摄像头画面"""
    ret, frame = cap.read()  # 读取摄像头的一帧
    if ret:
        # 将OpenCV的BGR格式转换为RGB格式
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 使用PIL将图像转换为PhotoImage对象
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        # 更新Label显示的图片
        label.imgtk = imgtk
        label.configure(image=imgtk)
    # 每隔30毫秒调用一次update_frame函数，实现实时更新
    root.after(30, update_frame)

update_frame()

# 运行主循环
root.mainloop()
