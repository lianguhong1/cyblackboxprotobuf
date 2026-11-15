# cyblackboxprotobuf

`cyblackboxprotobuf` decodes and encodes Protocol Buffers messages when the
original `.proto` schema is unavailable. Its top-level API follows
`blackboxprotobuf` and accepts the same message typedef format, with support
for official Protobuf scalar type names as well as legacy BBPB type aliases.

```python
import cyblackboxprotobuf

form_data, form_type = cyblackboxprotobuf.protobuf_to_dict(data)
encoded = cyblackboxprotobuf.encode_message(form_data, form_type)
assert encoded == data
```

`protobuf_to_dict` preserves Python values, including `bytes`. The JSON
convenience API represents byte fields as base64 strings and uses the returned
typedef to distinguish bytes from text:

```python
json_text, form_type = cyblackboxprotobuf.protobuf_to_json(data)
encoded = cyblackboxprotobuf.protobuf_from_json(json_text, form_type)
```

Without a schema, the wire format cannot distinguish types such as `int32`,
`uint32`, and `sint32`, or a nested message from arbitrary bytes. In those
cases the decoder uses documented best-effort defaults; pass a typedef to
`decode_message` or `protobuf_to_dict` to specify the intended types.

The core is pure Python and supports Python 3.8 and newer. The package is
distributed under the MIT license; portions of its implementation are adapted
from NCC Group's `blackboxprotobuf` project.
