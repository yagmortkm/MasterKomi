from data import db_session
from flask import Flask, render_template, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from data.users import User
from data.events import Event
from data.event_signups import EventSignup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.template_filter('fmt_date')
def fmt_date(value):
    if not value:
        return '—'
    if hasattr(value, 'strftime'):
        return value.strftime('%d.%m.%Y')
    return str(value)


def current_user_name():
    return session.get('user_name', '')


@app.route('/')
@app.route('/index')
def index():
    user = current_user_name() or 'гость'
    return render_template('index.html', title='Главная страница', username=user)


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


class MasterclassForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    date = StringField('Дата', validators=[DataRequired()])
    time = StringField('Время', validators=[DataRequired()])
    location = StringField('Место', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    price = StringField('Цена', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class EventSignupForm(FlaskForm):
    submit = SubmitField('Записаться')


class CancelFrom(FlaskForm):
    pass


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('masterclasses'))
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        login_value = form.username.data.strip()
        user = db_sess.query(User).filter(
            (User.name == login_value) | (User.email == login_value)
        ).first()
        if user and user.hashed_password and check_password_hash(user.hashed_password, form.password.data):
            session['user_id'] = user.id
            session['user_name'] = user.name or user.email
            return redirect(url_for('masterclasses'))
        return render_template('login.html', title='Авторизация', form=form,
                               message='Неверный логин или пароль')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if session.get('user_id'):
        return render_template('registration.html', title='Регистрация',
                               form=RegistrationForm(), message='Вы уже вошли в аккаунт')
    form = RegistrationForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html', title='Регистрация', form=form,
                                   message='Такой email уже существует')
        if db_sess.query(User).filter(User.name == form.username.data).first():
            return render_template('registration.html', title='Регистрация', form=form,
                                   message='Такой пользователь уже существует')
        if form.password.data != form.password_again.data:
            return render_template('registration.html', title='Регистрация', form=form,
                                   message='Пароли не совпадают')
        user = User()
        user.name = form.username.data
        user.email = form.email.data
        user.hashed_password = generate_password_hash(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        session['user_id'] = user.id
        session['user_name'] = user.name
        return redirect(url_for('masterclasses'))
    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    db_sess = db_session.create_session()
    user = db_sess.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    my_events = (db_sess.query(Event).filter(Event.user_id == user.id).order_by(Event.created_date.desc()).all())
    my_signups = (db_sess.query(EventSignup).filter(EventSignup.user_id == user.id).order_by(EventSignup.created_date.desc()).all())
    cancel_signup_forms = {s.event_id: CancelFrom(prefix=f'c{s.event_id}') for s in my_signups}
    return render_template('profile.html', title='Профиль', user=user, my_events=my_events, my_signups=my_signups, cancel_signup_forms=cancel_signup_forms)


@app.route('/masterclasses')
def masterclasses():
    db_sess = db_session.create_session()
    items = db_sess.query(Event).order_by(Event.created_date.desc()).all()
    user_id = session.get('user_id')
    signed_ids = set()
    if user_id:
        signed_ids = {r[0] for r in db_sess.query(EventSignup.event_id).filter(EventSignup.user_id == user_id).all()}
    signup_forms_by_id = {e.id: EventSignupForm(prefix=f'e{e.id}') for e in items}
    return render_template('masterclasses.html', title='Мастер-классы', masterclasses=items, user_id=user_id, signed_event_ids=signed_ids, signup_forms_by_id=signup_forms_by_id)


@app.route('/signup_event/<int:event_id>', methods=['POST'])
def signup_event(event_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    form = EventSignupForm(prefix=f'e{event_id}')
    if not form.validate_on_submit():
        return redirect(url_for('masterclasses'))
    db_sess = db_session.create_session()
    event = db_sess.get(Event, event_id)
    if not event:
        flash('Мероприятие не найдено', 'warning')
        return redirect(url_for('masterclasses'))
    uid = session['user_id']
    if event.user_id == uid:
        flash('Нельзя записаться на своё мероприятие', 'warning')
        return redirect(url_for('masterclasses'))
    if db_sess.query(EventSignup).filter_by(user_id=uid, event_id=event_id).first():
        flash('Вы уже записаны на это мероприятие', 'info')
        return redirect(url_for('masterclasses'))
    db_sess.add(EventSignup(user_id=uid, event_id=event_id))
    db_sess.commit()
    flash('Вы успешно записались', 'success')
    return redirect(url_for('masterclasses'))


@app.route('/cancel_signup/<int:event_id>', methods=['POST'])
def cancel_signup(event_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    form = CancelFrom(prefix=f'c{event_id}')
    if not form.validate_on_submit():
        return redirect(url_for('profile'))
    db_sess = db_session.create_session()
    rec = db_sess.query(EventSignup).filter_by(user_id=session['user_id'], event_id=event_id).first()
    if rec:
        db_sess.delete(rec)
        db_sess.commit()
        flash('Запись отменена', 'success')
    return redirect(url_for('profile'))


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    form = MasterclassForm()
    if form.validate_on_submit():
        try:
            price = int(form.price.data.strip())
        except (TypeError, ValueError, AttributeError):
            return render_template('add_event.html', title='Новый мастер-класс', form=form,
                                   message='Укажите цену целым числом')
        try:
            event_date = datetime.datetime.strptime(form.date.data.strip(), '%Y-%m-%d')
        except ValueError:
            return render_template('add_event.html', title='Новый мастер-класс', form=form,
                                   message='Дата в формате ГГГГ-ММ-ДД, например 2026-05-13')
        db_sess = db_session.create_session()
        event = Event()
        event.name = form.name.data
        event.date = event_date
        event.time = form.time.data
        event.location = form.location.data
        event.description = form.description.data
        event.price = price
        event.user_id = session['user_id']
        db_sess.add(event)
        db_sess.commit()
        return redirect(url_for('masterclasses'))
    return render_template('add_event.html', title='Новый мастер-класс', form=form)


if __name__ == '__main__':
    db_session.global_init("db/users.db")
    app.run(port=8081, host='127.0.0.1')
