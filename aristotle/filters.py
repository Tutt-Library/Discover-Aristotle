__author__ = "Jeremy Nelson"

import re

import click

from bs4 import BeautifulSoup
from flask import url_for
from .blueprint import aristotle
import search


@aristotle.app_template_filter('carousel_item')
def generate_carousel_item(hit, count):
    """Filter takes an Elasticsearch hit and generates a bootstrap carousel 
    item.

    Args:
        hits(list): A list of Elastic search hits
    """
    result = hit.get("_source")
    carousel = BeautifulSoup()
    item_attrs = { "class": "carousel-item"}
    if int(count) < 1:
        item_attrs["class"] += " active"   
    div = carousel.new_tag("div", **item_attrs)
    repo_link = carousel.new_tag(
        "a", 
        **{"href": url_for("aristotle.fedora_object", 
                           identifier="pid", 
                           value=result.get("pid"))})
    if "islandora:compoundCModel" in result.get("content_models"):
        for stream in result.get("datastreams"):
            if stream.get("dsid").startswith("OBJ") and \
               stream.get("order").startswith('1'):
                src = url_for("aristotle.fedora_datastream",
                              pid=stream.get("pid"),
                              dsid="OBJ",
                              ext="jpg")
                break
    else:
        src = url_for("aristotle.fedora_datastream",
            pid=result.get("pid"),
            dsid="OBJ",
            ext="jpg")
    img_attrs = {"class": "d-block img-fluid mt-2",
                 "style": "height: 450px", 
                 "src": src,
                 "alt": "{} slide".format(count)}

    img = carousel.new_tag("img", **img_attrs)
    repo_link.append(img)
    div.append(repo_link)
    title = carousel.new_tag(
        "div",
        **{"class": "carousel-caption d-none d-md-block"})
    h5 = carousel.new_tag("h5")
    h5.string = result.get("titlePrincipal")
    title.append(h5)
    div.append(title)
    return div.prettify()
        

@aristotle.app_template_filter('icon')
def get_icon(datastream):
    """Filter returns the glyphicon CSS class for a datastream

    Args:
	    datastream -- Datastream dict
    """
    mime_type = datastream.get('mimeType')
    if mime_type.endswith("pdf"):
        return "fa-file-pdf-o"
    if mime_type.endswith("mp4") or\
       mime_type.endswith("quicktime"):
        return "file-movie-o"
    if mime_type.endswith("mp3") or\
       mime_type.endswith("wav") or\
       mime_type.endswith("wave") or\
       mime_type.endswith("mpeg") or\
       mime_type.startswith("audio/x-m4a"):
        return "fa-audio-o"
    if mime_type.endswith("jpg") or\
       mime_type.endswith("jpeg") or\
       mime_type.endswith("jp2"):
        return "glyphicon-picture"
    if mime_type.endswith("octet-stream"):
        return "glyphicon-stats"
    if mime_type.endswith("tif"):
        return "glyphicon-download"

@aristotle.app_template_filter('page_display')
def build_pagination_button(number, offset, size, query, current_position, total_length):
    snippet = BeautifulSoup()
    li = snippet.new_tag("li", **{"class":"page-item"})
    anchor = snippet.new_tag("a", **{"class": "page-link"})
    anchor.string = "{:,}".format(number)
    offset = int(offset)
    
    if offset == number:
        li.attrs["class"].append("active")
    anchor.attrs["href"] = url_for("aristotle.fedora_object",
                                     identifier="pid",
                                     value=query) + "?offset={}".format(number)
    if number == 0:
        anchor.string = "1"
    if total_length >= 10:
        lower_bound = (offset - 3*size)
        upper_bound = (offset + 3*size)
        if (lower_bound > 0 and lower_bound == number) or \
           (upper_bound == number and current_position+1 != total_length):
            li.attrs["class"].append("disabled")
            anchor.attrs["href"] = "#"
            anchor.string= "..."
        elif (lower_bound - size) == number or offset == number or (upper_bound - size) == number :
            print((lower_bound - size), number)

            pass
        #else:
            #return ""
        #return ""   
        #if not (total_length - current_position) == 1 and \
        #   not number == current_position and \
        #   not offset-number == size and \
        #   not offset-number == -size:
        #    return "" 
        #elif (offset-number) == size*2 or (offset-number) == -(size*2):
        
    li.insert(0, anchor)
  
    return str(li)

            
            
    

@aristotle.app_template_filter('scripts')
def get_scripts(s):
    scripts = cache.get('scripts')
    if scripts:
        return scripts
    harvest()
    return cache.get('scripts')

@aristotle.app_template_filter('slugify')
def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

@aristotle.app_template_filter('sort_ds')
def sort_datastreams(datastreams):
    """Filter takes a list of datastreams and returns the sorted
    datastreams depending on the keys in each datastream dict.

    Args:
        datastreams(list): List of Datastreams dicts
    """
    if datastreams is None or len(datastreams) < 1:
        return []
    if "order" in datastreams[0]:
        datastreams.sort(key=lambda x: int(x['order']))
    elif "label" in datastreams[0]:
        datastreams.sort(key=lambda x: x['label'])
    else:
        datastreams.sort(key=lambda x: x["dsid"])
    return datastreams
        

@aristotle.app_template_filter('styles')
def get_styles(s):
    styles = cache.get('styles')
    if styles:
        return styles
    harvest()
    return cache.get('styles')

@aristotle.app_template_filter('tabs')
def get_tabs(s):
    """Filter retrieves or harvests CC Library's homepage tabs
  
    Args:
        s -- Ignored string to call from template
    """
    tabs = cache.get('tabs')
    if tabs:
        return tabs
    harvest()
    return cache.get('tabs')


@aristotle.app_template_filter('title_principal')
def get_title(pid):
    """Filter takes a pid and attempts to return the titlePrincipal

    Args:
        pid -- Fedora Object PID
    """
    return search.get_title(pid)

AUDIO_TEMPLATE = """<audio src="{0}" controls="controls" id="viewer-{1}">
 <a href="{0}" class="center-block">Download</a>
</audio>"""

DATASET_TEMPLATE = """Download Dataset <em>{1}</em> <a href="{0}" class="btn btn-primary">
<i class="glyphicon-stats glyphicon"></i></a>"""

PDF_TEMPLATE = """<object data="{0}" type="application/pdf" width="100%" height="600px">
        alt : <a href="{0}">{1}</a> 
</object>"""

QT_TEMPLATE = """<embed src="{}" width="640" height="480" class="center-block" 
controller="true" loop="false" pluginspage="http://www.apple.com/quicktime/"></embed>"""

TIFF_TEMPLATE = """<div class="row">
<div class="col-md-4 col-md-offset-4">
<a href="{}" class="btn btn-lg btn-primary">
<i class="glyphicon glyphicon-download"></i> Download</a>
</div>
</div>"""


VIDEO_TEMPLATE = """<video src="{0}" controls="controls" poster="poster.jpg" width="640" height="480" id="viewer-{1}">
<a href="{0}" class="center-block">Download video</a>
</video>"""


@aristotle.app_template_filter("viewer")
def generate_viewer(datastream, dlg_number):
    """Filter takes a datastream and generates HTML5 player based on mime-type

    Args:
        datastream -- Dictionary with Data stream information
        dlg_number -- Dialog ID Number

    """
    mime_type = datastream.get('mimeType')
    ds_url = url_for(
        'aristotle.get_datastream', 
        pid=datastream.get('pid'),
        dsid=datastream.get('dsid'))
    if mime_type.endswith('pdf'):
        return PDF_TEMPLATE.format(
             ds_url,
             datastream.get('label'))
    if mime_type.endswith('audio/mpeg') or\
       mime_type.endswith("audio/mp3") or\
       mime_type.endswith("audio/x-m4a") or\
       mime_type.endswith("wav") or\
       mime_type.endswith("wave"):
        return AUDIO_TEMPLATE.format(ds_url, dlg_number)
    if mime_type.endswith("octet-stream"):
        return DATASET_TEMPLATE.format(ds_url, datastream.get('label'))
    if mime_type.endswith('quicktime'):
        return QT_TEMPLATE.format(ds_url)
    if mime_type.endswith('mp4'):
        return VIDEO_TEMPLATE.format(ds_url, dlg_number)
    if mime_type.endswith('jpeg'):
        return """<img src="{}" class="center-block img-thumbnail">""".format(ds_url)
    if mime_type.endswith("tif"):
        return TIFF_TEMPLATE.format(ds_url)        



