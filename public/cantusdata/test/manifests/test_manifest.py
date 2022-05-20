from rest_framework.test import APITransactionTestCase
from cantusdata.settings import BASE_DIR
import urllib.request
import requests
import time
import os
import json
# Refer to http://www.django-rest-framework.org/api-guide/testing

class IIIFSpeedTestCase(APITransactionTestCase):
    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")
        with open(os.path.join(BASE_DIR, "cantusdata", "test", "manifests", "manifests.txt"), "r") as f:
            self.manifest_list = [line.strip() for line in f.readlines()]

    def test_manifest_proxy(self):
        times = []
        for manifest_url in self.manifest_list:
            proxy_path = f"/manifest-proxy/{manifest_url}"
            try:
                start = time.time()
                self.client.get(proxy_path)
                elapsed = time.time() - start
                times.append({"url": manifest_url, "time": elapsed})
            except:
                raise Exception(f"{manifest_url} unreachable")
        times.sort(key = lambda x: x["time"])
        for t in times:
            print(f'Acessed { t["url"]} in {t["time"]} seconds.')
    
    def test_image_uris(self):
        for manifest in self.manifest_list:
            try:
                manifest_json = urllib.request.urlopen(manifest)
                manifest_data = json.loads(manifest_json.read().decode("utf-8"))
                canvas = manifest_data["sequences"][0]["canvases"][0]
                service = canvas["images"][0]["resource"]["service"]
                uri = service["@id"]
                path_tail = (
                    "default.jpg"
                    if service["@context"]
                    == "http://iiif.io/api/image/2/context.json"
                    else "native.jpg"
                )
                uri_obj = {
                    "full": uri,
                    "thumbnail": uri + "/full/,160/0/" + path_tail,
                    "large": uri + "/full/,1800/0/" + path_tail
                }
                
                report = f"{manifest}\n========\n"
                for key in uri_obj.keys():
                    start = time.time()
                    requests.get(uri_obj[key])
                    elapsed = time.time() - start
                    report += f"{key}_load_time: {elapsed}\n" 
                print(report)
            except:
                print(f"{manifest} has a problem")
                continue