from lxml import etree, objectify
import datetime
import os

DAC_CODELISTS_DIR = "Current_DAC"
IATI_CODELISTS_DIR = "IATI_codelists"
DAC_IATI_CODELISTS = [
    ("Co-operation modality", "AidType", "not(@Heading)"),
    ("Co-operation modality", "AidType-category", "@Heading=1"),
    ("Channel of delivery", "CRSChannelCode", None),
    ("Bi_Multi", "CollaborationType", None),
    ("Type of finance", "FinanceType", "not(@Heading)"),
    ("Type of finance", "FinanceType-category", "@Heading=1"),
    ("Type of flow", "FlowType", None),
    ("Purpose code", "Sector", "not(@Heading)"),
    ("Purpose code", "SectorCategory", "@Heading=1"),
]
OUTPUTDIR = "DAC_to_IATI"
namespaces = {"dac": "http://www.oecd.org/dac/stats/dacandcrscodelists"}
codelist_dict = {"Channel-category": "CRSChannelCode"}


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


def filter_codelist(codelist, condition):
    codelist_items = codelist.find("codelist-items")

    if condition:
        for codelist_item in codelist_items.findall("codelist-item"):
            if not codelist_item.xpath(condition):
                codelist_items.remove(codelist_item)

    return codelist


def cleanup(codelist):
    """Clean up the xml by removing tags, namespaces, anchors and attributes."""

    # Remove some tags
    for codelist_item in codelist.find("codelist-items").findall("codelist-item"):
        for child in codelist_item:
            if child.tag in ["acronym", "crs", "tossd", "parent-code"]:
                child.getparent().remove(child)

    # Remove dac namespaces from the xml.
    if codelist.attrib["name"] in codelist_dict.keys():
        codelist.attrib["name"] = codelist_dict[codelist.attrib["name"]]
    for elem in codelist.getiterator():
        if not hasattr(elem.tag, "find"):
            continue
        i = elem.tag.find("dacandcrscodelists}")
        if i >= 0:
            elem.tag = elem.tag[i + 1]
    objectify.deannotate(codelist, cleanup_namespaces=True)

    # Remove anchors
    anchors = codelist.xpath("//a")
    for anchor in anchors:
        anchor.getparent().remove(anchor)

    # Remove some attributes
    for key in ["CRS", "TOSSD"]:
        codelist.attrib.pop(key, None)
    for codelist_item in codelist.find("codelist-items").findall("codelist-item"):
        for key in ["mcd", "Heading", "Particularity", "modality"]:
            codelist_item.attrib.pop(key, None)
        remove_trailing_whitespaces(codelist_item)
    return codelist


def renames(codelist):
    """Rename some tags and values"""

    # Rename some status values
    for codelist_item in codelist.find("codelist-items").findall("codelist-item"):
        if "status" in codelist_item.attrib.keys():
            codelist_status = codelist_item.attrib["status"]
            if codelist_status in ["Active", "voluntary basis"]:
                codelist_item.attrib["status"] = "active"
            if codelist_status in ["Withdrawn"]:
                codelist_item.attrib["status"] = "withdrawn"

    return codelist


def remove_empty_narratives(codelist_item):
    if codelist_item.find("description") is not None:
        for narrative in codelist_item.find("description").findall("narrative"):
            if narrative.text:
                return
        codelist_item.remove(codelist_item.find("description"))
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
    codelist.attrib["embedded"] = "0"
    metadata = codelist.find("metadata")
    iati_metadata = iati_codelist.find("metadata")
    metadata.getparent().replace(metadata, iati_metadata)
    sorted_codes = compare_codes(codelist, iati_codelist)
    new_codelist = etree.Element("codelist-items")
    for item in sorted_codes:
        remove_empty_narratives(item[1])
        new_codelist.append(item[1])
    codelist.replace(codelist.find("codelist-items"), new_codelist)
    return codelist


def compare_codes(codelist, iati_codelist):
    """Go through all codelist-item codes and ensure they exist in both codelists."""
    iati_codes = {}
    dac_codes = {}
    for iati_code in iati_codelist.find("codelist-items").findall("codelist-item"):
        iati_codes[iati_code.find("code").text] = iati_code
    for code in codelist.find("codelist-items").findall("codelist-item"):
        code_text = code.find("code").text
        if code_text in dac_codes:
            code2 = dac_codes[code_text]
            # Prefer the <crs>1</crs> entries
            if code.find("crs").text == "0" and code2.find("crs").text == "1":
                continue
            if code.find("crs").text == "1" and code2.find("crs").text == "0":
                dac_codes[code_text] = code
                continue
            if datetime.date.fromisoformat(
                code.attrib.get("activation-date", "1900-01-01")
            ) < datetime.date.fromisoformat(code.attrib.get("activation-date", "1900-01-02")):
                earlier_code = code
                later_code = code2
            else:
                earlier_code = code2
                later_code = code
            if "activation-date" in earlier_code:
                later_code.attrib["activation-date"] = earlier_code.attrib["activation-date"]
            dac_codes[code_text] = later_code
        else:
            dac_codes[code_text] = code

    for key, element in iati_codes.items():
        if key not in dac_codes.keys():
            if element.attrib["status"] != "withdrawn":
                element.attrib["status"] = "withdrawn"
            if "withdrawal-date" not in element.attrib.keys():
                element.attrib["withdrawal-date"] = "2026-04-02"
            dac_codes[key] = element
    return sorted(dac_codes.items())


parser = etree.XMLParser(remove_blank_text=True)
for dac_name, iati_name, condition in DAC_IATI_CODELISTS:
    print(f"Processing {dac_name} -> {iati_name}")
    iati_codelist = etree.parse(f"{IATI_CODELISTS_DIR}/{iati_name}.xml").getroot()
    codelist = etree.parse(f"{DAC_CODELISTS_DIR}/{dac_name}.xml").getroot()
    codelist.attrib["name"] = iati_name
    if "category-codelist" in iati_codelist.attrib:
        codelist.attrib["category-codelist"] = iati_codelist.attrib["category-codelist"]
    filtered_codelist = renames(filter_codelist(codelist, condition))
    iati_format = etree.ElementTree(
        add_iati_codelist_xml(filtered_codelist, iati_codelist)
    )
    indent(cleanup(iati_format.getroot()), 0, 4)
    try:
        iati_format.write(os.path.join(OUTPUTDIR, f"{iati_name}.xml"), encoding="utf-8")
    except AttributeError:
        print(codelist_string)
