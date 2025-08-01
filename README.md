# DAC-Codelists

This repository holds scripts to process Codelists downloaded from DAC and turn them into IATI codelists.

Files/Directories/process:

* The data downloaded from DAC is in the files in the root directory
* The `extract_dac.py` script extracts information from the DAC Downloads into a more structured form in `Current_DAC` directory
* The `IATI_codelists` directory holds current IATI codelists. These should be copied from https://github.com/IATI/IATI-Codelists-NonEmbedded . These are used as part of the processing to try and preserve order.
* The `convert_to_iati.py` script uses information from `Current_DAC` and `IATI_codelists` and writes the new codelists to `DAC_to_IATI`
* The new codelists in `DAC_to_IATI` should be synced back to https://github.com/IATI/IATI-Codelists-NonEmbedded

## Python Environment Setup

```
python3 -m venv venv/env
source venv/env/bin/activate
pip install -r requirements.txt
```

## Process

- Create a branch `updates/YYYY-MM-DD`
- Sync from IATI-Codelist-NonEmbedded repo `rsync -avz --existing ~/Projects/IATI-Codelists-NonEmbedded/xml/ IATI_codelists`
- Download the XML from https://development-finance-codelists.oecd.org/CodesList.aspx and copy to this repo
  - Make sure Active, Heading and Withdrawn are selected
- Extract `python extract_dac.py`
  - Make sure to update filename in code
 Update this line in `convert_to_iati.py` with the date DAC updated files: `element.attrib['withdrawal-date'] = "2022-01-21"`
- Convert to IATI `python convert_to_iati.py`
- Copy into [IATI-Codelists-NonEmbedded](https://github.com/IATI/IATI-Codelists-NonEmbedded) in a branch `updates/YYYY-MM-DD`
