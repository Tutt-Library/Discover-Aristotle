__author__ = "Jeremy Nelson"

import os

from flask import Flask, request
from werkzeug.contrib.cache import FileSystemCache
from werkzeug.contrib.fixers import ProxyFix
from aristotle.blueprint import aristotle

app = Flask(__name__,  
    instance_relative_config=True, 
    template_folder="templates")

app.config.from_pyfile('conf.py')

app.register_blueprint(aristotle)

@app.errorhandler(404)
def dcc_404_debug(e):
    return "Failed to find {}".format(request.url), 404

#app.wsgi_app = ProxyFix(app.wsgi_app)
#app.url_map.strict_slashes = False

#aristotle_templates = app.blueprints.get(
#    'aristotle').jinja_loader.list_templates()
#for row in app.jinja_loader.list_templates():
#    if row in aristotle_templates:
#        aristotle_templates.pop(row)

        

cache = FileSystemCache(
    app.config.get(
        "CACHE_DIR", 
        os.path.join(
            os.path.split(
                os.path.abspath(os.path.curdir))[0],
                "cache")))

