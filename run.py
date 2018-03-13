__author__ = "Jeremy Nelson"

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from app import app

application = DispatcherMiddleware(
    app,
    {"/digitalcc": app }
)

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8048, debug=True)
    run_simple('0.0.0.0', 8048, application, use_reloader=True, use_debugger=True)

