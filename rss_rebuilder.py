#!/usr/bin/env python3
import os
import ssl
import yaml
import email.utils as eut
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.dom import minidom
from urllib.request import urlopen, Request

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"

ET.register_namespace('itunes', ITUNES_NS)
ET.register_namespace('atom', ATOM_NS)

CLEAN_PARAMS = (
    'utm_', 'gclid', 'fbclid', 'mc_cid', 'mc_eid', 'ad', 'adParam', 'audio_id',
    'awCollectionId', 'awEpisodeId', 'aw_0_', 'aw', 'campaign', 'source', 'medium'
)

USER_AGENT = 'ytm-rss-builder/1.0 (+https://github.com/)'

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_xml(url):
    req = Request(url, headers={'User-Agent': USER_AGENT})
    ctx = ssl.create_default_context()
    with urlopen(req, context=ctx, timeout=60) as resp:
        data = resp.read()
    return data.decode('utf-8', errors='replace')

def strip_tracking_params(href: str) -> str:
    try:
        parts = urlsplit(href)
        if parts.query:
            kept = []
            for kv in parts.query.split('&'):
                if not kv:
                    continue
                key = kv.split('=', 1)[0]
                low = key.lower()
                drop = False
                for pat in CLEAN_PARAMS:
                    if pat.endswith('_') and low.startswith(pat):
                        drop = True
                        break
                    if low == pat.lower():
                        drop = True
                        break
                if not drop:
                    kept.append(kv)
            new_query = '&'.join(kept)
        else:
            new_query = ''
        new = parts._replace(query=new_query, fragment='')
        return urlunsplit(new)
    except Exception:
        return href

def rfc2822(dt: datetime) -> str:
    return eut.format_datetime(dt)

def pretty_xml(elem: ET.Element) -> str:
    rough = ET.tostring(elem, encoding='utf-8')
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

def build_feed(src_xml: str, site_base_path: str = '/') -> str:
    src = ET.fromstring(src_xml)
    ch = src.find('channel')
    if ch is None:
        raise RuntimeError('Brak <channel> w źródłowym RSS')

    rss = ET.Element('rss', attrib={'version': '2.0',
                                    f'xmlns:itunes': ITUNES_NS,
                                    f'xmlns:atom': ATOM_NS})
    channel = ET.SubElement(rss, 'channel')

    def copy_text(tag):
        el = ch.find(tag)
        if el is not None and (el.text or '').strip():
            ET.SubElement(channel, tag).text = el.text

    for t in ['title', 'link', 'language', 'copyright', 'description']:
        copy_text(t)

    ET.SubElement(channel, f'{{{ATOM_NS}}}link', attrib={
        'href': site_base_path.rstrip('/') + '/podcast.xml',
        'rel': 'self',
        'type': 'application/rss+xml',
    })

    for t in [f'{{{ITUNES_NS}}}author', f'{{{ITUNES_NS}}}owner', f'{{{ITUNES_NS}}}image',
              f'{{{ITUNES_NS}}}category', f'{{{ITUNES_NS}}}explicit', f'{{{ITUNES_NS}}}type',
              f'{{{ITUNES_NS}}}summary', f'{{{ITUNES_NS}}}subtitle']:
        el = ch.find(t)
        if el is not None:
            channel.append(el)

    ET.SubElement(channel, 'lastBuildDate').text = rfc2822(datetime.now(timezone.utc))

    for item in ch.findall('item'):
        out = ET.SubElement(channel, 'item')
        for t in ['title', 'link', 'guid', 'pubDate', 'description']:
            el = item.find(t)
            if el is not None:
                out.append(el)
        for t in [f'{{{ITUNES_NS}}}duration', f'{{{ITUNES_NS}}}episode', f'{{{ITUNES_NS}}}episodeType',
                  f'{{{ITUNES_NS}}}explicit', f'{{{ITUNES_NS}}}image', f'{{{ITUNES_NS}}}author',
                  f'{{{ITUNES_NS}}}summary', f'{{{ITUNES_NS}}}subtitle']:
            el = item.find(t)
            if el is not None:
                out.append(el)

        enc = item.find('enclosure')
        if enc is not None and 'url' in enc.attrib:
            clean = strip_tracking_params(enc.attrib['url'])
            new_enc = ET.SubElement(out, 'enclosure', attrib={
                'url': clean,
                'type': enc.attrib.get('type', 'audio/mpeg'),
            })
            if 'length' in enc.attrib:
                new_enc.set('length', enc.attrib['length'])

    return pretty_xml(rss)

def main():
    cfg = load_config('config.yaml')
    src_url = cfg['source_feed']
    out_file = cfg.get('output_file', 'podcast.xml')
    base_path = cfg.get('site_base_path', '/')

    xml = fetch_xml(src_url)
    cleaned = build_feed(xml, site_base_path=base_path)

    os.makedirs('public', exist_ok=True)
    out_path = os.path.join('public', out_file)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    print(f"Wygenerowano: {out_path}")

if __name__ == '__main__':
    main()
