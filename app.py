from flask import Flask,flash,redirect,request,url_for,render_template,session,send_file
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from mail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
app=Flask(__name__)
app.secret_key='876@#^%jh'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='application'
Session(app)
mysql=MySQL(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registration',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        gender=request.form['gender']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from details')
        data=cursor.fetchall()
        cursor.execute('SELECT email from details')
        edata=cursor.fetchall()
        if (email,) in edata:
            flash('Email id already exists')
            return render_template('register.html')
        cursor.close()
        otp=genotp()
        sendmail(email,otp)
        return render_template('otp.html',otp=otp,name=name,email=email,password=password,gender=gender)
        return otp
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        print(request.form)
        name=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from details where name=%s and password=%s',[name,password])
        count=cursor.fetchone()[0]
        if count==0:
            print(count)
            flash('Invalid username or password')
            return render_template('login.html')
        else:
            session['user']=name
            return redirect(url_for('home'))
    return render_template('login.html')
@app.route('/home',methods=['GET','POST'])
def home():
    cursor=mysql.connection.cursor()
    cursor.execute('select * from blogs')
    data=cursor.fetchall()
    cursor.close()
    return render_template('home.html',data=data)
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash('already logged out')
        return redirect(url_for('login'))
def register():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash('already logged out')
        return redirect(url_for('login'))
@app.route('/otp/<otp>/<name>/<email>/<password>/<gender>',methods=['GET','POST'])
def otp(otp,name,password,email,gender):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            query='insert into details values(%s,%s,%s,%s)'
            cursor.execute(query, [name,email,password,gender])
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,name=name,email=email,password=password,gender=gender)
@app.route('/blogview',methods=['GET','POST'])
def blogview2():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            Categories= request.form['Categories']
            cursor=mysql.connection.cursor()
            name=session.get('user')
            cursor.execute('insert into blogs(name,title,description,Categories) values(%s,%s,%s,%s)',[name,title,description,Categories])
            mysql.connection.commit()
            cursor.close()
            flash(f'{title} added successfully')
            return redirect(url_for('home'))
        return render_template('blogview.html')
    else:
        return redirect(url_for('login'))
@app.route('/edit/<blogid>',methods=['GET','POST'])
def edit(blogid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select title,description,Categories from blogs where blogid=%s',[blogid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            Categories=request.form['Categories']
            cursor=mysql.connection.cursor()
            cursor.execute('update blogs set title=%s,description=%s,Categories=%s where blogid=%s',[title,description,Categories,blogid])
            mysql.connection.commit()
            cursor.close()
            flash('Blog edited successfully')
            return redirect(url_for('home')) 
        return render_template('edit.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/delete/<blogid>')
def delete(blogid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from blogs where blogid=%s',[blogid])
    mysql.connection.commit()
    cursor.close()
    flash(' Blog deleted successfully')
    return redirect(url_for('home'))
@app.route('/viewmore/<blogid>')
def viewmore(blogid):
    cursor=mysql.connection.cursor()
    cursor.execute('select title,description from blogs where blogid=%s',[blogid])
    data=cursor.fetchone()
    cursor.close()
    return render_template('viewmore.html',data=data)
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        name=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from details')
        data=cursor.fetchall()
        if (name,) in data:
            cursor.execute('select email from details where name=%s',[name])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using-{request.host+url_for("createpassword",token=token(name,120))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid username'
    return render_template('forget.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        name=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update details set password=%s where name=%s',[npass,name])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except:
        return 'Link expired try again'
app.run(debug=True,use_reloader=True)
