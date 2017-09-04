__author__ = "Jeremy Nelson"

#from aristotle import app
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8048, debug=True)
