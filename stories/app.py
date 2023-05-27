import os
from flask import Flask,render_template,redirect,url_for,request,session,flash,send_from_directory
from flask_mysqldb import MySQL

from passlib.hash import pbkdf2_sha256
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mykey'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USERNAME'] =  'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hadithi'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}

mysql = MySQL(app)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to sign in or sign up first.")
            return redirect(url_for('signin'))
    return wrap



@app.route('/')
def index():

    return render_template('index.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = pbkdf2_sha256.hash(str(request.form['password']))
        cur = mysql.connection.cursor()
        existing_name = cur.execute("SELECT * FROM users WHERE name = %s",[name])
        existing_email = cur.execute("SELECT * FROM users WHERE email = %s",[email])
        if existing_name > 0:
            flash("The name already exists!Please choose another",category='info')
            return render_template('signup.html')
        if existing_email > 0:
            flash("The Email used is already registered!")
            return render_template('signup.html')
        cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",(name,email,password))
        mysql.connection.commit()
        cur.close()
        flash("Registration Success!.Please Sign In.",category="info")
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin',methods=['GET','POST'])
def signin():
    if request.method == 'POST':
        name = request.form['name']
        password_entered = request.form['password']
        cur = mysql.connection.cursor()
        user = cur.execute("SELECT * FROM users WHERE name = %s",[name])
        if user > 0:
            data = cur.fetchone()
            real_password = data['password']
            name = data['name']
            user_id = data['user_id']

            if pbkdf2_sha256.verify(password_entered,real_password):
                session['logged_in'] = True
                session['name'] = name
                session['user_id'] = user_id
                flash('Sign In Successful!',category='info')
                return redirect(url_for('index'))
            else:
                flash('Details Incorrect!Please try again.',category='error')
                return render_template('signin.html')
        else:
            flash('User does not exist!Please Register.',category='error')
            return redirect(url_for('signup'))
        
    return render_template('signin.html')

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/write_story',methods=['GET','POST'])
def write_story():
    if request.method == 'POST':
        target = os.path.join(APP_ROOT,'static/')
        title = request.form['title']
        category = request.form['category']
        body = request.form['body']

        picture = request.files['image']
        img_name = picture.filename
        destination = '/'.join([target,img_name])
        picture.save(destination)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO stories(title,category,body,picture) VALUES(%s,%s,%s,%s)",(title,category,body,img_name))
        mysql.connection.commit()
        flash("Story Added Successfuly!", category='info')
        cur.close()
    return render_template('write_story.html')

@app.route('/stories',methods=['GET','POST'])
def stories():
    if request.method == 'POST':
        genre = request.form['category']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM stories WHERE category = %s",[genre])
        stories = cur.fetchall()
        cur.close()
        if stories == '':
            flash("No stories available!",category='info')
        return render_template('stories.html',stories=stories)
    else:
        print("No error")
    return render_template('stories.html')
    

@app.route('/single_story/<string:id>/')
def single_story(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM stories WHERE story_id = %s",[id])
    story = cur.fetchone()
    return render_template('single_story.html',story=story)
 
    
    


@app.route('/profile/<string:user_id>')
@login_required
def profile(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=%s",[user_id])
    info = cur.fetchone()
    return render_template('profile.html',info=info)

@app.route('/edit_profile/<string:user_id>',methods=['GET','POST'])
@login_required
def edit_profile(user_id):
    cur  = mysql.connection.cursor()
    cur.execute("SELECT name,email FROM users WHERE user_id = %s",[user_id])
    profileData = cur.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        profile_pic = request.files['profile_pic']
        bio = request.form['bio']

        target = os.path.join(APP_ROOT,'static/')
        img_name = profile_pic.filename
        destination = '/'.join([target,img_name])
        profile_pic.save(destination)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET name = %s, email = %s, profile_pic = %s, bio = %s WHERE user_id = %s",(name,email,img_name,bio,user_id))
        mysql.connection.commit()
        cur.close()
        flash("Success!",category="info")
        return redirect(url_for('index'))
    return render_template('edit_profile.html',profileData=profileData)

@app.route('/delete_account/<string:user_id>')
@login_required
def delete_account(user_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s",[user_id])
    mysql.connection.commit()
    cur.close()
    session.clear()
    flash("Your account has been Deleted!!")
    return redirect(url_for('index'))    


if __name__ == "__main__":
    app.run(debug=True)