"""
Module containing utilities for the manipulation of bounding boxes 
obtained from MEI files.
"""

from typing import List, Tuple, Dict
from .mei_parsing_types import Zone


def combine_bounding_boxes_single_system(bounding_boxes: List[Zone]) -> Zone:
    """
    Combing a list of bounding boxes contained within a single system into
    one bounding box with no rotation.

    NOTE: This function does not handle cases where any of the bounding boxes
    has a rotation != 0. The rotation is currently ignored, but Issue #834 has
    been created to rectify this.

    :param bounding_boxes: A list of bounding boxes
    :return: A single bounding box that contains the contents of all the given
        bounding boxes and has rotation = 0.
    """
    ulx_list = []
    uly_list = []
    lrx_list = []
    lry_list = []
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
    system_boxes: Dict[int, List[Zone]] = {}
    for box, system in bounding_boxes:
        if system not in system_boxes:
            system_boxes[system] = []
        system_boxes[system].append(box)

    # Combine the bounding boxes for each system, in system order
    combined_boxes = []
    for _, boxes in sorted(system_boxes.items()):
        combined_boxes.append(combine_bounding_boxes_single_system(boxes))

    return combined_boxes
