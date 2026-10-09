"""Download the fixed UBL 2.1 schema and its imports into a disposable directory."""
import hashlib
import json
import pathlib
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT_URL = 'https://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd'


def fetch(destination):
    destination = pathlib.Path(destination).resolve()
    manifest = {}
    def download(url):
        parsed = urllib.parse.urlsplit(url)
        if parsed.hostname not in {'docs.oasis-open.org', 'www.w3.org'} or parsed.scheme not in {'http', 'https'}:
            raise ValueError('Unsupported schema reference')
        if url in manifest:
            return pathlib.Path(manifest[url]['path'])
        target = (destination / parsed.hostname / parsed.path.lstrip('/')).resolve()
        if not target.is_relative_to(destination):
            raise ValueError('Schema path leaves destination')
        secure = urllib.parse.urlunsplit(('https', parsed.netloc, parsed.path, '', ''))
        with urllib.request.urlopen(secure, timeout=30) as response:
            data = response.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            raise ValueError('Schema exceeds size limit')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[url] = {'path': str(target), 'sha256': hashlib.sha256(data).hexdigest()}
        schema = ET.fromstring(data)
        for node in schema.iter():
            location = node.attrib.get('schemaLocation')
            if location:
                download(urllib.parse.urljoin(url, location))
        return target
    schema = download(ROOT_URL)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(schema)
    return schema


if __name__ == '__main__':
    fetch(sys.argv[1])
