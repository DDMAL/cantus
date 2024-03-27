"""
Module containing utilities for the manipulation of bounding boxes 
obtained from MEI files.
"""

from typing import List, Tuple, Dict
import json
from collections import defaultdict
from .mei_parsing_types import Zone


def combine_bounding_boxes_single_system(bounding_boxes: List[Zone]) -> Zone:
    """
    Combing a list of bounding boxes contained within a single system into
    one bounding box with no rotation.

    NOTE: This function does not handle cases where any of the bounding boxes
    has a rotation != 0. The rotation is currently ignored, but Issue #834 has
    been created to rectify this.

    :param bounding_boxes: A list of bounding boxes. See mei_parsing_types.Zone for
        the structure of a bounding box.
    :return: A single bounding box that contains the contents of all the given
        bounding boxes and has rotation = 0.
    """
    # Collect the upper-left ("ulx", "uly") and lower-right ("lrx", "lry") vertex
    # coordinates of each bounding box
    ulx_list: List[int] = []
    uly_list: List[int] = []
    lrx_list: List[int] = []
    lry_list: List[int] = []
    for box in bounding_boxes:
        ulx_list.append(box["coordinates"][0])
        uly_list.append(box["coordinates"][1])
        lrx_list.append(box["coordinates"][2])
        lry_list.append(box["coordinates"][3])
    comb_ulx = min(ulx_list)
    comb_uly = min(uly_list)
    comb_lrx = max(lrx_list)
    comb_lry = max(lry_list)

    return {"coordinates": (comb_ulx, comb_uly, comb_lrx, comb_lry), "rotate": 0}


def combine_bounding_boxes(bounding_boxes: List[Tuple[Zone, int]]) -> List[Zone]:
    """
    Combine bounding boxes that may cross multiple systems. This function
    takes a list of bounding boxes and the system number that each box
    belongs to, and returns a list of bounding boxes, one for each system.

    :param bounding_boxes: A list of 2-tuples, each containing (1) a bounding
        box and (2) the system number that the bounding box belongs to.
    :return: A list of bounding boxes, one for each system.
    """
    # Create a dictionary to store the bounding boxes for each system
    system_boxes: Dict[int, List[Zone]] = defaultdict(list)
    for box, system in bounding_boxes:
        system_boxes[system].append(box)

    # Combine the bounding boxes for each system, in system order
    combined_boxes = []
    for _, boxes in sorted(system_boxes.items()):
        combined_boxes.append(combine_bounding_boxes_single_system(boxes))

    return combined_boxes


def stringify_bounding_boxes(bounding_boxes: List[Zone]) -> str:
    """
    Convert a list of bounding box types to a string for indexing. The
    string encodes some JSON, an array of objects, each of which
    represents a bounding box:

        [
            {"ulx":  , # X-coordinate of upper left corner of box
            "uly":  , # Y-coordinate of upper left corner of box
            "width": , # Height of the box
            "height":  }, # Width of the box
            ...
        ]

    :param bounding_box: A list of bounding boxes (Zone type)
    :return: A string representation of the bounding boxes
    """
    bbox_strings: List[Dict[str, int]] = []
    for box in bounding_boxes:
        ulx = box["coordinates"][0]
        uly = box["coordinates"][1]
        width = box["coordinates"][2] - box["coordinates"][0]  # lrx - ulx
        height = box["coordinates"][3] - box["coordinates"][1]  # uly - lry
        bbox_strings.append({"ulx": ulx, "uly": uly, "width": width, "height": height})
    return json.dumps(bbox_strings)
