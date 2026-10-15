"""Regression tests for the McBracket data pipeline.

These guard the two traps that would silently corrupt the public snapshot:

1.  A missing nutrition cell must stay missing (None) — never become a
    fabricated 0. The official table really does contain 0s (diet cola,
    apple slices), so "0" and "absent" must remain distinguishable.
2.  Cross-run merging must never mix prices from a different store or a
    different ordering channel, and an old price must not silently
    override a newer observation.

Run from the repository root:

    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

import fetch_snapshot as fs  # noqa: E402


def row(code, **over):
    """A minimal snapshot row, as the fetcher writes it."""
    base = {
        'code': code,
        'name': f'餐品{code}',
        'menuPriceCents': 2000,
        'quotePriceCents': 2000,
        'quoteNote': None,
        'priceSource': 'calculate-price',
        'nutrition': {'energyKcal': 400, 'protein': 20.0, 'fat': 10.0,
                      'carbohydrate': 40.0, 'sodium': 800},
        'nutritionMatch': 'exact',
        'collectedAt': '2026-10-15 12:00:00',
        'carried': False,
    }
    base.update(over)
    return base


class NutritionParsing(unittest.TestCase):
    TABLE = (
        '[8]{productName,nutritionDescription,energyKj,energyKcal,'
        'protein,fat,carbohydrate,sodium,calcium}:\n'
        '巨无霸,null,2146,513,27,26,42,961,171\n'
        '苹果片,null,133,32,0,0,7,0,18\n'
        '可乐中杯,null,616,147,0,0,36,0,10\n'
    )

    def test_real_zero_stays_zero(self):
        out = fs.parse_nutrition_csv(self.TABLE)
        # Apple slices genuinely carry 0 protein / 0 fat / 0 sodium in the
        # official table — those must not be turned into "missing".
        self.assertEqual(out['苹果片']['sodium'], 0)
        self.assertEqual(out['苹果片']['protein'], 0.0)
        self.assertEqual(out['苹果片']['energyKcal'], 32)
        self.assertEqual(out['巨无霸']['sodium'], 961)

    def test_absent_cell_becomes_none_not_zero(self):
        out = fs.parse_nutrition_csv(
            '[2]{productName,nutritionDescription,energyKj,energyKcal,'
            'protein,fat,carbohydrate,sodium,calcium}:\n'
            '神秘餐,null,100,100,5,,10,20,30\n')
        self.assertEqual(out['神秘餐']['protein'], 5.0)
        self.assertIsNone(out['神秘餐']['fat'])  # empty cell, NOT 0.0

    def test_fully_empty_row_is_all_none(self):
        out = fs.parse_nutrition_csv(
            '[1]{productName,nutritionDescription,energyKj,energyKcal,'
            'protein,fat,carbohydrate,sodium,calcium}:\n'
            '空白餐,null,,,,,,,\n')
        self.assertEqual(set(out['空白餐'].values()), {None})

    def test_columns_are_located_from_the_header(self):
        # Same numbers, reordered columns: values must follow their names.
        out = fs.parse_nutrition_csv(
            '[1]{sodium,productName,energyKcal}:\n'
            '961,巨无霸,513\n')
        self.assertEqual(out['巨无霸']['energyKcal'], 513)
        self.assertEqual(out['巨无霸']['sodium'], 961)
        # Columns the header did not mention stay missing, not zero.
        self.assertIsNone(out['巨无霸']['protein'])

    def test_row_with_wrong_field_count_is_skipped(self):
        out = fs.parse_nutrition_csv(
            '[1]{productName,energyKcal,sodium}:\n'
            '短行,100\n'
            '正常行,200,50\n')
        self.assertNotIn('短行', out)
        self.assertEqual(out['正常行']['sodium'], 50)

    def test_list_payload_and_duplicates(self):
        out = fs.parse_nutrition_csv([
            {'productName': '甲', 'energyKcal': '100', 'sodium': '5'},
            {'productName': '甲', 'energyKcal': '999', 'sodium': '5'},
        ])
        self.assertEqual(out['甲']['energyKcal'], 100)  # first wins


class Money(unittest.TestCase):
    def test_yuan_strings_to_cents(self):
        self.assertEqual(fs.yuan_to_cents('25.5'), 2550)
        self.assertEqual(fs.yuan_to_cents('¥13'), 1300)
        self.assertEqual(fs.yuan_to_cents(13), 1300)
        self.assertIsNone(fs.yuan_to_cents('abc'))
        self.assertIsNone(fs.yuan_to_cents(None))

    def test_quote_cents_tolerate_numeric_strings(self):
        self.assertEqual(fs.to_int_cents(2550), 2550)
        self.assertEqual(fs.to_int_cents('2550'), 2550)
        self.assertIsNone(fs.to_int_cents('25.5'))
        self.assertIsNone(fs.to_int_cents(True))


class MergeCompatibility(unittest.TestCase):
    CHANNEL = {'orderType': 1, 'beType': 1}
    LABEL = '堂食/到店取餐渠道（orderType=1, beType=1）'

    def prev(self, **over):
        base = {'items': [row('1100')], 'store': {'code': '1450713'},
                'channel': dict(self.CHANNEL), 'orderType': self.LABEL}
        base.update(over)
        return base

    def test_same_store_and_channel_merges(self):
        self.assertTrue(fs.compatible_previous(
            self.prev(), '1450713', self.CHANNEL, self.LABEL))

    def test_different_store_never_merges(self):
        prev = self.prev()
        prev['store']['code'] = '9999999'
        self.assertFalse(fs.compatible_previous(
            prev, '1450713', self.CHANNEL, self.LABEL))

    def test_different_channel_never_merges(self):
        prev = self.prev()
        prev['channel'] = {'orderType': 2, 'beType': 2}
        self.assertFalse(fs.compatible_previous(
            prev, '1450713', self.CHANNEL, self.LABEL))

    def test_legacy_file_without_channel_field(self):
        legacy = self.prev()
        del legacy['channel']
        self.assertTrue(fs.compatible_previous(
            legacy, '1450713', self.CHANNEL, self.LABEL))
        legacy['orderType'] = '外送渠道'
        self.assertFalse(fs.compatible_previous(
            legacy, '1450713', self.CHANNEL, self.LABEL))

    def test_empty_previous_is_incompatible(self):
        self.assertFalse(fs.compatible_previous(None, '1450713', self.CHANNEL, self.LABEL))
        self.assertFalse(fs.compatible_previous({}, '1450713', self.CHANNEL, self.LABEL))


class MergeRules(unittest.TestCase):
    NOW = '2026-10-15 21:00:00'

    def test_no_previous_keeps_only_fresh_rows_in_seed_order(self):
        fresh = [row('6102'), row('1100')]
        merged, carried, refreshed, notes = fs.merge_items(fresh, None, self.NOW, [])
        self.assertEqual([r['code'] for r in merged], ['1100', '6102'])
        self.assertEqual(carried, [])
        self.assertEqual(refreshed, [])
        self.assertEqual(notes, [])

    def test_item_absent_today_is_carried_with_its_own_timestamp(self):
        old = row('511781', collectedAt='2026-10-14 11:26:56',
                  quotePriceCents=None, priceSource='query-meals')
        merged, carried, refreshed, notes = fs.merge_items(
            [row('1100')], {'items': [old]}, self.NOW, [])
        by_code = {r['code']: r for r in merged}
        self.assertEqual(carried, ['511781'])
        self.assertTrue(by_code['511781']['carried'])
        self.assertEqual(by_code['511781']['collectedAt'], '2026-10-14 11:26:56')
        self.assertEqual(notes, [])

    def test_stale_row_is_dropped_not_shown(self):
        old = row('511781', collectedAt='2026-10-01 09:00:00')
        merged, carried, refreshed, notes = fs.merge_items(
            [row('1100')], {'items': [old]}, self.NOW, [])
        self.assertNotIn('511781', {r['code'] for r in merged})
        self.assertTrue(any('511781' in n and 'older than' in n for n in notes))

    def test_new_quote_beats_old_quote(self):
        old = row('1100', quotePriceCents=2550, menuPriceCents=2550)
        fresh = [row('1100', quotePriceCents=2250, menuPriceCents=2250,
                     collectedAt=self.NOW)]
        merged, _, _, _ = fs.merge_items(fresh, {'items': [old]}, self.NOW, [])
        self.assertEqual(merged[0]['quotePriceCents'], 2250)

    def test_old_quote_is_inherited_only_when_todays_quote_failed(self):
        old = row('1100', quotePriceCents=2550, collectedAt='2026-10-14 11:26:56')
        fresh = [row('1100', quotePriceCents=None, priceSource='query-meals',
                     quoteNote='calculate-price transport error: boom',
                     collectedAt=self.NOW)]
        merged, _, refreshed, _ = fs.merge_items(fresh, {'items': [old]}, self.NOW, [])
        out = merged[0]
        self.assertEqual(out['quotePriceCents'], 2550)
        self.assertEqual(out['priceSource'], 'calculate-price')
        self.assertEqual(out['quoteCollectedAt'], '2026-10-14 11:26:56')
        self.assertIn('earlier run', out['quoteNote'])
        # Everything else still comes from today's observation.
        self.assertEqual(out['collectedAt'], self.NOW)
        self.assertIn('1100', refreshed)

    def test_nutrition_is_inherited_when_todays_match_failed(self):
        old = row('1100')
        fresh = [row('1100', nutrition=None, nutritionMatch='none')]
        merged, _, _, _ = fs.merge_items(fresh, {'items': [old]}, self.NOW, [])
        self.assertEqual(merged[0]['nutrition']['energyKcal'], 400)
        self.assertEqual(merged[0]['nutritionMatch'], 'exact')

    def test_rows_outside_the_eight_seeds_are_never_carried(self):
        old = row('9999')
        merged, _, _, notes = fs.merge_items(
            [row('1100')], {'items': [old]}, self.NOW, [])
        self.assertEqual([r['code'] for r in merged], ['1100'])
        self.assertTrue(any('outside the eight seeds' in n for n in notes))

    def test_undated_row_is_treated_as_stale(self):
        old = row('511781', collectedAt=None)
        merged, _, _, notes = fs.merge_items(
            [row('1100')], {'items': [old]}, self.NOW, [])
        self.assertNotIn('511781', {r['code'] for r in merged})


if __name__ == '__main__':
    unittest.main()
