from lxml import etree
import os

DAC_CRS_FILE = 'DAC-CRS-CODES_27042021.xml'
DAC_CODELISTS = ['AidType', 'AidType-category', 'Channel-category', 'Channelcode', 'CollaborationType', 'FinanceType', 'FinanceType-category', 'FlowType', 'Sector', 'SectorCategory']
OUTPUTDIR = 'Current_DAC'


def indent(elem, level=0, shift=2):
    """Adapted from code at http://effbot.org/zone/element-lib.htm."""
    i = "\n" + level * " " * shift
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + " " * shift
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1, shift)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def merge_channel_codelists(channel, channel_code):
    combined_channel = channel.getroot()
    codelist_item = combined_channel.find("codelist-items")
    for item in channel_code.getroot().find("codelist-items").findall("codelist-item"):
        codelist_item.append(item)
    return channel


parser = etree.XMLParser(remove_blank_text=True)
dac_xml = etree.parse(DAC_CRS_FILE)
for codelist in DAC_CODELISTS:
    new_codelist = etree.ElementTree(dac_xml.find("codelist[@name='{}']".format(codelist)))
    indent(new_codelist.getroot(), 0, 4)
    try:
        new_codelist.write(os.path.join(OUTPUTDIR, '{}.xml'.format(codelist)), encoding='utf-8')
    except AttributeError:
        print(codelist)

channel = etree.parse('{}/Channel-category.xml'.format(OUTPUTDIR))
channel_code = etree.parse('{}/Channelcode.xml'.format(OUTPUTDIR))
combined = merge_channel_codelists(channel, channel_code)
combined.write(os.path.join(OUTPUTDIR, '{}.xml'.format('CRSChannelCode')), encoding='utf-8')
os.remove('{}/Channelcode.xml'.format(OUTPUTDIR))
os.remove('{}/Channel-category.xml'.format(OUTPUTDIR))
