import csv
import sys
import pprint as pp
from natsort import natsorted

def extract_ids(str_list):
    tmp_str_list = remove_longest_common_string(str_list, 'left')
    print(tmp_str_list)
    tmp_str_list = remove_longest_common_string(tmp_str_list, 'right')
    print(tmp_str_list)
    return tmp_str_list


def remove_longest_common_string(str_list, align='left'):
    longest_str = max(str_list, key=len)
    max_length = len(longest_str)
    if align == 'left':
        norm_str_list = [s.ljust(max_length) for s in str_list]
    elif align == 'right':
        norm_str_list = [s.rjust(max_length) for s in str_list]    
    s1 = norm_str_list[0]
    diffs = []
    for s2 in norm_str_list[1:]:
        [diffs.append(i) for i in range(max_length) if s1[i] != s2[i]]
    diffs_set = set(diffs)
    print(diffs_set)
    mismatch_start = min(diffs_set)
    mismatch_end = max(diffs_set)
    return [s[mismatch_start:mismatch_end+1].strip() for s in norm_str_list]


if __name__ == '__main__':
    cantus_csv = sys.argv[1]
    mapping_csv = sys.argv[2]
    folio_link = {}
    uris = []
    with open(cantus_csv) as csvfile:
        cantus = csv.DictReader(csvfile)
        for row in cantus:
            folio = row['Folio'].strip()
            link = row['Image link'].strip()
            if link == '' or folio in folio_link:
                continue
            folio_link[folio] = link
    image_links = list(folio_link.values())
    with open(mapping_csv) as csvfile:
        mapping = csv.DictReader(csvfile)
        for row in mapping:
            uri = row['uri'].strip()
            uris.append(uri)
    print(image_links)
    ids_image_links = natsorted(extract_ids(image_links))
    print(uris)
    ids_uris = natsorted(extract_ids(uris))
    print(ids_image_links)
    print(ids_uris)
    for i in ids_uris:
        if i in ids_image_links:
            link = ids_image_links[ids_image_links.index(i)]
        else:
            link = ''    
        print('{} {}'.format(i, link))
    
