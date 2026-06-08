from flask import Flask, render_template
from config import VERSION
from bloomin.routes import bloomin_bp

app = Flask(__name__)
app.register_blueprint(bloomin_bp)

@app.route("/")
def home():
    return render_template('ascii-render.html', version=VERSION)

if __name__ == "__main__":
    app.run(debug=True)