__author__ = "Jeremy Nelson"

# Standard modules
import datetime
import io
import os
import sys
import uuid

# External moudles
import click
import rdflib
import requests 
from bibcat.ingesters.rels_ext import RELSEXTIngester
from bibcat.rml.processor import  XMLProcessor

BF = rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/")

class MetadataMigrator(object):
    """Class creates BIBCAT Library Linked Data from Colorado College's 
    Islandora based Fedora 3.8 environment"""
    namespaces={"mods": "http://www.loc.gov/mods/v3",
                "xlink": "https://www.w3.org/1999/xlink"}

    def __init__(self, **kwargs):
        self.bf_graph = None
        config = kwargs.get('config')
        self.cc_processor = XMLProcessor(
            rml_rules=["bibcat-base.ttl",
                "mods-to-bf.ttl",
                kwargs.get("cc_rules")],
                namespaces=MetadataMigrator.namespaces)
        #self.connections = config.CONNECTIONS
        self.default_copyright = kwargs.get("default-copyright",
            rdflib.URIRef("http://rightsstatements.org/vocab/InC/1.0/")) 
        self.base_url=config.BASE_URL
        self.rels_processor = RELSEXTIngester(base_url=self.base_url)    
        self.fedora_ri_search = config.RI_URL
        self.fedora_auth = config.FEDORA_AUTH
        self.cc_repo_base = config.REPOSITORY_URL
        # URL Minter for supporting DP.LA project
        self.minter = kwargs.get("minter") 
        self.start_pid = kwargs.get("start_pid", "coccc:root")
        self.repo_graph = rdflib.Graph()
        self.repo_graph.namespace_manager.bind("bf", BF)

    def __cc_collection__(self,
        pid, 
        rights_stmt=None):
        if rights_stmt is None:
            rights_stmt = self.default_copyright 
        child_results = requests.post(self.fedora_ri_search,
            data={"type": "tuples",
              "lang": "sparql",
              "format": "json",
              "query": CHILD_PIDS.format(pid)},
            auth=self.fedora_auth)
        if child_results.status_code > 399:
            raise ValueError("Could not add CC collection")
        collection_iri = rdflib.URIRef("{}pid/{}".format(
            self.base_url, pid))
        self.repo_graph.add(
            (collection_iri, 
             rdflib.RDF.type, 
             BF.Collection))
        self.__set_label__(pid, collection_iri)
        count = 0
        start = datetime.datetime.utcnow()
        start_msg = "Start processing collection {} at {}".format(
            pid,
            start)
        try:
            click.echo(start_msg)
        except io.UnsupportedOperation:
            print(start_msg)
        for i,child_row in enumerate(child_results.json().get("results")):
            child_pid = child_row.get("s").split("/")[-1]
            if self.__cc_is_collection__(child_pid):
                self.__cc_collection__(child_pid, rights_stmt)
                continue
            item_iri = self.__cc_pid__(child_pid)
            if item_iri is None:
                continue
            self.repo_graph.add((item_iri, BF.usageAndAccessPolicy, rights_stmt))
            instance_iri = self.repo_graph.value(subject=item_iri,
                predicate=BF.itemOf)
            work_iri = self.repo_graph.value(subject=instance_iri,
                predicate=BF.instanceOf)
            self.repo_graph.add((work_iri, BF.partOf, collection_iri))
            if not i%5 and i>0:
                try:
                    click.echo(".", nl=False)
                except io.UnsupportedOperation:
                    print('.', end="")
            if not i%10:
                count_msg = "{:,}".format(i)
                try:
                    click.echo(count_msg, nl=False)
                except io.UnsupportedOperation:
                    print(count_msg, end="")
            count += 1
        end = datetime.datetime.utcnow()
        end_msg = """Finished processing at {}
Total {:,} mins, {} objects for PID {}""".format(
        end,
        (end-start).seconds / 60.0,
        count,
        pid)
        try:
            click.echo(end_msg)
        except io.UnsupportedOperation:
            print(end_msg) 


    def __cc_pid__(self, pid):
        if self.__cc_is_member__(pid):
            return
        mods_url = "{}/objects/{}/datastreams/MODS/content".format(
            self.cc_repo_base, 
            pid)
        mods_result = requests.get(mods_url)
        if mods_result.status_code > 399:
            return
        if self.minter:
            item_iri = self.minter.item(pid)
            if item_iri is None: # Can't reach so don't continue
                return
            instance_iri = self.minter.instance(item=item_iri, pid=pid)
            work_uri = self.minter.work(instance_iri=instance_iri)
        else:
            item_iri = rdflib.URIRef("{}pid/{}".format(self.base_url, pid))
            instance_iri = rdflib.URIRef("{}#Instance".format(item_iri))
            work_uri = rdflib.URIRef("{}#Work".format(item_iri))
        mods_xml = mods_result.text
        self.cc_processor.run(mods_xml, 
            instance_iri=instance_iri,
            item_iri=item_iri,
            work_iri=work_uri)
        self.repo_graph += self.cc_processor.output
        self.repo_graph.add((item_iri, 
                           BF.heldBy, 
                           rdflib.URIRef("https://www.coloradocollege.edu/")))

        self.repo_graph.add((work_uri, rdflib.RDF.type, BF.Work))
        self.repo_graph.add((instance_iri, BF.instanceOf, work_uri))
        rels_url = "{}/objects/{}/datastreams/RELS-EXT/content".format(
            self.cc_repo_base, 
            pid)
        rels_result = requests.get(rels_url)
        self.rels_processor.run(rels_result.text,
            instance_iri=instance_iri,
            work_iri=str(work_uri))
        self.repo_graph += self.rels_processor.output
        return item_iri


    def __cc_is_collection__(self, pid):
        sparql = IS_COLLECTION.format(pid)
        collection_result = requests.post(self.fedora_ri_search,
            data={"type": "tuples",
                "lang": "sparql",
                "format": "json",
                "query": sparql},
            auth=self.fedora_auth)
        if len(collection_result.json().get('results')) > 0:
            return True
        return False

    def __cc_is_member__(self, pid):
        rels_ext_url = "{}{}/datastream/RELS-EXT".format(
            self.cc_repo_base,
            pid)
        rels_ext_result = requests.get(rels_ext_url)
        if rels_ext_result.status_code < 399:
            rels_ext_xml = lxml.etree.XML(rels_ext_result.text)
            is_constituent =  rels_ext_xml.xpath(
                "rdf:Description/fedora:isConstituentOf",
                namespaces=self.rels_processor.xml_ns)
            if len(is_constituent) > 0:
                return True
        return False

    def __set_label__(self, pid, entity_iri):
        mods_url = "{}{}/datastream/MODS".format(
            self.cc_repo_base, 
            pid)
        result = requests.get(mods_url)
        if result.status_code > 399:
            return
        mods_xml = lxml.etree.XML(result.text)
        title = mods_xml.xpath("mods:titleInfo/mods:title", 
            namespaces=self.cc_processor.xml_ns)
        if title is None:
            return
        self.repo_graph.add((entity_iri, 
            rdflib.RDFS.label, 
            rdflib.Literal(title[0].text, lang="en")))


    def harvest(self, output_path=None):
        start = datetime.datetime.utcnow()
        start_msg = "Starting CC Migration to BF Linked Data at {}".format(
            start)
        try:
            click.echo(start_msg)
        except io.UnsupportedOperation:
            print(start_msg)
        self.__cc_collection__(self.start_pid)
        if output_path:
            with open(output_path, 'wb+') as fo:
                fo.write(self.repo_graph.serialize(format='turtle'))
        end = datetime.datetime.utcnow()
        end_msg = """Finished CC Migration harvest at {}, total time {:,} minutes
Total number of triples {:,}""".format(end, (end-start).seconds / 60.0, len(self.repo_graph))
        try:
            click.echo(end_msg)
        except io.UnsupportedOperation:
            print(end_msg)
        



# SPARQL Templates
CHILD_PIDS = """SELECT DISTINCT ?s
WHERE {{
      ?s <fedora-rels-ext:isMemberOfCollection> <info:fedora/{}> .
}}"""

IS_COLLECTION = """SELECT DISTINCT ?o
WHERE {{        
  <info:fedora/{0}> <fedora-model:hasModel> <info:fedora/islandora:collectionCModel> .
  <info:fedora/{0}> <fedora-model:hasModel> ?o
}}"""

# Plains2Peaks Minter
class P2PMinter(object):

    def __init__(self):
        self.base_url = "https://plains2peaks.org/"
        self.islandora_url = "https://digitalcc.coloradocollege.edu/islandora/object/"

    def item(self, pid):
        # Returns Islandora URL if available
        islandora_pid_url = "{}{}".format(self.islandora_url, pid)
        test_available = requests.get(islandora_pid_url)
        if test_available.status_code < 400:
            return rdflib.URIRef(islandora_pid_url)

    def instance(self, **kwargs):
        return rdflib.URIRef("{}{}".format(self.base_url, uuid.uuid1()))

   
    def work(self, **kwargs):
        instance_iri = kwargs.get("instance_iri")
        return rdflib.URIRef("{}#Work".format(instance_iri))

@click.command()
@click.option("--minter", prompt="Alternate Minter")
@click.option("--cc_rules", prompt="Full path to Colorado College RML")
@click.option("--output_path", prompt="Full path to output turtle file")
def main(minter=None, cc_rules=[], output_path=None):
    sys.path.append(os.path.abspath(
        os.path.dirname(
            os.path.dirname(__name__))))
    import instance.conf as config
    if minter is None:
        migrator = MetadataMigrator(
            config=config,
            cc_rules=cc_rules)
    elif minter.startswith("plains2peak"):
        minter = P2PMinter()
        migrator = MetadataMigrator(
            config=config,
            cc_rules=cc_rules,
            minter=minter)
    migrator.harvest(output_path)
    
    

if __name__ == "__main__":
    main()
     
