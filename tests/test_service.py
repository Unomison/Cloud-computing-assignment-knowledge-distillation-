"""Unit tests for inference service, schema validation, and NACL logic.
Compatible with standard python unittest and pytest.
"""
import unittest
from service.app import validate_prediction, parse_command, REQUIRED_KEYS, VALID_INTENTS
from tools.nacl_sim import load_rules, decide


class TestServiceAndNetwork(unittest.TestCase):
    def test_1_schema_validation_valid(self):
        """Test 1: Valid 4-key JSON conforms to schema."""
        valid_data = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'
        result = validate_prediction(valid_data)
        self.assertIsNotNone(result)
        self.assertEqual(set(result.keys()), REQUIRED_KEYS)
        self.assertIn(result["intent"], VALID_INTENTS)
        self.assertEqual(result["place"], "london")

    def test_2_schema_validation_rejections(self):
        """Test 2: Extra keys, missing keys, invalid intent, or non-json must fail."""
        # Invalid intent
        bad_intent = '{"intent": "book_flight", "date": null, "time": null, "place": "paris"}'
        self.assertIsNone(validate_prediction(bad_intent))

        # Missing keys
        missing_key = '{"intent": "alarm_set", "date": "tomorrow"}'
        self.assertIsNone(validate_prediction(missing_key))

        # Extra keys
        extra_key = '{"intent": "alarm_set", "date": null, "time": "seven am", "place": null, "extra": 123}'
        self.assertIsNone(validate_prediction(extra_key))

        # Non-json text
        self.assertIsNone(validate_prediction("not json"))

    def test_3_command_parser_intent_extraction(self):
        """Test 3: Verify intent and slot extraction from commands."""
        res = parse_command("set an alarm for seven thirty am tomorrow")
        self.assertEqual(res["intent"], "alarm_set")
        self.assertEqual(res["date"], "tomorrow")
        self.assertEqual(res["time"], "seven thirty am")
        self.assertIsNone(res["place"])

        res2 = parse_command("what is the weather in london")
        self.assertEqual(res2["intent"], "weather_query")
        self.assertEqual(res2["place"], "london")

    def test_4_nacl_sample_packets(self):
        """Test 4: Verify NACL rules match expected sample packet decisions."""
        rules = load_rules("network/nacl.json")
        packets = [
            {"id": "S01", "direction": "inbound", "protocol": "tcp", "port": 443, "address": "192.0.2.55", "expected": "allow"},
            {"id": "S02", "direction": "inbound", "protocol": "tcp", "port": 22, "address": "192.0.2.55", "expected": "deny"},
            {"id": "S03", "direction": "outbound", "protocol": "tcp", "port": 8000, "address": "10.20.1.1", "expected": "allow"},
            {"id": "S04", "direction": "inbound", "protocol": "tcp", "port": 443, "address": "198.51.100.9", "expected": "deny"}
        ]
        for p in packets:
            action, _ = decide(rules, p)
            self.assertEqual(action, p["expected"])


if __name__ == "__main__":
    unittest.main()
