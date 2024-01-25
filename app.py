from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('Contact_page.html')

@app.route('/login')
def login():
    return render_template('Login.html')

@app.route('/register')
def register():
    return render_template('Register.html')

@app.route('/school')
def school():
    return render_template('School_page.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
