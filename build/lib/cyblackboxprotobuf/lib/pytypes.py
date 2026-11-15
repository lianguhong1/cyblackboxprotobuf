"""Typing aliases used by the library's public and internal APIs."""

from typing import Any, Dict, List, TypedDict, Union

Message = Dict[Union[str, int], Any]
TypeDefDict = Dict[str, "FieldDefDict"]


class FieldDefDict(TypedDict, total=False):
    name: str
    type: str
    message_type_name: str
    message_typedef: TypeDefDict
    group_typedef: TypeDefDict
    alt_typedefs: Dict[str, Union[str, TypeDefDict]]
    example_value_ignored: Any
    seen_repeated: bool
    field_order: List[str]
    packed: bool
