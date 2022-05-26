from random import randint
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
    
    def test_image_bursts(self):
        for manifest in self.manifest_list:
            try:
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
                        if service["@context"]
                        == "http://iiif.io/api/image/2/context.json"
                        else "native.jpg"
                    )
                    transformations = [
                        {"region":"full", "size":",1800", "rotation":"0"},
                        {"region":"pct:10,30,50,50", "size":",1800", "rotation":"0"},
                        {"region":"pct:10,30,50,50", "size":",1800", "rotation":"45"},
                        {"region":"pct:10,30,50,50", "size":",1500", "rotation":"45"},
                        {"region":"full", "size":",1500", "rotation":"60"},
                        {"region":"pct:40,10,40,80", "size":",300", "rotation":"0"},
                        {"region":"pct:90,90,10,10", "size":",900", "rotation":"180"},
                        {"region":"square", "size":",2000", "rotation":"20"}
                    ]
                    
                    for (j, t) in enumerate(transformations):
                        start = time.time()
                        requests.get(f"{uri}/{t['region']}/{t['size']}/{t['rotation']}/{path_tail}")
                        elapsed = time.time() - start
                        total_time += elapsed
                        print(f"  {i}.{j} - {elapsed}")
                print(f"Total 4x8 time for {manifest} = {total_time}")
            except:
                print(f"{manifest} has a problem")
                continue