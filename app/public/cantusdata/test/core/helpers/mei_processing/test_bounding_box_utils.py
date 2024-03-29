from unittest import TestCase
from typing import List, Tuple
from cantusdata.helpers.mei_processing.bounding_box_utils import (
    combine_bounding_boxes,
    combine_bounding_boxes_single_system,
    stringify_bounding_boxes,
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
        """
        The combine_bounding_boxes function combines a set of bounding
        boxes on one or more systems. The function takes a list of
        2-tuples, each containing a bounding box (object of type Zone)
        and the system number on which the bounding box is found.
        """
        with self.subTest("Test combining bounding boxes from single system"):
            bounding_boxes_one_sys: List[Tuple[Zone, int]] = [
                ({"coordinates": (4, 3, 5, 6), "rotate": 0.0}, 2),
                ({"coordinates": (2, 1, 3, 2), "rotate": 0.0}, 2),
                ({"coordinates": (3, 3, 4, 4), "rotate": 0.0}, 2),
            ]
            combined_boxes_one_sys = combine_bounding_boxes(bounding_boxes_one_sys)
            expected_combined_boxes_one_sys = [
                {"coordinates": (2, 1, 5, 6), "rotate": 0.0},
            ]
            self.assertEqual(combined_boxes_one_sys, expected_combined_boxes_one_sys)
        with self.subTest("Test combining bounding boxes from multiple systems"):
            bounding_boxes_multi_sys: List[Tuple[Zone, int]] = [
                ({"coordinates": (0, 0, 1, 1), "rotate": 0.0}, 2),
                ({"coordinates": (4, 3, 5, 6), "rotate": 0.0}, 3),
                ({"coordinates": (8, 8, 9, 10), "rotate": 0.0}, 1),
                ({"coordinates": (1, 1, 2, 2), "rotate": 0.0}, 2),
                ({"coordinates": (2, 1, 3, 2), "rotate": 0.0}, 3),
                ({"coordinates": (3, 3, 4, 4), "rotate": 0.0}, 3),
            ]
            combined_boxes_multi_sys = combine_bounding_boxes(bounding_boxes_multi_sys)
            expected_combined_boxes_multi_sys = [
                {"coordinates": (8, 8, 9, 10), "rotate": 0.0},
                {"coordinates": (0, 0, 2, 2), "rotate": 0.0},
                {"coordinates": (2, 1, 5, 6), "rotate": 0.0},
            ]
            self.assertEqual(
                combined_boxes_multi_sys, expected_combined_boxes_multi_sys
            )

    def test_stringify_bounding_boxes(self) -> None:
        bounding_boxes: List[Zone] = [
            {"coordinates": (0, 0, 1, 1), "rotate": 0},
            {"coordinates": (2, 3, 5, 8), "rotate": 0.123},
        ]
        stringified_boxes = stringify_bounding_boxes(bounding_boxes)
        expected_stringified_boxes = (
            '[{"ulx": 0, "uly": 0, "width": 1, "height": 1}, '
            '{"ulx": 2, "uly": 3, "width": 3, "height": 5}]'
        )
        self.assertEqual(stringified_boxes, expected_stringified_boxes)
