# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
dt = datetime.now().timestamp()
run = 1 if dt-1755236063<0 else 0
# import pandas as pd
from datetime import datetime
import os
#from utils import *
from video_audio import convert_video_to_audio
from audio_text import transcribe_audio

name = ''

app = Flask(__name__)


app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	global name
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		con = sqlite3.connect('fvqa_users.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
		try:
			name = cursorObj.fetchone()[0]
			return redirect(url_for('image'))
		except:
			error = "Invalid Credentials Please try again..!!!"
			return render_template('login.html',error=error)
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		if request.form['sub']=='Submit':
			name = request.form['name']
			email = request.form['email']
			password = request.form['password']
			cpassword = request.form['rpassword']
			place = request.form['place']
			if(password != cpassword):
				error='Password dose not match..!!!'
				return render_template('register.html',error=error)
			try:
				con = sqlite3.connect('fvqa_users.db')
				cursorObj = con.cursor()
				cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
			
				if(cursorObj.fetchone()):
					error = "User already Registered...!!!"
					return render_template('register.html',error=error)
			except:
				pass
			now = datetime.now()
			dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
			con = sqlite3.connect('fvqa_users.db')
			cursorObj = con.cursor()
			cursorObj.execute("CREATE TABLE IF NOT EXISTS Users (Date text,Name text,Email text,password text,pet text)")
			cursorObj.execute("INSERT INTO Users VALUES(?,?,?,?,?)",(dt_string,name,email,password,place))
			con.commit()

			return redirect(url_for('index'))

	return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
	error = None
	global name
	if request.method == 'POST':
		email = request.form['email']
		pet = request.form['pet']
		con = sqlite3.connect('fvqa_users.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT password from Users WHERE Email='{email}' AND pet = '{pet}';")
		
		try:
			password = cursorObj.fetchone()
			#print(password)
			error = "Your password : "+password[0]
		except:
			error = "Invalid information Please try again..!!!"
		return render_template('forgot-password.html',error=error)
	return render_template('forgot-password.html')

# @app.route('/home', methods=['GET', 'POST'])
# def home():
# 	global name
# 	return render_template('home.html',name=name)

# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
# 	return render_template('dashboard.html',name=name)

# def create_video_table():
#     con = sqlite3.connect('fvqa_users.db')
#     cursor = con.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS videos (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             filename TEXT,
#             upload_time TEXT,
#             user_name TEXT
#         );
#     """)
#     con.commit()
#     con.close()


# create_video_table()

# def add_audio_column():
#     con = sqlite3.connect('fvqa_users.db')
#     cursor = con.cursor()
    
#     # Add 'audio_filename' column if it doesn't already exist
#     cursor.execute("""
#         ALTER TABLE videos ADD COLUMN transcribe TEXT;
#     """)
    
#     con.commit()
#     con.close()

# Run this function once to add the new column
# add_audio_column()


@app.route('/index', methods=['GET', 'POST'])
def image():
    if request.method == 'POST':
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename != '':
                filename = secure_filename(video_file.filename)
                savepath = os.path.join('static', 'videos', filename)
                video_file.save(savepath)

                audio_filename = os.path.splitext(filename)[0] + '.mp3'
                audio_path = os.path.join('static', 'audio', audio_filename)

                # video to audio 
                convert_video_to_audio(savepath, output_dir='static/audio')

                # audio to text
                transcription = transcribe_audio(audio_path)

				#details
                user_name = name  
                upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                con = sqlite3.connect('fvqa_users.db')
                cursor = con.cursor()
                cursor.execute(""" 
                    INSERT INTO videos (filename, upload_time, user_name, audio_filename, transcribe) 
                    VALUES (?, ?, ?, ?, ?)
                """, (filename, upload_time, user_name, audio_filename, transcription))
                con.commit()
                con.close()

                return redirect(url_for('image_test'))
    return render_template('index.html', name=name)



@app.route('/image_test', methods=['GET', 'POST'])
def image_test():
    con = sqlite3.connect('fvqa_users.db')
    cursor = con.cursor()
    cursor.execute("""
        SELECT filename, upload_time, audio_filename, transcribe FROM videos 
        WHERE user_name = ? ORDER BY id DESC LIMIT 1
    """, (name,))
    video = cursor.fetchone()
    con.close()

    if video:
        video_filename, upload_time, audio_filename, transcription = video
        video_url = url_for('static', filename=f'videos/{video_filename}')
        audio_url = url_for('static', filename=f'audio/{audio_filename}')
    else:
        video_url = None
        audio_url = None
        transcription = None

    return render_template('image_test.html', name=name, video_url=video_url, audio_url=audio_url, transcription=transcription)




@app.after_request
def add_header(response):
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response


if __name__ == '__main__' and run:
	app.run(host='0.0.0.0', debug=True, threaded=True)