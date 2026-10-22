import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'kakao_daily.py'
spec = importlib.util.spec_from_file_location('kakao_daily', MODULE)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


class DeliveryTests(unittest.TestCase):
    def test_old_brief_is_rejected(self):
        with self.assertRaises(k.DeliveryError):
            k.parse_brief(b'<header>2026.10.22</header><h3>A</h3>', '2026-10-23')

    def test_today_but_incomplete_brief_is_rejected(self):
        with self.assertRaises(k.DeliveryError):
            k.parse_brief(b'<header>2026.10.23</header><h3>A</h3>', '2026-10-23')

    def test_unconsented_recipient_is_rejected(self):
        with self.assertRaises(k.DeliveryError):
            k.recipients('[{"to":"01000000000"}]', 50)

    def test_recipient_limit_and_duplicates(self):
        person = {'to': '01000000000', 'consent': True}
        for data, limit in [([person, person], 50), ([person, person], 1), ([], 50)]:
            with self.subTest(data=data, limit=limit), self.assertRaises(k.DeliveryError):
                k.recipients(json.dumps(data), limit)

    def test_payload_uses_friend_intersection_and_no_sms(self):
        targets = k.recipients('[{"to":"01000000000","consent":true}]', 50)
        body = k.payload('@test', targets, 'test', k.BASE)
        self.assertEqual(body['targeting'], 'I')
        self.assertIs(body['messages'][0]['useSmsFailover'], False)
        self.assertEqual(body['messages'][0]['buttons'][0]['linkMobile'], k.BASE)
        self.assertNotIn('consent', body['messages'][0])

    def test_summary_under_400(self):
        text = k.message_text('2026-10-23', ['가' * 300] * 3)
        self.assertLessEqual(len(text), 400)
        self.assertIn('2026.10.23', text)

    def test_hmac_signature_known_vector(self):
        self.assertEqual(k.signature('GET', '/test', '1', 'access', 'secret'),
                         '3OnJ5NIf96VHA+COTkIU8zsZwtH+xosO/ePpfZJLz2c=')

    def test_result_processing_not_reported_delivered(self):
        sens = object.__new__(k.Sens)
        sens.call = MagicMock(return_value={'statusCode': '202', 'messages': [
            {'messageStatusName': 'success'}]})
        self.assertEqual(sens.results('dummy', 3), {'success': 1, 'fail': 0, 'processing': 2})

    def test_result_pagination(self):
        sens = object.__new__(k.Sens)
        sens.call = MagicMock(side_effect=[
            {'statusCode': '202', 'messages': [{'messageStatusName': 'success'}],
             'hasMore': True, 'nextToken': 'next'},
            {'statusCode': '202', 'messages': [{'messageStatusName': 'fail'}]}])
        self.assertEqual(sens.results('dummy', 2), {'success': 1, 'fail': 1, 'processing': 0})

    def test_failed_status_lookup_is_not_success(self):
        sens = object.__new__(k.Sens)
        sens.call = MagicMock(return_value={'statusCode': '500'})
        with self.assertRaises(k.DeliveryError):
            sens.results('dummy', 1)

    def test_duplicate_run_never_posts(self):
        with patch.object(k, 'datetime') as clock, patch.object(k, 'Sens') as sens_class, \
                patch.object(k, 'Ledger') as ledger_class, patch.object(k, 'reconcile') as rec:
            clock.now.return_value = datetime(2026, 10, 23, 8, 10, tzinfo=k.KST)
            ledger_class.return_value.read.return_value = ({'request_id': 'existing'}, 'sha')
            k.run(True)
            sens_class.return_value.call.assert_not_called()
            rec.assert_called_once()

    def test_uncertain_send_is_locked(self):
        with patch.object(k, 'datetime') as clock, patch.object(k, 'Sens') as sens_class, \
                patch.object(k, 'Ledger') as ledger_class:
            clock.now.return_value = datetime(2026, 10, 23, 8, 10, tzinfo=k.KST)
            ledger_class.return_value.read.return_value = ({'status': 'pending'}, 'sha')
            with self.assertRaises(k.DeliveryError):
                k.run(True)
            sens_class.return_value.call.assert_not_called()

    def test_night_send_never_calls_provider(self):
        with patch.object(k, 'datetime') as clock, patch.object(k, 'Sens') as sens_class:
            clock.now.return_value = datetime(2026, 10, 23, 7, 59, tzinfo=k.KST)
            with self.assertRaises(k.DeliveryError):
                k.run(True)
            sens_class.assert_not_called()

    def test_preview_never_initializes_provider(self):
        with patch.object(k, 'verify_publication', return_value=(k.BASE, ['A', 'B', 'C'], 'hash')), \
                patch.object(k, 'Sens') as sens_class, patch('builtins.print'):
            k.run(False)
            sens_class.assert_not_called()


if __name__ == '__main__':
    unittest.main()
