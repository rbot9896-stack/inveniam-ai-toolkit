"""Build the Meridian dashboard from ../../deals/the-meridian/data.json + template_meridian.html.
Writes meridian.html next to this script, with every field link rewritten from the
host the API returns (sales-v1.inveniam.io) to the current app host, sales.inveniam.io
(confirmed working 2026-09-24). Set VIEWER_HOST to override.
Usage: python3 build_meridian.py   (run meridian_data.py first)
"""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
data = open(os.path.join(H, '..', '..', 'deals', 'the-meridian', 'data.json')).read()
tpl = open(os.path.join(H, 'template_meridian.html')).read()
data_js = data.replace('</', '<\\/')  # keep the inline <script> safe
host = os.environ.get('VIEWER_HOST', 'https://sales.inveniam.io')
out = tpl.replace('__DATA__', data_js).replace('__HOST__', host)
open(os.path.join(H, 'meridian.html'), 'w').write(out)
print('meridian.html', len(out) // 1024, 'KB', '->', host)
