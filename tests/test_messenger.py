"""Offline Messenger request tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "dooray" / "scripts"))
import messenger


class RecordingClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, params=None, json_body=None, apply=False, resource_id=None):
        call = (method, path, params, json_body, apply, resource_id)
        self.calls.append(call)
        return {"recorded": call}


class MessengerTests(unittest.TestCase):
    def test_list_channels_is_read_only(self):
        client = RecordingClient()
        result = messenger.list_channels(client=client)
        self.assertEqual(client.calls, [("GET", "/messenger/v1/channels", None, None, False, None)])
        self.assertEqual(result["recorded"], client.calls[0])

    def test_direct_send_uses_singular_member_id_and_explicit_write(self):
        client = RecordingClient()
        messenger.direct_send("member-1", "Hello", apply=True, client=client)
        self.assertEqual(client.calls, [("POST", "/messenger/v1/channels/direct-send", None,
                                         {"text": "Hello", "organizationMemberId": "member-1"},
                                         True, "member-1")])

    def test_send_channel_message_uses_logs_endpoint_and_explicit_write(self):
        client = RecordingClient()
        messenger.send_channel_message("channel-1", "Hello", client=client)
        self.assertEqual(client.calls, [("POST", "/messenger/v1/channels/channel-1/logs", None,
                                         {"text": "Hello"}, False, "channel-1")])

    def test_default_client_blocks_send_without_apply_without_network(self):
        from client import DoorayClient, DoorayError
        client = DoorayClient(token="dummy", write_policy="deny")
        for operation in [lambda: messenger.direct_send("member-1", "Hello", client=client),
                          lambda: messenger.send_channel_message("channel-1", "Hello", client=client),
                          lambda: messenger.direct_send("member-1", "Hello", apply=True, client=client)]:
            with self.assertRaises(DoorayError):
                operation()

    def test_invalid_recipients_paths_and_empty_text_never_call_client(self):
        client = RecordingClient()
        for fn, args in [(messenger.direct_send, ("member-1,member-2", "Hello")),
                         (messenger.direct_send, ("member-1", "  ")),
                         (messenger.send_channel_message, ("../other", "Hello")),
                         (messenger.send_channel_message, ("channel-1", ""))]:
            with self.subTest(fn=fn.__name__, args=args), self.assertRaises(ValueError):
                fn(*args, client=client)
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
