from itertools import combinations
from operator import le
from sre_constants import SUCCESS
import numpy as np
from numpy.linalg import norm
from scipy.spatial import distance
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
                    # coord1 = np.array(zones[z1]["coordinates"])
                    # coord2 = np.array(zones[z2]["coordinates"])
                    # x = cosine_similarity(coord1, coord2)
                    # cosine_similarities.append(x)
                    # if x > 0.9999:
                    #     pass
                    if zones[z1] == zones[z2]:
                        print(f"\tIdentical bounding box: {z1} {z2}")


def cosine_similarity(v1, v2):
    # similarity = v1.dot(v2) / (norm(v1) * norm(v2))
    similarity = distance.euclidean(v1, v2)
    if np.isnan(similarity):
        print("nan")
    return similarity


if __name__ == "__main__":
    run()
