import unittest
from os.path import join
import io
from contextlib import redirect_stdout

from praatio import textgrid
from praatio.utilities.constants import Interval, Point, POINT_TIER
from praatio.utilities import constants
from praatio.utilities import errors

from tests.praatio_test_case import PraatioTestCase
from tests.testing_utils import makeIntervalTier, makePointTier


class TestPointTier(PraatioTestCase):
    def test__eq__(self):
        sut = makePointTier(name="foo", points=[], minT=1, maxT=4)
        pointTier = makePointTier(name="foo", points=[], minT=1, maxT=4)
        intervalTier = makeIntervalTier()
        point1 = Point(1.0, "hello")
        point2 = Point(3.0, "world")

        # must be the same type
        self.assertEqual(sut, pointTier)
        self.assertNotEqual(sut, intervalTier)

        # must have the same entries
        sut.insertEntry(point1)
        self.assertNotEqual(sut, pointTier)

        # just having the same number of entries is not enough
        pointTier.insertEntry(point2)
        self.assertNotEqual(sut, pointTier)

        sut.insertEntry(point2)
        pointTier.insertEntry(point1)
        self.assertEqual(sut, pointTier)

        # must have the same name
        pointTier.name = "bar"
        self.assertNotEqual(sut, pointTier)
        pointTier.name = "foo"
        self.assertEqual(sut, pointTier)

        # must have the same min/max timestamps
        pointTier.minTimestamp = 0.5
        self.assertNotEqual(sut, pointTier)

        pointTier.minTimestamp = 1
        pointTier.maxTimestamp = 5
        self.assertNotEqual(sut, pointTier)

        sut.maxTimestamp = 5
        self.assertEqual(sut, pointTier)

    def test__len__returns_the_number_of_points_in_the_point_tier(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")

        sut = makePointTier(points=[])

        self.assertEqual(len(sut), 0)

        sut.insertEntry(point1)
        self.assertEqual(len(sut), 1)

        sut.insertEntry(point2)
        self.assertEqual(len(sut), 2)

        sut.deleteEntry(point1)
        self.assertEqual(len(sut), 1)

        sut.deleteEntry(point2)
        self.assertEqual(len(sut), 0)

    def test__iter__iterates_through_points_in_the_point_tier(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")

        sut = makePointTier(points=[point1, point2])

        seenPoints = []
        for point in sut:
            seenPoints.append(point)

        self.assertEqual(seenPoints, [point1, point2])

    def test__reversed__iterates_through_points_in_reverse_order(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")

        sut = makePointTier(points=[point1, point2])

        reversedPoints = list(reversed(sut))
        self.assertEqual(reversedPoints, [point2, point1])

    def test__contains__checks_if_point_exists(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")

        sut = makePointTier(points=[point1, point2])

        self.assertIn(point1, sut)
        self.assertIn(point2, sut)
        self.assertNotIn(point3, sut)

    def test__getitem__with_integer_index(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")

        sut = makePointTier(points=[point1, point2])

        self.assertEqual(sut[0], point1)
        self.assertEqual(sut[1], point2)
        self.assertEqual(sut[-1], point2)
        self.assertEqual(sut[-2], point1)

        with self.assertRaises(IndexError):
            _ = sut[2]

    def test__getitem__with_slice(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")

        sut = makePointTier(points=[point1, point2, point3])

        self.assertEqual(sut[1:3], [point2, point3])
        self.assertEqual(sut[2:], [point3])
        self.assertEqual(sut[:-1], [point1, point2])
        self.assertEqual(sut[::2], [point1, point3])

    def test__setitem__with_integer_index(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")

        sut = makePointTier(points=[point2, point3])

        sut[0] = point1
        self.assertEqual(sut.entries, (point1, point3))

        with self.assertRaises(IndexError):
            sut[-3] = point2

    def test__setitem__with_slice_accepts_lists(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")

        sut = makePointTier(points=[point1, point2, point3])

        sut[1:3] = [[7, "new"]]
        self.assertEqual(sut.entries, (point1, Point(7.0, "new")))

    def test__setitem__with_slice_keeps_entries_sorted(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")
        point4 = Point(7.0, "foo")
        point5 = Point(9.5, "bar")

        sut = makePointTier(points=[point2, point4])

        sut[1:1] = [point3, point5, point1]
        self.assertEqual(sut.entries, (point1, point2, point3, point4, point5))

    def test__delitem__with_integer_index(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")

        sut = makePointTier(points=[point1, point2])

        del sut[1]
        self.assertEqual(sut.entries, (point1,))
        del sut[0]
        self.assertEqual(sut.entries, ())

        with self.assertRaises(IndexError):
            del sut[0]

    def test__delitem__with_slice(self):
        point1 = Point(1, "hello")
        point2 = Point(3.5, "world")
        point3 = Point(5.0, "test")

        sut = makePointTier(points=[point1, point2, point3])

        del sut[::2]
        self.assertEqual(sut.entries, (point2,))

    def test_print_format(self):
        sut = makePointTier()
        with io.StringIO() as buf, redirect_stdout(buf):
            print(sut)
            self.assertEqual(
                buf.getvalue(),
                "PointTier('pitch_values', [(1.3, '55'), (3.7, '99')], 0.0, 5.0)\n"
            )

    def test__repr__round_trip(self):
        from praatio.textgrid import PointTier
        sut = makePointTier()
        reconstructed = eval(repr(sut))
        self.assertEqual(sut, reconstructed)

    def test_inequivalence_with_non_point_tiers(self):
        sut = makePointTier()
        self.assertNotEqual(sut, 55)

    def test_append_tier_with_mixed_type_throws_exception(self):
        pointTier = makePointTier()
        intervalTier = textgrid.IntervalTier(
            "words",
            [Interval(1, 2, "hello"), Interval(3.5, 4.0, "world")],
            minT=0,
            maxT=5.0,
        )
        with self.assertRaises(errors.ArgumentError) as _:
            pointTier.appendTier(intervalTier)

    def test_append_tier_with_point_tiers(self):
        pointTier = textgrid.PointTier(
            "pitch_values", [Point(1.3, "55"), Point(3.7, "99")], minT=0, maxT=5
        )
        pointTier2 = textgrid.PointTier(
            "new_pitch_values", [Point(4.2, "153"), Point(7.1, "89")], minT=0, maxT=10
        )
        sut = pointTier.appendTier(pointTier2)
        self.assertEqual(0, sut.minTimestamp)
        self.assertEqual(15, sut.maxTimestamp)
        self.assertEqual(
            [Point(1.3, "55"), Point(3.7, "99"), Point(9.2, "153"), Point(12.1, "89")],
            sut._entries,
        )
        self.assertEqual(POINT_TIER, sut.tierType)

    def test_find_with_point_tiers(self):
        sut = makePointTier(
            points=[
                Point(1, "hello"),
                Point(2.5, "the"),
                Point(3.5, "world"),
            ]
        )
        self.assertEqual([], sut.find("mage", substrMatchFlag=False, usingRE=False))
        self.assertEqual([1], sut.find("the", substrMatchFlag=False, usingRE=False))

        self.assertEqual([], sut.find("mage", substrMatchFlag=True, usingRE=False))
        self.assertEqual([0, 1], sut.find("he", substrMatchFlag=True, usingRE=False))

        self.assertEqual([], sut.find("mage", substrMatchFlag=False, usingRE=True))
        self.assertEqual([0, 1], sut.find("he", substrMatchFlag=False, usingRE=True))
        self.assertEqual(
            [0, 1, 2], sut.find("[eo]", substrMatchFlag=False, usingRE=True)
        )

    def test_point_tier_creation_with_no_times(self):
        with self.assertRaises(errors.TimelessTextgridTierException) as cm:
            textgrid.PointTier("pitch_values", [], None, None)

        self.assertEqual(
            "All textgrid tiers much have a min and max duration", str(cm.exception)
        )

    def test_crop_raises_error_if_crop_start_time_occurs_after_crop_end_time(self):
        sut = makePointTier()

        with self.assertRaises(errors.ArgumentError) as cm:
            sut.crop(2.1, 1.1, "lax", True)

        self.assertEqual(
            "Crop error: start time (2.1) must occur before end time (1.1)",
            str(cm.exception),
        )

    def test_crop_when_rebase_to_zero_is_true(self):
        pointTier = makePointTier(
            points=[
                Point(0.5, "12"),
                Point(1.3, "55"),
                Point(3.7, "99"),
                Point(4.5, "32"),
            ],
            minT=0,
            maxT=5,
        )
        sut = pointTier.crop(1.0, 3.8, rebaseToZero=True)
        expectedPointTier = makePointTier(
            points=[Point(0.3, "55"), Point(2.7, "99")],
            minT=0,
            maxT=2.8,
        )
        self.assertEqual(expectedPointTier, sut)

    def test_crop_when_rebase_to_zero_is_false(self):
        pointTier = makePointTier(
            points=[
                Point(0.5, "12"),
                Point(1.3, "55"),
                Point(3.7, "99"),
                Point(4.5, "32"),
            ],
            minT=0,
            maxT=5,
        )
        sut = pointTier.crop(1.0, 3.8, rebaseToZero=False)
        expectedPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99")],
            minT=1,
            maxT=3.8,
        )
        self.assertEqual(expectedPointTier, sut)

    def test_dejitter_when_reference_tier_is_interval_tier(self):
        sut = makePointTier(
            points=[
                Point(0.9, "will be modified"),
                Point(2.1, "will also be modified"),
                Point(2.5, "will not be modified"),
                Point(3.56, "will also not be modified"),
            ]
        )
        refInterval = makeIntervalTier(
            intervals=[Interval(1, 2.0, "foo"), Interval(2.65, 3.45, "bar")]
        )
        self.assertSequenceEqual(
            [
                Point(1, "will be modified"),
                Point(2.0, "will also be modified"),
                Point(2.5, "will not be modified"),
                Point(3.56, "will also not be modified"),
            ],
            sut.dejitter(refInterval, 0.1)._entries,
        )

    def test_dejitter_when_reference_tier_is_point_tier(self):
        sut = makePointTier(
            points=[
                Point(0.9, "will be modified"),
                Point(2.1, "will also be modified"),
                Point(2.5, "will not be modified"),
                Point(3.56, "will also not be modified"),
            ]
        )
        refInterval = makePointTier(
            points=[
                Point(1, "foo"),
                Point(2.0, "bar"),
                Point(2.65, "bizz"),
                Point(3.45, "whomp"),
            ]
        )
        self.assertSequenceEqual(
            [
                Point(1, "will be modified"),
                Point(2.0, "will also be modified"),
                Point(2.5, "will not be modified"),
                Point(3.56, "will also not be modified"),
            ],
            sut.dejitter(refInterval, 0.1)._entries,
        )

    def test_erase_region_when_do_shrink_is_true(self):
        pointTier = makePointTier(
            points=[
                Point(0.5, "12"),
                Point(1.3, "55"),
                Point(3.7, "99"),
                Point(4.5, "32"),
            ],
            minT=0,
            maxT=5,
        )
        sut = pointTier.eraseRegion(1.0, 2.1, doShrink=True)
        expectedPointTier = makePointTier(
            points=[Point(0.5, "12"), Point(2.6, "99"), Point(3.4, "32")],
            minT=0,
            maxT=3.9,
        )
        self.assertEqual(expectedPointTier, sut)

    def test_erase_region_when_do_shrink_is_false(self):
        pointTier = makePointTier(
            points=[
                Point(0.5, "12"),
                Point(1.3, "55"),
                Point(3.7, "99"),
                Point(4.5, "32"),
            ]
        )
        sut = pointTier.eraseRegion(1.0, 2.1, doShrink=False)
        expectedPointTier = makePointTier(
            points=[Point(0.5, "12"), Point(3.7, "99"), Point(4.5, "32")],
        )
        self.assertEqual(expectedPointTier, sut)

    def test_get_values_at_points_when_fuzzy_matching_is_false(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )
        dataList = [
            (0.9, 100, 55),
            (1.3, 34, 92),
            (1.5, 32, 15),
            (1.8, 21, 34),
            (4.5, 31, 2),
            (4.8, 99, 44),
        ]

        self.assertEqual(
            [(1.3, 34, 92), (), (4.5, 31, 2)],
            sut.getValuesAtPoints(dataList, fuzzyMatching=False),
        )

        dataList2 = [(0.9, 100), (1.3, 34), (1.5, 32), (1.8, 21)]
        self.assertEqual(
            [(1.3, 34), (), ()],
            sut.getValuesAtPoints(dataList2, fuzzyMatching=False),
        )

    def test_get_values_at_points_when_fuzzy_matching_is_true(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        dataList = [
            (0.9, 100, 55),
            (1.3, 34, 92),
            (1.5, 32, 15),
            (1.8, 21, 34),
            (4.5, 31, 2),
            (4.8, 99, 44),
        ]
        self.assertEqual(
            [(1.3, 34, 92), (4.5, 31, 2), (4.5, 31, 2)],
            sut.getValuesAtPoints(dataList, fuzzyMatching=True),
        )

        dataList2 = [(0.9, 100), (1.3, 34), (1.5, 32), (1.8, 21)]
        self.assertEqual(
            [(1.3, 34), (1.8, 21), (1.8, 21)],
            sut.getValuesAtPoints(dataList2, fuzzyMatching=True),
        )

    def test_insert_point_at_start_of_point_tier(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(Point(0.5, "21"))

        self.assertEqual(
            [Point(0.5, "21"), Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            sut._entries,
        )

    def test_insert_point_at_middle_of_point_tier(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(Point(3.9, "21"))

        self.assertEqual(
            [Point(1.3, "55"), Point(3.7, "99"), Point(3.9, "21"), Point(4.5, "32")],
            sut._entries,
        )

    def test_insert_entry_works_with_points_tuples_or_lists(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(Point(3.9, "21"))
        sut.insertEntry((4.0, "23"))
        sut.insertEntry((4.1, "99"))

        self.assertEqual(
            [
                Point(1.3, "55"),
                Point(3.7, "99"),
                Point(3.9, "21"),
                Point(4.0, "23"),
                Point(4.1, "99"),
                Point(4.5, "32"),
            ],
            sut._entries,
        )

    def test_insert_point_at_end_of_point_tier(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(Point(4.9, "21"))

        self.assertEqual(
            [Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32"), Point(4.9, "21")],
            sut._entries,
        )

    def test_insert_point_when_collision_occurs(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        with self.assertRaises(errors.CollisionError) as _:
            sut.insertEntry(
                Point(3.7, "hello"),
                constants.ErrorReportingMode.ERROR,
                constants.ErrorReportingMode.SILENCE,
            )

    def test_insert_point_when_collision_occurs_and_merge(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(
            Point(3.7, "hello"),
            constants.IntervalCollision.MERGE,
            constants.ErrorReportingMode.SILENCE,
        )
        self.assertEqual(
            [Point(1.3, "55"), Point(3.7, "99-hello"), Point(4.5, "32")],
            sut._entries,
        )

    def test_insert_point_when_collision_occurs_and_replace(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut.insertEntry(
            Point(3.7, "hello"),
            constants.IntervalCollision.REPLACE,
            constants.ErrorReportingMode.SILENCE,
        )
        self.assertEqual(
            [Point(1.3, "55"), Point(3.7, "hello"), Point(4.5, "32")],
            sut._entries,
        )

    def test_edit_timestamps_throws_error_if_reporting_mode_is_invalid(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        with self.assertRaises(errors.WrongOption) as _:
            sut.editTimestamps(
                2.0,
                "cats",
            )

    def test_edit_timestamps_can_make_points_appear_later(self):
        originalPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut = originalPointTier.editTimestamps(0.4)

        expectedPointTier = makePointTier(
            points=[Point(1.7, "55"), Point(4.1, "99"), Point(4.9, "32")],
        )
        self.assertEqual(expectedPointTier, sut)

    def test_edit_timestamps_can_make_points_appear_earlier(self):
        originalPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut = originalPointTier.editTimestamps(-0.4)

        expectedPointTier = makePointTier(
            points=[Point(0.9, "55"), Point(3.3, "99"), Point(4.1, "32")],
        )
        self.assertEqual(expectedPointTier, sut)

    def test_edit_timestamp_can_raise_exception_when_reporting_mode_is_silence(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            minT=0,
            maxT=5,
        )

        with self.assertRaises(errors.OutOfBounds) as _:
            sut.editTimestamps(
                -1.4,
                constants.ErrorReportingMode.ERROR,
            )
        with self.assertRaises(errors.OutOfBounds) as _:
            sut.editTimestamps(
                1.4,
                constants.ErrorReportingMode.ERROR,
            )

    def test_edit_timestamp_can_exceed_maxtimestamp_when_reporting_mode_is_silence(
        self,
    ):
        originalPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            maxT=5,
        )

        sut = originalPointTier.editTimestamps(
            1.4, constants.ErrorReportingMode.SILENCE
        )
        expectedPointTier = makePointTier(
            points=[Point(2.7, "55"), Point(5.1, "99"), Point(5.9, "32")],
            maxT=5.9,
        )
        self.assertEqual(expectedPointTier, sut)

    def test_edit_timestamp_drops_points_that_are_moved_before_zero(self):
        originalPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        sut = originalPointTier.editTimestamps(
            -1.4, constants.ErrorReportingMode.SILENCE
        )
        expectedPointTier = makePointTier(
            points=[Point(2.3, "99"), Point(3.1, "32")],
        )
        self.assertEqual(expectedPointTier, sut)

    def test_insert_space(self):
        originalPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            maxT=5,
        )

        sut = originalPointTier.insertSpace(2.0, 1.1)
        predictedPointTier = makePointTier(
            points=[Point(1.3, "55"), Point(4.8, "99"), Point(5.6, "32")],
            maxT=6.1,
        )
        self.assertEqual(predictedPointTier, sut)

    def test_to_zero_crossings(self):
        wavFN = join(self.dataRoot, "bobby.wav")
        tgFN = join(self.dataRoot, "bobby.TextGrid")

        tg = textgrid.openTextgrid(tgFN, False)
        originalTier = tg.getTier("pitch")

        expectedFN = join(self.dataRoot, "bobby_boundaries_at_zero_crossings.TextGrid")
        expectedTg = textgrid.openTextgrid(expectedFN, False)
        expectedTier = expectedTg.getTier("pitch")

        sut = originalTier.toZeroCrossings(wavFN)
        sut.name = "auto"

        # TODO: There are small differences between praat and praatio's
        #       zero-crossing calculations.
        self.assertEqual(len(expectedTier.entries), len(sut.entries))
        for entry, sutEntry in zip(expectedTier.entries, sut.entries):
            self.assertAlmostEqual(entry.time, sutEntry.time, 3)

    def test_validate_throws_error_if_points_are_not_in_sequence(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
        )

        self.assertTrue(sut.validate())
        sut._entries.append(Point(3.9, "21"))
        self.assertFalse(sut.validate(constants.ErrorReportingMode.SILENCE))
        with self.assertRaises(errors.TextgridStateError) as _:
            sut.validate(constants.ErrorReportingMode.ERROR)

    def test_validate_throws_error_if_points_are_less_than_minimum_time(self):
        sut = makePointTier(
            points=[Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            minT=0,
        )

        self.assertTrue(sut.validate())
        sut.minTimestamp = 2.0
        self.assertFalse(sut.validate(constants.ErrorReportingMode.SILENCE))
        with self.assertRaises(errors.OutOfBounds) as _:
            sut.validate(constants.ErrorReportingMode.ERROR)

    def test_validate_throws_error_if_points_are_more_than_maximum_time(self):
        sut = makePointTier(
            [Point(1.3, "55"), Point(3.7, "99"), Point(4.5, "32")],
            maxT=5,
        )

        self.assertTrue(sut.validate())
        sut.maxTimestamp = 3.0
        self.assertFalse(sut.validate(constants.ErrorReportingMode.SILENCE))
        with self.assertRaises(errors.OutOfBounds) as _:
            sut.validate(constants.ErrorReportingMode.ERROR)


if __name__ == "__main__":
    unittest.main()
