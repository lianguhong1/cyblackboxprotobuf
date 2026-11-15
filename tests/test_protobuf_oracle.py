import unittest

import cyblackboxprotobuf as cybbp

try:
    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
except ImportError:
    descriptor_pb2 = None


@unittest.skipIf(descriptor_pb2 is None, "optional google.protobuf test dependency missing")
class OfficialProtobufOracleTests(unittest.TestCase):
    def test_wire_compatibility_with_official_runtime(self):
        file_descriptor = descriptor_pb2.FileDescriptorProto()
        file_descriptor.name = "cyblackboxprotobuf_oracle.proto"
        file_descriptor.package = "cybbp.test"
        file_descriptor.syntax = "proto3"
        message_descriptor = file_descriptor.message_type.add()
        message_descriptor.name = "OracleMessage"

        fields = [
            ("int32_value", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32, False),
            ("uint64_value", 2, descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, False),
            ("sint64_value", 3, descriptor_pb2.FieldDescriptorProto.TYPE_SINT64, False),
            ("fixed32_value", 4, descriptor_pb2.FieldDescriptorProto.TYPE_FIXED32, False),
            ("sfixed64_value", 5, descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED64, False),
            ("float_value", 6, descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT, False),
            ("bool_value", 7, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL, False),
            ("bytes_value", 8, descriptor_pb2.FieldDescriptorProto.TYPE_BYTES, False),
            ("string_value", 9, descriptor_pb2.FieldDescriptorProto.TYPE_STRING, False),
            ("packed_values", 10, descriptor_pb2.FieldDescriptorProto.TYPE_SINT32, True),
        ]
        for name, number, field_type, repeated in fields:
            field = message_descriptor.field.add()
            field.name = name
            field.number = number
            field.type = field_type
            field.label = (
                descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
                if repeated
                else descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
            )
            if repeated:
                field.options.packed = True

        pool = descriptor_pool.DescriptorPool()
        pool.AddSerializedFile(file_descriptor.SerializeToString())
        descriptor = pool.FindMessageTypeByName("cybbp.test.OracleMessage")
        if hasattr(message_factory, "GetMessageClass"):
            message_class = message_factory.GetMessageClass(descriptor)
        else:
            message_class = message_factory.MessageFactory(pool).GetPrototype(descriptor)

        official_message = message_class()
        official_message.int32_value = -1
        official_message.uint64_value = (1 << 64) - 1
        official_message.sint64_value = -123456789
        official_message.fixed32_value = 0xDEADBEEF
        official_message.sfixed64_value = -(1 << 40)
        official_message.float_value = 1.5
        official_message.bool_value = True
        official_message.bytes_value = b"\x00\x98\xff"
        official_message.string_value = "Protobuf 世界"
        official_message.packed_values.extend([1, -2, 3])
        official_wire = official_message.SerializeToString()

        typedef = {
            "1": {"type": "int32"},
            "2": {"type": "uint64"},
            "3": {"type": "sint64"},
            "4": {"type": "fixed32"},
            "5": {"type": "sfixed64"},
            "6": {"type": "float"},
            "7": {"type": "bool"},
            "8": {"type": "bytes"},
            "9": {"type": "string"},
            "10": {"type": "sint32", "packed": True},
        }
        decoded, decoded_typedef = cybbp.protobuf_to_dict(official_wire, typedef)
        self.assertEqual(decoded["1"], -1)
        self.assertEqual(decoded["2"], (1 << 64) - 1)
        self.assertEqual(decoded["3"], -123456789)
        self.assertEqual(decoded["8"], b"\x00\x98\xff")
        self.assertEqual(decoded["9"], "Protobuf 世界")
        self.assertEqual(decoded["10"], [1, -2, 3])
        self.assertEqual(cybbp.encode_message(decoded, decoded_typedef), official_wire)

        cybbp_wire = cybbp.encode_message(decoded, decoded_typedef)
        parsed_again = message_class.FromString(cybbp_wire)
        self.assertEqual(parsed_again, official_message)


if __name__ == "__main__":
    unittest.main()
