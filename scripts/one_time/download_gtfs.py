import zipfile

import requests

from hcme.config import input_data

url = "https://transitfeeds.com/p/arcata-mad-river-transit-system/148/20211215/download"

output = input_data.gtfs_dir / "gtfs.zip"

if __name__ == "__main__":
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with output.open("wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)

    with zipfile.ZipFile(str(output), "r") as zip_ref:
        zip_ref.extractall(str(output.parent))
