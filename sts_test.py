import logging.config
import unittest

import numpy
import numpy.testing

import sts
from card import Card
from deck import Deck
from monster import Monster

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)


class TestDamage(unittest.TestCase):
    def test_scaling_damage(self):
        self.assertEqual("O(1)",
                         sts.format_scaling_damage([17, -0.0, -0.0, 0]))

        self.assertEqual("O(7*n)",
                         sts.format_scaling_damage([17, 6.9, 0.2, 0]))

        self.assertEqual("O(7*n + 1*n^2)",
                         sts.format_scaling_damage([17, 6.9, 1.3, 0]))

        self.assertEqual("O(7*n + 1*n^2 + 4*n^3)",
                         sts.format_scaling_damage([17, 6.9, 1.3, 4.0]))

    def test_get_frontloaded_damage(self):
        self.assertEqual(6, sts.get_frontloaded_damage([6]))
        self.assertEqual(9, sts.get_frontloaded_damage([6, 6]))
        self.assertEqual(12, sts.get_frontloaded_damage([6, 6], False))

    def test_curve_fit(self):
        coefficients, residuals, fit = sts.curve_fit(list(range(10)), [2]*10)
        self.assertAlmostEqual(2.0, coefficients[0])
        self.assertAlmostEqual(0.0, coefficients[1])
        self.assertAlmostEqual(0.0, residuals[0])
        self.assertCountEqual([2.0]*10, fit)

    def test_create_scatter_plot_data(self):
        values_by_trial = [[1, 2, 8], [1, 3, 8]]
        scatter_data, size, sizes_by_value = sts.create_scatter_plot_data(
            values_by_trial)
        print(sts.create_scatter_plot_data(values_by_trial))
        self.assertEqual({'turns': [0, 1, 1, 2], 'value': [
                         1, 2, 3, 8]}, scatter_data)
        self.assertEqual([100.0, 50.0, 50.0, 100.0], size)
        self.assertEqual([{1: 100.0}, {2: 50.0, 3: 50.0},
                         {8: 100.0}], sizes_by_value)

    def test_histogram_values(self):
        values_by_trial = [[1, 2, 8], [1, 3, 8]]
        # hist, bin_edges
        expected = (([2], [1, 2]),
                    ([1, 1], [2, 3, 4]),
                    ([2], [8, 9]))
        results = sts.histogram(values_by_trial)
        print(results[0])
        print(results[1])
        print(results[2])

        for i in range(len(results)):
            self.assertCountEqual(expected[i][0], results[i][0])
            self.assertCountEqual(expected[i][1], results[i][1])

    def test_histogram_values_ragged(self):
        values_by_trial = [[1, 8], [1, -1], [1, 8]]
        # hist, bin_edges
        expected = (([3], [1, 2]),
                    ([2], [8, 9]))
        results = sts.histogram(values_by_trial)
        print(results[0])
        print(results[1])

        for i in range(len(results)):
            self.assertCountEqual(expected[i][0], results[i][0])
            self.assertCountEqual(expected[i][1], results[i][1])

    def test_pad_to_dense(self):
        result = sts.pad_to_dense(numpy.array([[1, 2], [1]]))
        numpy.testing.assert_equal(numpy.array([[1, 2], [1, -1]]), result)

    def test_pad_to_dense_empty(self):
        numpy.testing.assert_equal(numpy.array([]), sts.pad_to_dense([]))

    def test_trial_stats_damage(self):
        ts = sts.TrialStats()
        ts.add_monster_damage([1, 1, 2])
        ts.add_monster_damage([3, 1, -1])
        ts.finish()
        numpy.testing.assert_equal(numpy.array(
            [2, 1, 2]), ts.average_monster_damage)


if __name__ == '__main__':
    unittest.main()
