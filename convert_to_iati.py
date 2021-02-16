from lxml import etree, objectify
import os


DAC_CODELISTS_DIR = 'Current_DAC'
IATI_CODELISTS_DIR = 'IATI_codelists'
OUTPUTDIR = 'DAC_to_IATI'
namespaces = {'dac': 'http://www.oecd.org/dac/stats/dacandcrscodelists'}
codelist_dict = {'Channel-category': 'CRSChannelCode'}


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


def cleanup(codelist):
    """Remove dac namespaces from the xml."""
    if codelist.attrib["name"] in codelist_dict.keys():
        codelist.attrib["name"] = codelist_dict[codelist.attrib["name"]]
    for elem in codelist.getiterator():
        if not hasattr(elem.tag, 'find'):
            continue
        i = elem.tag.find('dacandcrscodelists}')
        if i >= 0:
            elem.tag = elem.tag[i + 1]
    objectify.deannotate(codelist, cleanup_namespaces=True)
    anchors = codelist.xpath("//a")
    for anchor in anchors:
        anchor.getparent().remove(anchor)
    for codelist_item in codelist.find('codelist-items').findall('codelist-item'):
        if 'mcd' in codelist_item.attrib.keys():
            codelist_item.attrib.pop('mcd')
        if 'status' in codelist_item.attrib.keys():
            codelist_status = codelist_item.attrib['status']
            if codelist_status == "voluntary basis":
                codelist_item.attrib['status'] = "active"
        remove_trailing_whitespaces(codelist_item)
    return codelist


def remove_empty_narratives(codelist_item):
    if codelist_item.find('description') is not None:
        for narrative in codelist_item.find('description').findall('narrative'):
            if narrative.text:
                return
        codelist_item.remove(codelist_item.find('description'))
    return


def remove_trailing_whitespaces(codelist_item):
    narratives = codelist_item.xpath("//narrative")
    for narrative in narratives:
        if hasattr(narrative, "text") and narrative.text is not None:
            narrative.text = narrative.text.strip()

    categories = codelist_item.xpath("//category")
    for category in categories:
        if hasattr(category, "text") and category.text is not None:
            category.text = category.text.strip()
    return


def add_iati_codelist_xml(codelist, iati_codelist):
    """Add metadata content and update codelists."""
    codelist.attrib['embedded'] = '0'
    metadata = codelist.find('metadata')
    iati_metadata = iati_codelist.find('metadata')
    metadata.getparent().replace(metadata, iati_metadata)
    sorted_codes = compare_codes(codelist, iati_codelist)
    new_codelist = etree.Element('codelist-items')
    for item in sorted_codes:
        remove_empty_narratives(item[1])
        new_codelist.append(item[1])
    codelist.replace(codelist.find('codelist-items'), new_codelist)
    return codelist


def compare_codes(codelist, iati_codelist):
    """Go through all codelist-item codes and ensure they exist in both codelists."""
    iati_codes = {}
    dac_codes = {}
    for iati_code in iati_codelist.find('codelist-items').findall('codelist-item'):
        iati_codes[iati_code.find('code').text] = iati_code
    for code in codelist.find('codelist-items').findall('codelist-item'):
        dac_codes[code.find('code').text] = code
    for key, element in iati_codes.items():
        if key not in dac_codes.keys():
            if element.attrib['status'] != 'withdrawn':
                element.attrib['status'] = 'withdrawn'
            if "withdrawal-date" not in element.attrib.keys():
                element.attrib['withdrawal-date'] = "2020-02-28"
            dac_codes[key] = element
    return sorted(dac_codes.items())


parser = etree.XMLParser(remove_blank_text=True)
for a, b, codelists in os.walk(DAC_CODELISTS_DIR):
    for codelist_string in codelists:
        codelist = etree.parse("{}/{}".format(DAC_CODELISTS_DIR, codelist_string))
        clean_codelist = cleanup(codelist.getroot())
        iati_format = etree.ElementTree(add_iati_codelist_xml(clean_codelist, etree.parse("{}/{}".format(IATI_CODELISTS_DIR, codelist_string)).getroot()))
        indent(iati_format.getroot(), 0, 4)
        try:
            iati_format.write(os.path.join(OUTPUTDIR, '{}'.format(codelist_string)), encoding='utf-8')
        except AttributeError:
            print(codelist_string)
