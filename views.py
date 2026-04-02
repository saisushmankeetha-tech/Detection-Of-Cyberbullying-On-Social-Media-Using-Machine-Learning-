from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import pymysql
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
from sklearn.externals import joblib
import random
from datetime import date

from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from string import punctuation
from nltk.corpus import stopwords
import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd
import pickle
from nltk.stem import PorterStemmer
from sklearn.ensemble import AdaBoostClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
import matplotlib.pyplot as plt

load_index = 0
global svm_classifier, user_status, sgd
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
ps = PorterStemmer()

accuracy = []
precision = []
recall = []
fscore = []

#functions to calculate accuracy, confusion matrix and other metrics 
def calculateMetrics(predict, y_test):
    a = accuracy_score(y_test,predict)*100
    p = precision_score(y_test, predict,average='macro') * 100
    r = recall_score(y_test, predict,average='macro') * 100
    f = f1_score(y_test, predict,average='macro') * 100
    accuracy.append(a)
    precision.append(p)
    recall.append(r)
    fscore.append(f)
    

def cleanPost(doc):
    tokens = doc.split()
    table = str.maketrans('', '', punctuation)
    tokens = [w.translate(table) for w in tokens]
    tokens = [word for word in tokens if word.isalpha()]
    tokens = [w for w in tokens if not w in stop_words]
    tokens = [word for word in tokens if len(word) > 1]
    tokens = [ps.stem(token) for token in tokens]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    tokens = ' '.join(tokens)
    return tokens

with open('model/vector.txt', 'rb') as file:
    vectorizer = pickle.load(file)
file.close()
X = np.load("model/X.npy")
Y = np.load("model/Y.npy")

indices = np.arange(X.shape[0])
np.random.shuffle(indices)
X = X[indices]
Y = Y[indices]
print(X)
print(Y)
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)

if os.path.exists('model/ada.txt'):
    with open('model/ada.txt', 'rb') as file:
        ab = pickle.load(file)
    file.close()
else:
    ab = AdaBoostClassifier()
    ab.fit(X_train, y_train)
    with open('model/ada.txt', 'wb') as file:
        pickle.dump(ab, file)
    file.close()
predict = ab.predict(X_test)
calculateMetrics(predict, y_test)

if os.path.exists('model/sgd.txt'):
    with open('model/sgd.txt', 'rb') as file:
        sgd = pickle.load(file)
    file.close()
else:
    sgd = SGDClassifier()
    sgd.fit(X_train, y_train)
    with open('model/sgd.txt', 'wb') as file:
        pickle.dump(sgd, file)
    file.close()
predict = sgd.predict(X_test)
calculateMetrics(predict, y_test)

if os.path.exists('model/nb.txt'):
    with open('model/nb.txt', 'rb') as file:
        nb = pickle.load(file)
    file.close()
else:
    nb = MultinomialNB()
    nb.fit(X_train, y_train)
    with open('model/nb.txt', 'wb') as file:
        pickle.dump(nb, file)
    file.close()
predict = nb.predict(X_test)
calculateMetrics(predict, y_test)

def TrainML(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Algorithm Name</font></th>'
        output+='<th><font size=3 color=black>Accuracy</font></th>'
        output+='<th><font size=3 color=black>Precision</font></th>'
        output+='<th><font size=3 color=black>Recall</font></th>'
        output+='<th><font size=3 color=black>F1 Score</font></th></tr>'
        algorithms = ['AdaBoost', 'SGD', 'Multinomial Naive Bayes']
        for i in range(len(accuracy)):
            output+='<tr><td><font size=3 color=black>'+algorithms[i]+'</font></td>'
            output+='<td><font size=3 color=black>'+str(accuracy[i])+'</font></td>'
            output+='<td><font size=3 color=black>'+str(precision[i])+'</font></td>'
            output+='<td><font size=3 color=black>'+str(recall[i])+'</font></td>'
            output+='<td><font size=3 color=black>'+str(fscore[i])+'</font></td>'
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        df = pd.DataFrame([['AdaBoost','Precision',precision[0]],['AdaBoost','Recall',recall[0]],['AdaBoost','F1 Score',fscore[0]],['AdaBoost','Accuracy',accuracy[0]],
                   ['SGD','Precision',precision[1]],['SGD','Recall',recall[1]],['SGD','F1 Score',fscore[1]],['SGD','Accuracy',accuracy[1]],
                   ['Multinomial Naive Bayes','Precision',precision[2]],['Multinomial Naive Bayes','Recall',recall[2]],['Multinomial Naive Bayes','F1 Score',fscore[2]],['Multinomial Naive Bayes','Accuracy',accuracy[2]],
                  ],columns=['Algorithms','Performance Output','Value'])
        df.pivot("Algorithms", "Performance Output", "Value").plot(kind='bar')
        plt.show()
        return render(request, 'AdminScreen.html', context)
    

def getOffensiveCount(username):
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
    count = 0
    with con:
        cur = con.cursor()
        cur.execute("select offensive_count FROM userstatus where username='"+username+"'")
        rows = cur.fetchall()
        for row in rows:
            count = row[0]
    return count        

def updateStatus(user):
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
    count = 0
    with con:
        cur = con.cursor()
        cur.execute("select offensive_count FROM userstatus where username='"+user+"'")
        rows = cur.fetchall()
        for row in rows:
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "update userstatus set offensive_count=offensive_count+1 where username='"+user+"'"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            count = 1
    if count == 0:
        count = 1
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO userstatus(username,offensive_count) VALUES('"+user+"','"+str(count)+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()

def getMessageType(description, user, sentiment):
    global ab, vectorizer
    msg = []
    msg.append(cleanPost(description))
    test = vectorizer.transform(msg).toarray()
    predict = ab.predict(test)[0]
    if sentiment == 'Positive' and predict == 1:
        predict = 0
    print("predict "+str(predict))
    msg_type = "Non-Offensive"
    if predict == 1:
        msg_type = "Offensive"
        updateStatus(user)
    return msg_type

def AdminLogin(request):
    if request.method == 'GET':
       return render(request, 'AdminLogin.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def ChangePassword(request):
    if request.method == 'GET':
       return render(request, 'ChangePassword.html', {})

def PostTopic(request):
    if request.method == 'GET':
       return render(request, 'PostTopic.html', {})

def getPostData():
    output = '<table border=1 align=center>'
    output+='<tr><th><font size=3 color=black>Username</font></th>'
    output+='<th><font size=3 color=black>Message ID</font></th>'
    output+='<th><font size=3 color=black>Message</font></th>'
    output+='<th><font size=3 color=black>Image</font></th>'
    output+='<th><font size=3 color=black>Message Sentiment</font></th>'
    output+='<th><font size=3 color=black>Message Type</font></th>'
    output+='<th><font size=3 color=black>Message Date</font></th></tr>'
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * FROM post")
        rows = cur.fetchall()
        for row in rows:
            username = row[0]
            post_id = str(row[1])
            message = row[2]
            image_name = row[3]
            sentiment = row[4]
            message_type = row[5]
            msg_date = row[6]
            output+='<tr><td><font size=3 color=black>'+username+'</font></td>'
            output+='<td><font size=3 color=black>'+str(post_id)+'</font></td>'
            output+='<td><font size=3 color=black>'+message+'</font></td>'
            output+='<td><img src=/static/post/'+str(post_id)+'.png width=200 height=200></img></td>'
            output+='<td><font size=3 color=black>'+sentiment+'</font></td>'
            output+='<td><font size=3 color=black>'+message_type+'</font></td>'
            output+='<td><font size=3 color=black>'+msg_date+'</font></td></tr>'
    output+="</table><br/><br/><br/><br/><br/><br/>"
    return output    

def BlockUser(request):
    if request.method == 'GET':
         bid = request.GET['id']
         db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
         db_cursor = db_connection.cursor()
         student_sql_query = "update register set status='Blocked' where username='"+bid+"'"
         db_cursor.execute(student_sql_query)
         db_connection.commit()
         #output+="</table><br/><br/><br/><br/><br/><br/>"
         context= {'data':'<font size="3" color="red"><center>selected '+bid+' permanently blocked</center></font>'}
         return render(request, 'AdminScreen.html', context)
         

def ViewOffensive(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Username</font></th>'
        output+='<th><font size=3 color=black>Password</font></th>'
        output+='<th><font size=3 color=black>Contact</font></th>'
        output+='<th><font size=3 color=black>Email</font></th>'
        output+='<th><font size=3 color=black>Address</font></th>'
        output+='<th><font size=3 color=black>Status</font></th>'
        output+='<th><font size=3 color=black>Profile Photo</font></th>'
        output+='<th><font size=3 color=black>Offensive Count</font></th>'
        output+='<th><font size=3 color=black>Blocked User</font></th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                username = row[0]
                password = str(row[1])
                contact = row[2]
                email = row[3]
                address = row[4]
                status = row[5]
                if status == 'none':
                    status = "Active"
                else:
                    status = "Blocked"
                count = getOffensiveCount(username)    
                output+='<tr><td><font size=3 color=black>'+username+'</font></td>'
                output+='<td><font size=3 color=black>'+password+'</font></td>'
                output+='<td><font size=3 color=black>'+contact+'</font></td>'
                output+='<td><font size=3 color=black>'+email+'</font></td>'
                output+='<td><font size=3 color=black>'+address+'</font></td>'
                output+='<td><font size=3 color=black>'+status+'</font></td>'
                output+='<td><img src=/static/profiles/'+username+'.png width=200 height=200></img></td>'
                output+='<td><font size=3 color=black>'+str(count)+'</font></td>'
                if count < 2:
                    output+='<td><font size=3 color=black>No Offensive Post Fount</font></td>'
                else:
                    output+='<td><a href=\'BlockUser?id='+username+'\'><font size=3 color=black>Click Here to Block</font></a></td></tr>'
                
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'AdminScreen.html', context)
    

def PostMyTopic(request):
    if request.method == 'POST':
        global load_index, svm_classifier
        description = request.POST.get('description', False)
        myfile = request.FILES['image']
        imagename = request.FILES['image'].name
        user = ''
        with open("session.txt", "r") as file:
            for line in file:
                user = line.strip('\n')
        counts = 0
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select max(msg_id) FROM post")
            rows = cur.fetchall()
            for row in rows:
                counts = row[0]
        if counts != None:
            counts = int(str(counts)) + 1        
        else:
            counts = 1
        if load_index == 0:
            svm_classifier = joblib.load('model/svmClassifier.pkl')
            load_index = 1
        X =  [description]
        svm_sentiment = svm_classifier.predict(X)
        senti = svm_sentiment[0]
        print(senti)
        sentiment = "Positive"
        if senti == 0:
            sentiment = "Negative"
        msg_type = getMessageType(description, user, sentiment)
        if sentiment == 'Negative' and msg_type == 'Non-Offensive':
            msg_type = "Offensive"
            updateStatus(user)
        fs = FileSystemStorage()
        filename = fs.save('CyberbullyingApp/static/post/'+str(counts)+'.png', myfile)
        today = str(date.today())
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO post(username,msg_id,message,image_name,sentiment,message_type,msg_date) VALUES('"+user+"','"+str(counts)+"','"+description+"','"+imagename+"','"+sentiment+"','"+msg_type+"','"+today+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        print(db_cursor.rowcount, "Record Inserted")
        status_data = ''
        if db_cursor.rowcount == 1:
            con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("select * FROM register")
                rows = cur.fetchall()
                for row in rows:
                    if row[0] == user:
                        status_data = row[5]
                        break
            if status_data == 'none':
                status_data = 'Active'
                user_status = 'Active'
            else:
                status_data = "Blocked"
                user_status = "Blocked"
            if msg_type != "Non-Offensive":
                status_data += "<br/>Your are using Offensive words. Admin will review & block you"
            output = ''
            output+='<table border=0 align=center width=100%><tr><td><img src=/static/profiles/'+user+'.png width=200 height=200></img></td>'
            output+='<td><font size=3 color=black>'+status_data+'</font></td><td><font size=3 color=black>welcome : '+user+'</font></td></tr></table></br></br>'
            output+=getPostData()                   
            context= {'data':output}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'Error in post topic'}
            return render(request, 'PostTopic.html', context)
    
def Signup(request):
    if request.method == 'POST':
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      myfile = request.FILES['image']

      fs = FileSystemStorage()
      filename = fs.save('CyberbullyingApp/static/profiles/'+username+'.png', myfile)
      
      db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
      db_cursor = db_connection.cursor()
      student_sql_query = "INSERT INTO register(username,password,contact,email,address,status) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"','none')"
      db_cursor.execute(student_sql_query)
      db_connection.commit()
      print(db_cursor.rowcount, "Record Inserted")
      if db_cursor.rowcount == 1:
       context= {'data':'Signup Process Completed'}
       return render(request, 'Register.html', context)
      else:
       context= {'data':'Error in signup process'}
       return render(request, 'Register.html', context)


def AdminLoginAction(request):
    if request.method == 'POST':
        global user_status
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        if username=='admin' and password=='admin':
            context= {'data':"Welcome "+username}
            return render(request, 'AdminScreen.html', context)
        else:
            context= {'data':'Invalid login details'}
            return render(request, 'AdminLogin.html', context)

def UserLogin(request):
    if request.method == 'POST':
        global user_status
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        status = 'none'
        status_data = ''
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'bullying',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and row[1] == password:
                    status = 'success'
                    status_data = row[5]
                    break
        if status_data == 'none':
            status_data = 'Active'
            user_status = 'Active'
        else:
            status_data = "Blocked"
            user_status = "Blocked"
        if status == 'success' and user_status == 'Active':
            file = open('session.txt','w')
            file.write(username)
            file.close()
            output = ''
            output+='<table border=0 align=center width=100%><tr><td><img src=/static/profiles/'+username+'.png width=200 height=200></img></td>'
            output+='<td><font size=3 color=black>'+status_data+'</font></td><td><font size=3 color=black>welcome : '+username+'</font></td></tr></table></br></br>'
            output+=getPostData()
            context= {'data':output}
            return render(request, 'UserScreen.html', context)
        if status == 'none' or status_data == 'Blocked':
            context= {'data':'Invalid login details or your account blocked by admin'}
            return render(request, 'Login.html', context)





        
            
