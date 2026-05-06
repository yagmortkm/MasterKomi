from data import db_session
from flask import Flask, render_template, request, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy
import datetime
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/index')
def index():
    user = "Пользователь"
    if request.method == 'GET':
        return render_template('index.html', title='Главная страница', 
                           username=user)
    

class LoginForm(FlaskForm):
    username = StringField('Логин/Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect('/masterclasses')
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.name = form.username.data
        user.email = form.email.data
        user.hashed_password = generate_password_hash(form.password.data)
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        return redirect('/masterclasses')
    return render_template('registration.html', title='Регистрация', form=form)
    
@app.route('/masterclasses')
def main_window():
    user = "Пользователь"
    if request.method == 'GET':
        return render_template('masterclasses.html', title='Мастер-классы', 
                           username=user)

if __name__ == '__main__':
    db_session.global_init("db/users.db")
    app.run(port=8081, host='127.0.0.1')