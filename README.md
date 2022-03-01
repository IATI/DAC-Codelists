## Python Environment Setup

```
python3 -m venv venv/env
source venv/env/bin/activate
pip install -r requirements.txt
```

## Process

- Create a branch `updates/YYYY-MM-DD`
- Sync from IATI-Codelist-NonEmbedded repo `rsync -avz --existing ~/Projects/IATI-Codelists-NonEmbedded/xml/ IATI_codelists`
- Download file and copy to repo: `DAC-CRS-CODES_DDMMYYYY.xml`
- Extract `python extract_dac.py`
  - Make sure to update filename in code
- Update this line in `convert_to_iati.py` with the date DAC updated files: `element.attrib['withdrawal-date'] = "2022-01-21"`
- Convert to IATI `python convert_to_iati.py`
- Copy into [IATI-Codelists-NonEmbedded](https://github.com/IATI/IATI-Codelists-NonEmbedded) in a branch `updates/YYYY-MM-DD`