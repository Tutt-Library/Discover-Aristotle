#
# iiibots.py -- Bots for interfacing with III's Millennium system
#
# author: Jeremy Nelson
#
# Copyrighted by Colorado College
import urllib2,logging,datetime
import csv
from eulxml import xmlmap
from vendors.iii.models import ItemRecord,IIIStatusCode,Fund,FundProcessLog
from discovery.parsers.tutt_maps import LOCATION_CODE_MAP

class FundBot(object):
    """
    `FundBot` takes a csv file, search and replaces each occurrence of a FUND
    code with its full account value.
    """

    def __init__(self,**kwargs):
        """
        Initalizes bot with csv file reader
   
        :param  csv_file: CSV file object 
        :param code_location: Field location index 0 where fund codes are located in 
                              the row, default is 9
        """
        if not kwargs.has_key('csv_file'):
            raise ValueError("FundBot requires a csv_file")
        self.input_csv = csv.reader(kwargs.get('csv_file'))
        if kwargs.has_key('code_location'):
            self.code_location = int(kwargs.get('code_location'))
        else:
            self.code_location = 9
        self.substitutions = 0
        

    
    def process(self,response):
        """
        Iterates through csv file, replacing each occurrence of fund code 
        with the expanded fund account value.
        
        :param response: Django response object 
        :rtype: file object
        """
        output_csv = csv.writer(response)
        for row in self.input_csv:
            paid_date = row[0]
            invoice_number = row[2]
            invoice_amount = row[3]
            end_index = len(row)-1 
            vendor = row[end_index].strip().upper()
            fund_code = row[end_index-1].strip().upper()
            query = Fund.objects.filter(code=fund_code)
            if query:
                fund_value = query[0].value
            elif fund_code.startswith('FUND'):
                fund_value = fund_code
            else:
                fund_value = '%s not found' % fund_code
            self.substitutions += 1
            output_csv.writerow([paid_date,
                                 invoice_number,
                                 invoice_amount,
                                 vendor,
                                 fund_value])
        return response 
        


class ItemBot(object):
    """`ItemBot` uses the eulxml module to capture specific information about an
    item in a III Millennium ILS from a method call to a web OPAC in XML mode.
    """

    def __init__(self,**kwargs):
        """
        Initializes web OPAC address from passed in variable.
        """
        if kwargs.has_key('opac_url'):
            self.opac_url  = kwargs.get('opac_url')
        else:
            self.opac_url = None
        if kwargs.has_key('item_id'):
            self.item_id = kwargs.get('item_id')
            raw_xml_url = self.opac_url + self.item_id
            try:
                raw_xml = urllib2.urlopen(raw_xml_url).read()
                self.item_xml = xmlmap.load_xmlobject_from_string(raw_xml,xmlclass=ItemRecord) 
            except:
                logging.error("ERROR with %s" % raw_xml_url)
                self.item_xml = None 
        else:
            self.item_id = None

    def location(self):
        """
        Retrieves location code from XML and then does a look-up
        using the discovery.parsers.tutt_map LOCATION_CODE_MAP
        for the human-friendly facet label

        :rtype: string
        """
        location = None
        if self.item_xml is not None:
            try:
                location = LOCATION_CODE_MAP[self.item_xml.location_code.strip()]
            except KeyError:
                location = 'Unknown location code %s' % self.item_xml.location_code
        return location

    def status(self):
        """
        Retrieves status code from XML

        :rtype: string or None
        """
        if self.item_xml is not None:
            try:
                status = IIIStatusCode.objects.get(code=self.item_xml.status)
            except:
                status = None
            try:
                due_date = datetime.datetime.strptime(self.item_xml.due_date,'%m-%d-%Y')
                return 'Due back on %s' % due_date.strftime('%m-%d-%Y')
            except ValueError:
                pass # Failed to parse due-date, assume item is not checked-out
        else:
            return None
        if status is None:
            return 'Status unknown for code %s' % self.item_xml.status
        else:
            return status.value

    def volume(self):
        """
        Method retrieves Volume from XML or None if not present.

        :rtype: string
        """
        if self.item_xml is not None:
            if self.item_xml.volume is not None:
                return self.item_xml.volume
        return None
            
 
