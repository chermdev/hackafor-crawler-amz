# Hackafor Amazon Product Scrapper
---
## Install
```bash
pip install git+https://github.com/chermdev/hackafor-crawler-amz.git#egg=hackafor_crawler_amz
```

## Use
Example:
```python
from hackafor_crawler_amz import crawler

URLS = ["https://a.co/d/geQhA2O","https://a.co/d/d650BRG"]

data = crawler.scrap_urls(URLS)

print(data)
```

this returns a list of dict with the structure:
```python
[
  {
    "name": str, # this value is always "", it's not generated.
    "full_name": str, # product full name
    "price": float, # price of the product
    "image": str, # url of the image
    "categories": list # list of categories
  },
  {
    ...
  },
  ...
]

```

---
## CLI
```bash
hackafor-crawler-amz
```

|params|value|
|---|---|
|`--urls`| comma-separated|
|`--locale`| default en-US|

Example:
```bash
hackafor_crawler_amz --urls https://a.co/d/geQhA2O,https://a.co/d/d650BRG
```

Export to JSON with `>> <filename>.json`.
For example:
```bash
hackafor_crawler_amz --urls https://a.co/d/geQhA2O,https://a.co/d/d650BRG >> data.json
```
This will append the stdout to `data.json`.

---
