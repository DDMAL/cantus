import urllib.request
import time
import requests
import json
import os
from cantusdata.settings import BASE_DIR
from cantusdata.models.manuscript import Manuscript
from unittest import TestCase


class IIIFTestCase(TestCase):
    def setUp(self):
        with open(
            os.path.join(
                BASE_DIR, "cantusdata", "test", "external", "iiif", "manifests.txt"
            ),
            "r",
        ) as f:
            self.manifest_list = [x.strip() for x in f.readlines()]

    def test_iiif(self):
        valid_list = []

        for manifest in self.manifest_list:
            # Access Manifest
            try:
                manifest_json = urllib.request.urlopen(manifest)
            except:
                print(f"FATAL: {manifest} failed at opening the manifest url.")
                continue
            # Load JSON
            try:
                manifest_data = json.loads(manifest_json.read().decode("utf-8"))
            except:
                print(f"FATAL: {manifest} failed at loading the json data.")
                continue
            # Access service id
            try:
                service = manifest_data["sequences"][0]["canvases"][0]["images"][0][
                    "resource"
                ]["service"]
                uri = service["@id"]
            except:
                print(
                    f"FATAL: {manifest} failed at providng a service id in the expected place."
                )
                continue
            # Test Image API
            path_tail = (
                "default.jpg"
                if service["@context"] == "http://iiif.io/api/image/2/context.json"
                else "native.jpg"
            )
            try:
                full = requests.get(f"{uri}/full/full/0/{path_tail}")
                square = requests.get(f"{uri}/square/full/0/{path_tail}")
                assert full.content != square.content
            except:
                print(f"FATAL: {manifest} failed at implementing the IIIF Image API")
                continue

            print(f"{manifest} passed all critical tests.")
            valid_list.append(manifest)

            try:
                manuscript_obj = Manuscript.objects.filter(manifest_url=manifest)[0]
                folio_count = manuscript_obj.folio_count
                canvas_count = len(manifest_data["sequences"][0]["canvases"])
                if canvas_count < folio_count:
                    print(
                        f"warning: {manifest} has fewer canvas items than there are folios in the database."
                    )
            except:
                print(f"{manifest} is not added to any manuscript.")

        self.image_bursts(valid_list)

    def image_bursts(self, valid_list):
        for manifest in valid_list:
            manifest_json = urllib.request.urlopen(manifest)
            manifest_data = json.loads(manifest_json.read().decode("utf-8"))
            total_time = 0
            print(f"\n{manifest}\n========")
            for i in range(4):
                canvas = manifest_data["sequences"][0]["canvases"][i]
                service = canvas["images"][0]["resource"]["service"]
                uri = service["@id"]
                path_tail = (
                    "default.jpg"
                    if service["@context"] == "http://iiif.io/api/image/2/context.json"
                    else "native.jpg"
                )
                transformations = [
                    {"region": "pct:0,0,25,25", "size": ",1800"},
                    {"region": "pct:25,0,25,25", "size": ",1800"},
                    {"region": "pct:50,0,25,25", "size": ",1800"},
                    {"region": "pct:75,0,25,25", "size": ",1800"},
                    {"region": "pct:0,25,25,25", "size": ",1800"},
                    {"region": "pct:0,50,25,25", "size": ",1800"},
                    {"region": "pct:0,75,25,25", "size": ",1800"},
                    {"region": "full", "size": ",160"},
                ]

                for (j, t) in enumerate(transformations):
                    start = time.time()
                    req = f"{uri}/{t['region']}/{t['size']}/0/{path_tail}"
                    requests.get(req)
                    elapsed = time.time() - start
                    total_time += elapsed
                    print(f"  {i}.{j} - {elapsed} - {req}")
            print(f"Total 4x8 time for {manifest} = {total_time}")
