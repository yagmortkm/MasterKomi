from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    user = "Ученик Яндекс.Лицея"
    if request.method == 'GET':
        return render_template('index.html', title='Домашняя страница', 
                           username=user)
    
@app.route('/register_form', methods=['POST', 'GET'])
def register_form():
    user = "Ученик Яндекс.Лицея"
    if request.method == 'GET':
        return render_template('register_form.html', title='Домашняя страница', 
                           username=user)
    elif request.method == 'POST':
        print(request.form['email'])
        print(request.form['password'])
        print(request.form['passwordcheck'])
        return "Форма отправлена"

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')