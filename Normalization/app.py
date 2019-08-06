from flask import Flask, render_template, redirect,url_for, request,flash, send_file
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField
import pandas as pd
import numpy as np
from flask_mail import Mail
from flask_mail import Message
import os
import base64
import time
UPLOAD_FOLDER = '/tmp/' + 'media/upload_folder'
os.mkdir('/tmp/media')
os.mkdir('/tmp/media/upload_folder')

app = Flask(__name__)
app.config['SECRET_KEY']='pass'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# mail setup
app.config['MAIL_SERVER'] = 'mail.privateemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'admin@mltool.in'
app.config['MAIL_PASSWORD'] = 'fzcrysngzcf'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False  
mail = Mail(app)
sender = ('NormalizationMarks Server | MLTool Admin', 'admin@mltool.in')
cc =  ["mukulverma855@gmail.com","dawarmuskan21@gmail.com", "robomex2020@gmail.com"]

ALLOWED_EXTENSIONS = set(['xlsx'])
class Form(FlaskForm):
    file=FileField('Upload your xlsx file')
    submit=SubmitField('submit')

import boto3
s3 = boto3.resource('s3')
BUCKET_NAME = 'normalization-mltool'

@app.route('/',methods=['GET', 'POST'])
def index():
    form=Form()
    FinalMarks = []
    RollNo=[]
    Name=[]
    marks=[]

    if form.validate_on_submit():
        
        user_id = int(time.time())

        file=form.file.data
        
        input_file = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id) + '/data.xlsx')

        os.mkdir(UPLOAD_FOLDER + "/" + str(user_id))

        file.save(input_file)
        try:
            df = pd.read_excel(input_file)
        except:
            flash("Input file is not supported. Send a mail to admin@mltool.in", 'error')
            return redirect(url_for('index'))

        x = df['Group'].tolist()

        x = set(x)
        mean=[]
        std=[]

        for i in x:
            mean.append(np.mean(df[df.Group == i][['Mark']]))
            std.append(np.std(df[df.Group == i][['Mark']]))


        avg=np.mean(mean)
        sd=np.mean(std)

        x=list(x)

        dict_mean = dict()

        for i,j in enumerate(mean):
            dict_mean[x[i]]=j 

        dict_sd = dict()

        for i,j in enumerate(std):
            dict_sd[x[i]]=j 

        marks = df['Mark'].tolist()
        group = df['Group'].tolist()
        RollNo = df['RollNo'].tolist()
        Name = df['Name'].tolist()


        norm=list()

        for i,j in enumerate(group):
            norm.append((marks[i]-dict_mean[j])/dict_sd[j])

        NormalizedMarks = list()

        for i in norm:
            NormalizedMarks.append((sd*i)+avg)


        FinalMarks = list()

        for i in NormalizedMarks:
            FinalMarks.append(round(i,0))


        FinalMarks = pd.DataFrame(FinalMarks) 

        FinalMarks = FinalMarks['Mark'].tolist()

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id) + '/Marks.csv')
        writefp = open(file_path, 'w')

        writefp.write('RollNo'+','+'Name'+','+'Original Marks'+','+'Group'+','+'Final Marks'+'\n')
        for i,j in enumerate(FinalMarks):
            writefp.write(str(RollNo[i])+','+str(Name[i])+','+str(marks[i])+','+str(group[i])+','+str(j)+'\n')
        writefp.close()

        msg = Message("Normalized marks result",
                  sender=sender,
                  cc=cc,
                  recipients=[request.form.get("to_email"),])
        msg.html = """
                   Dear Sir/Ma\'am<br/><br/>Your result is ready. Check it out in attached file.
                   <br/><br/Regards,<br/>MLTool Admin | NormalizationMarks Server
                   """


        with open(file_path, 'rb') as fp:
            msg.attach(
            'output.csv',
            'text/csv',
            fp.read())
        try:
            mail.send(msg)
            flash("Email sent successfully! Don't forget the spam folder", 'success')
            return redirect(url_for('index'))
        except:
            flash("Your file coudn't be processed. Send a mail to admin@mltool.in", 'error')
            return redirect(url_for('index'))
    return render_template('index.html',form=form)

@app.errorhandler(404)
def page_not_found(e):
            flash("Page not found", 'error')
            return redirect(url_for('index'))

@app.route('/download')
def download():

    path = "static/data.xlsx"
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
  app.run(debug=True)
 
