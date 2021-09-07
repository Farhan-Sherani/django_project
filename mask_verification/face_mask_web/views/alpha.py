from django.http import HttpResponse
from django.http.response import StreamingHttpResponse
from .beta import VideoCamera
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import cv2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
import numpy as np
import argparse
import cv2
from tensorflow.keras.models import load_model
import os
import urllib.request

def index(request):
    return render(request,'index.html')

def about(request):
     input_img = request.GET.get('image', 'off')
     input_video=request.GET.get('video','off')
     if input_img!="off":
        return render(request,'image.html')
     elif input_video!="off":
        return render(request,'video.html')

def checked(request):
    context = {}
    check = request.POST.get('varify', 'off')
    file = request.POST.get('inpFile', 'off')
    if check!="off" and request.method=='POST':
        uploaded_photo=request.FILES['inpFile']
        fs=FileSystemStorage()
        name=fs.save(uploaded_photo.name,uploaded_photo)
        context['url']=fs.url(name) 
        # print("[INFO] loading face detector model...")
        prototxtPath ="media/deploy.prototxt"
        weightsPath = "media/res10_300x300_ssd_iter_140000.caffemodel"
        net = cv2.dnn.readNet(prototxtPath, weightsPath)
        model = load_model("media/mask_detector.model")
        # path = "http://127.0.0.1:8000/media/" + uploaded_photo.name
        #path = "https://farhan-777.github.io/django_project/mask_verification/media/" + uploaded_photo.name
        path = "http://34.131.0.142/django_project/mask_verification/media/" + uploaded_photo.name
	resp = urllib.request.urlopen(path)
        image = np.asarray(bytearray(resp.read()),dtype="uint8")
        image = cv2.imdecode(image,cv2. IMREAD_COLOR)
        orig = image.copy()
        (h,w) = image.shape[:2]
        # print(context['url'])
        blob = cv2.dnn.blobFromImage(image,1.0,(300,300),(104.0,177.0,123.0))
        # print("[INFO] computing face detection...")
        # print(django.urls.path())
        net.setInput(blob)
        detections = net.forward()
        for i in range(detections.shape[2]):
            confidence = detections[0,0,i,2]
            if confidence>0.5:
                box = detections[0,0,i,3:7]*np.array([w,h,w,h])
                (startX,startY,endX,endY) = box.astype("int")
                (startX,startY) = (max(0,startX),max(0,startY))
                (endX,endY) = (min(w-1,endX),min(h-1,endY))

                face = image[startY:endY,startX:endX]
                face = cv2.cvtColor(face,cv2.COLOR_BGR2RGB)
                face = cv2.resize(face,(224,224))
                face = img_to_array(face)
                face = preprocess_input(face)
                face = np.expand_dims(face,axis=0)

                (mask,withoutMask) = model.predict(face)[0]
                label = "Mask" if mask > withoutMask else "No Mask"
                color = (0,255,0) if label=="Mask" else (0,0,255)

                label = "{}: {:.2f}%".format(label,max(mask,withoutMask)*100)
                cv2.putText(image,label,(startX,startY-10),cv2.FONT_HERSHEY_SIMPLEX,0.45,color,2)
                cv2.rectangle(image,(startX,startY),(endX,endY),color,2)
        cv2.imwrite("media/OUTPUT.jpg",image) 
        context['output']="media/OUTPUT.jpg"
        os.remove("media/"+uploaded_photo.name)
        return render(request,'result.html',context)
    else:
        return HttpResponse("Checked off")




def gen(camera):
	while True:
		frame = camera.get_frame()
		yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
def video_feed(request):
	return StreamingHttpResponse(gen(VideoCamera()),
					content_type='multipart/x-mixed-replace; boundary=frame')
