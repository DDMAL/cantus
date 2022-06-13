from itertools import combinations
from operator import le
from sre_constants import SUCCESS
import numpy as np
from numpy.linalg import norm
import os
from pprint import pprint

from mei_parse import parse, query_pitch_sequence


def run():
    for manuscript in ["Salzinnes", "Einsiedeln"]:
        for root, _, files in os.walk(manuscript):
            for f in sorted(files):
                if not f.endswith(".mei"):
                    continue
                filepath = os.path.join(root, f)
                print(filepath)
                zones, _, _ = parse(filepath)
                cosine_similarities = []
                for z1, z2 in combinations(zones.keys(), 2):
                    coord1 = np.array(zones[z1]["coordinates"])
                    coord2 = np.array(zones[z2]["coordinates"])
                    x = cosine_similarity(coord1, coord2)
                    cosine_similarities.append(x)
                    if x == 1.0:
                        print(z1, z2, "same bounding box")
                        break
                        

def cosine_similarity(v1, v2):
    v1_l2_norm = norm(v1)
    v2_l2_norm = norm(v2)
    dot_prod = np.matmul(v1, v2)
    return dot_prod/(v1_l2_norm * v2_l2_norm)
    
    

if __name__ == "__main__":
    run()
