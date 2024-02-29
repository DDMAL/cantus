from unittest import TestCase
from typing import List, Tuple
from cantusdata.helpers.mei_processing.bounding_box_utils import (
    combine_bounding_boxes,
    combine_bounding_boxes_single_system,
)
from cantusdata.helpers.mei_processing.mei_parsing_types import Zone


class TestBoundingBoxUtils(TestCase):

    def test_combine_bounding_boxes_single_system(self) -> None:
        bounding_boxes: List[Zone] = [
            {"coordinates": (0, 0, 1, 1), "rotate": 0},
            {"coordinates": (1, 1, 2, 2), "rotate": 0},
        ]
        combined_box = combine_bounding_boxes_single_system(bounding_boxes)
        expected_combined_box = {"coordinates": (0, 0, 2, 2), "rotate": 0.0}
        self.assertEqual(combined_box, expected_combined_box)

    def test_combine_bounding_boxes(self) -> None:
        bounding_boxes: List[Tuple[Zone, int]] = [
            ({"coordinates": (0, 0, 1, 1), "rotate": 0.0}, 1),
            ({"coordinates": (1, 1, 2, 2), "rotate": 0.0}, 1),
            ({"coordinates": (2, 1, 3, 2), "rotate": 0.0}, 2),
            ({"coordinates": (3, 3, 4, 4), "rotate": 0.0}, 2),
            ({"coordinates": (4, 3, 5, 6), "rotate": 0.0}, 2),
            ({"coordinates": (8, 8, 9, 10), "rotate": 0.0}, 3),
        ]
        combined_boxes = combine_bounding_boxes(bounding_boxes)
        expected_combined_boxes = [
            {"coordinates": (0, 0, 2, 2), "rotate": 0.0},
            {"coordinates": (2, 1, 5, 6), "rotate": 0.0},
            {"coordinates": (8, 8, 9, 10), "rotate": 0.0},
        ]
        self.assertEqual(combined_boxes, expected_combined_boxes)
