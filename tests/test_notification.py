import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1] / 'skills' / 'pushplus-notification'
spec = importlib.util.spec_from_file_location('notify', SKILL / 'scripts' / 'send_notification.py')
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copy(SKILL / 'notification-template.txt', self.root)
        (self.root / '.env').write_text('PUSHPLUS_TOKEN="test-secret"\n', encoding='utf-8-sig')
        self.env = patch.dict(os.environ, {'PUSHPLUS_TOKEN': ''})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.data = dict(task_id='thread:task1', task='测试任务', summary='已完成中文、引号"与换行\n内容。')

    def test_payload_and_duplicate(self):
        calls = []
        def transport(payload):
            calls.append(payload)
            return {'code': 200, 'data': 'abc123'}
        first = notify.send(self.data, self.root, transport)
        second = notify.send(self.data, self.root, transport)
        self.assertEqual(first['status'], 'accepted')
        self.assertEqual(second['previous_status'], 'accepted')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['channel'], 'wechat')
        self.assertEqual(calls[0]['token'], 'test-secret')
        self.assertNotIn('topic', calls[0])
        self.assertNotIn('验证：', calls[0]['content'])
        self.assertNotIn('test-secret', json.dumps(first))

    def test_timeout_is_unknown_and_not_retried(self):
        def transport(payload):
            raise TimeoutError('test-secret')
        result = notify.send(self.data, self.root, transport)
        self.assertEqual(result['status'], 'unknown')
        self.assertNotIn('test-secret', json.dumps(result))
        self.assertEqual(notify.send(self.data, self.root, transport)['status'], 'duplicate_skipped')

    def test_business_rejection_does_not_echo_upstream_secret(self):
        result = notify.send(self.data, self.root, lambda p: {'code': 905, 'msg': 'test-secret'})
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['code'], 905)
        self.assertNotIn('test-secret', json.dumps(result))

    def test_bad_response_is_unknown(self):
        self.assertEqual(notify.send(self.data, self.root, lambda p: [])['status'], 'unknown')

    def test_missing_token_stops_before_transport(self):
        (self.root / '.env').write_text('PUSHPLUS_TOKEN=\n')
        with self.assertRaises(ValueError):
            notify.send(self.data, self.root, lambda p: self.fail('network must not run'))
        self.assertFalse((self.root / '.state').exists())

    def test_environment_precedence(self):
        with patch.dict(os.environ, {'PUSHPLUS_TOKEN': 'env-token'}):
            self.assertEqual(notify.read_token(self.root), 'env-token')

    def test_template_optional_fields_and_validation(self):
        self.data.update(verification='测试通过', artifact_url='https://example.com/result')
        msg = notify.build_message(self.data, self.root)
        self.assertIn('验证：测试通过', msg['content'])
        self.assertIn('产物：https://example.com/result', msg['content'])
        self.data['artifact_url'] = 'D:/private/file.txt'
        with self.assertRaises(ValueError):
            notify.build_message(self.data, self.root)


if __name__ == '__main__':
    unittest.main()
