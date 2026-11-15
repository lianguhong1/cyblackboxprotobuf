"""Mappings between Protobuf field names, wire types, and codecs."""

from cyblackboxprotobuf.lib.types import fixed, length_delim, varint, wiretypes
from cyblackboxprotobuf.lib.exceptions import EncoderException

import six


def _require_integer(value, field_type, minimum, maximum):
    if not isinstance(value, six.integer_types) or isinstance(value, bool):
        raise EncoderException("%s requires an integer, got %r" % (field_type, value))
    if value < minimum or value > maximum:
        raise EncoderException(
            "%s value %d is outside the range [%d, %d]"
            % (field_type, value, minimum, maximum)
        )
    return value


def _encode_int32(value):
    return varint.encode_varint(
        _require_integer(value, "int32", -(1 << 31), (1 << 31) - 1)
    )


def _encode_int64(value):
    return varint.encode_varint(
        _require_integer(value, "int64", -(1 << 63), (1 << 63) - 1)
    )


def _encode_uint32(value):
    return varint.encode_uvarint(_require_integer(value, "uint32", 0, (1 << 32) - 1))


def _encode_uint64(value):
    return varint.encode_uvarint(_require_integer(value, "uint64", 0, (1 << 64) - 1))


def _encode_sint32(value):
    return varint.encode_svarint(
        _require_integer(value, "sint32", -(1 << 31), (1 << 31) - 1)
    )


def _decode_int32(buf, pos):
    value, pos = varint.decode_uvarint(buf, pos)
    value &= 0xFFFFFFFF
    if value & 0x80000000:
        value -= 1 << 32
    return value, pos


def _decode_uint32(buf, pos):
    value, pos = varint.decode_uvarint(buf, pos)
    return value & 0xFFFFFFFF, pos


def _decode_sint32(buf, pos):
    value, pos = varint.decode_uvarint(buf, pos)
    value &= 0xFFFFFFFF
    if value & 1:
        return -((value >> 1) + 1), pos
    return value >> 1, pos


def _encode_bool(value):
    if isinstance(value, bool):
        return varint.encode_uvarint(1 if value else 0)
    if isinstance(value, six.integer_types) and value in (0, 1):
        return varint.encode_uvarint(value)
    raise EncoderException("bool requires True, False, 0, or 1; got %r" % (value,))


def _decode_bool(buf, pos):
    value, pos = varint.decode_uvarint(buf, pos)
    return bool(value), pos


ENCODERS = {
    # Legacy BBPB names.
    "uint": varint.encode_uvarint,
    "int": varint.encode_varint,
    "sint": varint.encode_svarint,
    # Official Protobuf names.
    "int32": _encode_int32,
    "int64": _encode_int64,
    "uint32": _encode_uint32,
    "uint64": _encode_uint64,
    "sint32": _encode_sint32,
    "sint64": varint.encode_svarint,
    "bool": _encode_bool,
    "enum": _encode_int32,
    "fixed32": fixed.encode_fixed32,
    "sfixed32": fixed.encode_sfixed32,
    "float": fixed.encode_float,
    "fixed64": fixed.encode_fixed64,
    "sfixed64": fixed.encode_sfixed64,
    "double": fixed.encode_double,
    "bytes": length_delim.encode_bytes,
    "bytes_hex": length_delim.encode_bytes_hex,
    "string": length_delim.encode_string,
}

DECODERS = {
    # Legacy BBPB names.
    "uint": varint.decode_uvarint,
    "int": varint.decode_varint,
    "sint": varint.decode_svarint,
    # Official Protobuf names.
    "int32": _decode_int32,
    "int64": varint.decode_varint,
    "uint32": _decode_uint32,
    "uint64": varint.decode_uvarint,
    "sint32": _decode_sint32,
    "sint64": varint.decode_svarint,
    "bool": _decode_bool,
    "enum": _decode_int32,
    "fixed32": fixed.decode_fixed32,
    "sfixed32": fixed.decode_sfixed32,
    "float": fixed.decode_float,
    "fixed64": fixed.decode_fixed64,
    "sfixed64": fixed.decode_sfixed64,
    "double": fixed.decode_double,
    "bytes": length_delim.decode_bytes,
    "bytes_hex": length_delim.decode_bytes_hex,
    "string": length_delim.decode_string,
}

WIRETYPES = {
    "uint": wiretypes.VARINT,
    "int": wiretypes.VARINT,
    "sint": wiretypes.VARINT,
    "int32": wiretypes.VARINT,
    "int64": wiretypes.VARINT,
    "uint32": wiretypes.VARINT,
    "uint64": wiretypes.VARINT,
    "sint32": wiretypes.VARINT,
    "sint64": wiretypes.VARINT,
    "bool": wiretypes.VARINT,
    "enum": wiretypes.VARINT,
    "fixed32": wiretypes.FIXED32,
    "sfixed32": wiretypes.FIXED32,
    "float": wiretypes.FIXED32,
    "fixed64": wiretypes.FIXED64,
    "sfixed64": wiretypes.FIXED64,
    "double": wiretypes.FIXED64,
    "bytes": wiretypes.LENGTH_DELIMITED,
    "bytes_hex": wiretypes.LENGTH_DELIMITED,
    "string": wiretypes.LENGTH_DELIMITED,
    "message": wiretypes.LENGTH_DELIMITED,
    "group": wiretypes.START_GROUP,
}

_PACKABLE_ENCODERS = {
    "int32": _encode_int32,
    "int64": _encode_int64,
    "uint32": _encode_uint32,
    "uint64": _encode_uint64,
    "sint32": _encode_sint32,
    "sint64": varint.encode_svarint,
    "bool": _encode_bool,
    "enum": _encode_int32,
    "fixed32": fixed.encode_fixed32,
    "sfixed32": fixed.encode_sfixed32,
    "float": fixed.encode_float,
    "fixed64": fixed.encode_fixed64,
    "sfixed64": fixed.encode_sfixed64,
    "double": fixed.encode_double,
    # Compatibility for BBPB typedefs using generic packed types.
    "uint": varint.encode_uvarint,
    "int": varint.encode_varint,
    "sint": varint.encode_svarint,
}

_PACKABLE_DECODERS = {
    "int32": _decode_int32,
    "int64": varint.decode_varint,
    "uint32": _decode_uint32,
    "uint64": varint.decode_uvarint,
    "sint32": _decode_sint32,
    "sint64": varint.decode_svarint,
    "bool": _decode_bool,
    "enum": _decode_int32,
    "fixed32": fixed.decode_fixed32,
    "sfixed32": fixed.decode_sfixed32,
    "float": fixed.decode_float,
    "fixed64": fixed.decode_fixed64,
    "sfixed64": fixed.decode_sfixed64,
    "double": fixed.decode_double,
    "uint": varint.decode_uvarint,
    "int": varint.decode_varint,
    "sint": varint.decode_svarint,
}

PACKED_ENCODERS = {
    name: length_delim.generate_packed_encoder(encoder)
    for name, encoder in _PACKABLE_ENCODERS.items()
}
PACKED_DECODERS = {
    name: length_delim.generate_packed_decoder(decoder)
    for name, decoder in _PACKABLE_DECODERS.items()
}

for _name, _encoder in PACKED_ENCODERS.items():
    ENCODERS["packed_" + _name] = _encoder
    WIRETYPES["packed_" + _name] = wiretypes.LENGTH_DELIMITED
for _name, _decoder in PACKED_DECODERS.items():
    DECODERS["packed_" + _name] = _decoder

# Defaults are necessarily guesses when no message descriptor is supplied.
WIRE_TYPE_DEFAULTS = {
    wiretypes.VARINT: "int64",
    wiretypes.FIXED32: "fixed32",
    wiretypes.FIXED64: "fixed64",
    wiretypes.LENGTH_DELIMITED: None,
    wiretypes.START_GROUP: "group",
    wiretypes.END_GROUP: None,
}
