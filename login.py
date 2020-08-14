from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from datetime import timedelta
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from datetime import datetime
from mongoengine import connect
import cv2
import face_recognition
import pickle

cnt = 0
 
app = Flask(__name__)
app.config["MONGO_URI"]="mongodb+srv://jiyulLee:sh032418@cluster0.tsie7.mongodb.net/faceid?retryWrites=true&w=majority"
app.config["PERMANENT_SESSION_LIFETIME"]=timedelta(minutes=30)
mongo=PyMongo(app)


@app.route("/join",methods=["GET","POST"])
def member_join():
    if request.method =="POST":
        name=request.form.get("name",type=str)
        email=request.form.get("email",type=str)
        pw=request.form.get("pw",type=str)
        
        if name=="" or email=="" or pw=="":
            flash("입력되지 않은 값이 있습니다!")
            return render_template("join.html")
        
        members=mongo.db.test
        cnt= members.find({"email" : email}).count()
        if cnt > 0:
            flash("중복된 id값이 있습니다!")
            return render_template("join.html")
        
        
        current_utc_time = round(datetime.utcnow().timestamp()*1000)
        post={
            "name":name,
            "email": email,
            "pw":pw,
            "joindate":current_utc_time,
            "logintime":"",
            "logincount":0
        }

        members.insert_one(post)
        
        return ""
   
    else:
       return render_template("join.html")


@app.route("/")
def index():
    return "<h5>Hi!</h5>"


@app.route("/login", methods=["GET","POST"])

def member_login():
   if request.method == "POST":
       email = request.form.get("email")
       pass1 = request.form.get("pw")
       
       members=mongo.db.test
       data= members.find_one({"email": email})
       print(email)

       if data is None:
           flash("회원 정보가 없습니다!!")
           return redirect(url_for("member_login"))
       else: 
           if data.get("pw") == pass1:
                session["email"]=email
                session["name"]=data.get("name")
                session.permanent = True

                # 2차 인증 - faceid
                encoding_file = 'encodings.pickle'
                def detectAndDisplay(frame):
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        boxes = face_recognition.face_locations(rgb, model="HOG")
                        encodings = face_recognition.face_encodings(rgb, boxes)
                        names = []

                        for encoding in encodings:
                            matches = face_recognition.compare_faces(data['encodings'], encoding, tolerance = 0.4)
                            name = 'unknown'

                            if True in matches:
                                matchedIndxs=[]
                                for (i,b) in enumerate(matches):
                                    if(b == True):
                                        matchedIndxs.append(i)

                                counts={}
                                for items in matchedIndxs:
                                    name = data['names'][items]
                                    counts[name]= 0
                                for items in matchedIndxs:
                                    counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                                name = max(counts, key=counts.get)
                                print()
                            names.append(name)

                        for ((top, right, bottom, left), name) in zip(boxes, names):
                            y = top-15
                            color=(255,255,0)
                            line = 1
                            if(name == 'unknown'):
                                color=(255,255,255)
                                line = 1
                                name = ''
                            cv2.rectangle(frame, (left,top), (right,bottom), color,line)
                            cv2.putText(frame, name, (left,y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, line)
                        
                        cv2.imshow('Recognition', frame)

                        
                        if(counts['suemin'] > 6):
                            print("it's suemin!")
                            global cnt
                            cnt += 1
                            print(cnt)

                            if(cnt == 5):
                                cap.release()
                                cv2.destroyAllWindows()
                                cnt = 0
                                return render_template("success.html")
                        else:
                            return flash("비밀번호가 일치하지 않습니다.")
                                                
                           
                data = pickle.loads(open(encoding_file, 'rb').read())

                cap = cv2.VideoCapture(0)
                   
                while True:
                    ret, frame = cap.read()
                    if frame is None:
                        print('No more captured frames!')
                        break
                    flipped = cv2.flip(frame, 1)
                    detectAndDisplay(flipped)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                cap.release()
                cv2.destroyAllWindows()
                #여기까지
                #return render_template("./success.html")
           else:
               flash("비밀번호가 일치하지 않습니다.")
               return redirect(url_for("member_login"))

   else:
       return render_template("./login.html")



       
#client를 특정하기 위해 쿠키같은 정보나 세션으로 서버에 저장해둠.
#저장된 데이터를 쿠키에 저장하는건 좀 취약하므로 세션이 훨씬 안정적임. but 부담이 큼


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host="0.0.0.0", debug=True, port=9000)
