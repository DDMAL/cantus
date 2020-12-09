import csv
import sys
import pprint as pp
from natsort import natsorted
import urllib.request
import json


def extract_ids(str_list):
    left_sweep = remove_longest_common_string(str_list, "left")
    right_sweep = remove_longest_common_string(left_sweep, "right")
    ids = [remove_number_padding(s) for s in right_sweep]
    return ids


def remove_longest_common_string(str_list, align="left"):
    longest_str = max(str_list, key=len)
    max_length = len(longest_str)
    if align == "left":
        norm_str_list = [s.ljust(max_length) for s in str_list]
    elif align == "right":
        norm_str_list = [s.rjust(max_length) for s in str_list]
    s1 = norm_str_list[0]
    diffs = []
    for s2 in norm_str_list[1:]:
        [diffs.append(i) for i in range(max_length) if s1[i] != s2[i]]
    diffs_set = set(diffs)
    print(diffs_set)
    mismatch_start = min(diffs_set)
    mismatch_end = max(diffs_set)
    return [
        s[mismatch_start : mismatch_end + 1].strip() for s in norm_str_list
    ]


def remove_number_padding(s):
    number_str = ""
    ret_str = ""
    for c in s:
        if c.isdigit():
            number_str += c
        else:
            if number_str:
                ret_str += "{}".format(int(number_str))
                number_str = ""
            ret_str += c
    if number_str:
        ret_str += "{}".format(int(number_str))
    return ret_str


if __name__ == "__main__":
    cantus_csv = sys.argv[1]
    manifest = sys.argv[2]
    uris = []
    manifest_json = urllib.request.urlopen(manifest)
    manifest_data = json.load(manifest_json)
    for canvas in manifest_data["sequences"][0]["canvases"]:
        service = canvas["images"][0]["resource"]["service"]
        uris.append(service["@id"])
    print(uris)

    folio_link = {}
    with open(cantus_csv) as csvfile:
        cantus = csv.DictReader(csvfile)
        for row in cantus:
            folio = row["Folio"].strip()
            link = row["Image link"].strip()
            if link == "" or folio in folio_link:
                continue
            folio_link[folio] = link
    image_links = list(folio_link.values())
    print(image_links)
    ids_image_links = natsorted(extract_ids(image_links))
    ids_uris = natsorted(extract_ids(uris))
    print(ids_image_links)
    print(ids_uris)
    for i in ids_uris:
        if i in ids_image_links:
            link = ids_image_links[ids_image_links.index(i)]
        else:
            link = ""
        print("{} {}".format(i, link))
