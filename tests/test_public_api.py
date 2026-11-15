import json
import os
import tempfile
import unittest
import warnings

import cyblackboxprotobuf as cybbp


class PublicApiTests(unittest.TestCase):
    def setUp(self):
        self.typedef = {
            "1": {"type": "int32"},
            "2": {"type": "uint64"},
            "3": {"type": "sint32"},
            "4": {"type": "uint32"},
            "5": {"type": "fixed32"},
            "6": {"type": "sfixed32"},
            "7": {"type": "fixed64"},
            "8": {"type": "sfixed64"},
            "9": {"type": "float"},
            "10": {"type": "double"},
            "11": {"type": "bool"},
            "12": {"type": "enum"},
            "13": {"type": "bytes"},
            "14": {"type": "string"},
            "15": {
                "type": "message",
                "message_typedef": {"1": {"type": "string"}},
            },
            "16": {"type": "int32", "packed": True},
        }
        self.message = {
            "1": -123,
            "2": (1 << 64) - 1,
            "3": -456789,
            "4": (1 << 32) - 1,
            "5": 0xDEADBEEF,
            "6": -(1 << 31),
            "7": (1 << 64) - 2,
            "8": -5,
            "9": 1.5,
            "10": 1.25,
            "11": True,
            "12": -1,
            "13": b"\x98\x01\x18\x00\xff",
            "14": "hello 世界",
            "15": {"1": "nested"},
            "16": [1, -2, 3],
        }

    def test_official_scalar_types_roundtrip_through_native_dict(self):
        encoded = cybbp.encode_message(self.message, self.typedef)
        form_data, form_type = cybbp.protobuf_to_dict(encoded, self.typedef)

        self.assertEqual(form_data, self.message)
        self.assertIsInstance(form_data["13"], bytes)
        self.assertIsInstance(form_data["14"], str)
        self.assertEqual(form_type["1"]["type"], "int32")
        self.assertEqual(form_type["16"]["type"], "int32")
        self.assertTrue(form_type["16"]["packed"])
        self.assertIs(type(form_data), dict)
        self.assertIs(type(form_data["15"]), dict)
        self.assertIs(type(form_type), dict)
        self.assertIs(type(form_type["15"]["message_typedef"]), dict)
        self.assertNotIn("example_value_ignored", repr(form_type))
        self.assertEqual(cybbp.encode_message(form_data, form_type), encoded)

    def test_json_bytes_use_base64_and_remain_distinct_from_text(self):
        encoded = cybbp.encode_message(self.message, self.typedef)
        json_text, form_type = cybbp.protobuf_to_json(encoded, self.typedef)
        json_data = json.loads(json_text)

        self.assertEqual(json_data["13"], "mAEYAP8=")
        self.assertEqual(json_data["14"], "hello 世界")
        self.assertEqual(form_type["13"]["type"], "bytes")
        self.assertNotIn("example_value_ignored", repr(form_type))
        self.assertEqual(cybbp.protobuf_from_json(json_text, form_type), encoded)

    def test_legacy_example_annotation_is_ignored(self):
        legacy_typedef = {
            "1": {"type": "int32", "example_value_ignored": 7}
        }
        cybbp.validate_typedef(legacy_typedef)
        self.assertEqual(
            cybbp.sort_typedef(legacy_typedef), {"1": {"type": "int32"}}
        )
        decoded, form_type = cybbp.protobuf_to_dict(b"\x08\x07", legacy_typedef)

        self.assertEqual(decoded, {"1": 7})
        self.assertEqual(form_type["1"]["type"], "int32")
        self.assertNotIn("example_value_ignored", repr(form_type))
        self.assertEqual(cybbp.encode_message(decoded, form_type), b"\x08\x07")

    def test_plain_dict_preserves_nested_wire_field_order(self):
        wire_data = bytes([10, 4, 16, 2, 8, 1])
        typedef = {
            "1": {
                "type": "message",
                "message_typedef": {
                    "1": {"type": "int32"},
                    "2": {"type": "int32"},
                },
            }
        }

        form_data, form_type = cybbp.protobuf_to_dict(wire_data, typedef)

        self.assertIs(type(form_data), dict)
        self.assertIs(type(form_data["1"]), dict)
        self.assertEqual(form_type["1"]["field_order"], ["2", "1"])
        self.assertEqual(cybbp.encode_message(form_data, form_type), wire_data)

    def test_list_input_returns_a_list_of_native_dictionaries(self):
        encoded = cybbp.encode_message(self.message, self.typedef)
        form_data, form_type = cybbp.protobuf_to_dict(
            [encoded, encoded], self.typedef
        )
        self.assertEqual(form_data, [self.message, self.message])
        self.assertEqual(
            [cybbp.encode_message(item, form_type) for item in form_data],
            [encoded, encoded],
        )

    def test_missing_or_invalid_type_warns_and_infers_from_values(self):
        with self.assertWarns(UserWarning):
            encoded = cybbp.encode_message(
                {"1": 7, "2": True, "3": b"\x00"}, None
            )
        self.assertEqual(encoded, b"\x08\x07\x10\x01\x1a\x01\x00")

        with self.assertWarns(UserWarning):
            encoded = cybbp.encode_message(
                {"1": "value"}, {"1": {"type": "not-a-protobuf-type"}}
            )
        self.assertEqual(encoded, b"\x0a\x05value")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with self.assertRaises(cybbp.EncoderException):
                cybbp.encode_message({"1": None}, None)
        self.assertEqual(len(caught), 1)

    def test_deprecated_group_fields_roundtrip(self):
        typedef = {
            "1": {"type": "group", "group_typedef": {"2": {"type": "int32"}}}
        }
        message = {"1": {"2": 7}}
        encoded = cybbp.encode_message(message, typedef)
        self.assertEqual(encoded, b"\x0b\x10\x07\x0c")
        decoded, form_type = cybbp.protobuf_to_dict(encoded, typedef)
        self.assertEqual(decoded, message)
        self.assertEqual(cybbp.encode_message(decoded, form_type), encoded)

    def test_type_range_validation(self):
        with self.assertRaises(cybbp.EncoderException):
            cybbp.encode_message({"1": 1 << 32}, {"1": {"type": "uint32"}})

    def test_legacy_type_aliases_remain_supported(self):
        typedef = {
            "1": {"type": "int"},
            "2": {"type": "uint"},
            "3": {"type": "sint"},
            "4": {"type": "packed_uint"},
        }
        message = {"1": -1, "2": 300, "3": -20, "4": [1, 2, 300]}
        encoded = cybbp.encode_message(message, typedef)
        decoded, _ = cybbp.decode_message(encoded, typedef)
        self.assertEqual(decoded, message)

    def test_inferred_typedef_roundtrip_needs_no_normalization(self):
        encoded = b"\x08\x96\x01"
        form_data, form_type = cybbp.protobuf_to_dict(encoded)
        self.assertEqual(form_data, {"1": 150})
        self.assertEqual(form_type["1"]["type"], "int64")
        with warnings.catch_warnings(record=True) as caught:
            self.assertEqual(cybbp.encode_message(form_data, form_type), encoded)
        self.assertEqual(caught, [])

    def test_protofile_uses_official_names_and_packed_metadata(self):
        source = 'syntax = "proto3";\nmessage Example {\n  repeated sint32 values = 1 [packed=true];\n  bool enabled = 2;\n}\n'
        with tempfile.TemporaryDirectory() as directory:
            proto_path = os.path.join(directory, "example.proto")
            output_path = os.path.join(directory, "output.proto")
            with open(proto_path, "w", encoding="utf-8") as proto_file:
                proto_file.write(source)

            imported = cybbp.import_protofile(proto_path, save_to_known=False)
            self.assertEqual(imported["Example"]["1"]["type"], "sint32")
            self.assertTrue(imported["Example"]["1"]["packed"])
            self.assertEqual(imported["Example"]["2"]["type"], "bool")

            cybbp.export_protofile(imported, output_path)
            with open(output_path, "r", encoding="utf-8") as proto_file:
                exported = proto_file.read()
            self.assertIn("repeated sint32 values = 1 [packed=true]", exported)


if __name__ == "__main__":
    unittest.main()
