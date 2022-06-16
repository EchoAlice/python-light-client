import math
import string
from typing import List, Sequence, Union
from xml.dom.minidom import Element
from containers import Bytes32, Root
from remerkleable.basic import boolean, byte, uint, uint64
from remerkleable.bitfields import Bitlist, Bitvector
from remerkleable.complex import Container, Vector


# Data types

# Bits = List[boolean]
Bits = Bitlist
GeneralizedIndex = int                                       # <----  Convert to binary to get the path for left and right traverse
# SSZType = Union[dict, list, tuple, str, int, bool, None]     # <----  Not sure if this is correct.  Proto had this somewhere
SSZType = Union[uint, boolean, Vector, List, Container, Bitvector, Bitlist]
SSZVariableName = str                                     
BasicValue = Union[uint, boolean]
ByteList = List[byte]
Tuple = tuple
BaseBytes = Bytes32
BaseList = List

# Are elements just the basic and complex data types for SSZ?
# remerkleable.subtree.get() <---- might help the cause

# what are elements?
Elements = Union[BaseBytes, BaseList, Container]

# Constants for merkle proofs:
SYNC_COMMITTEE_SIZE = 512

# Helper functions given to me by Ethereum!  Maybe I should Import them from protozzzzlambda

def get_power_of_two_ceil(x: int) -> int:
    """
    Get the power of 2 for given input, or the closest higher power of 2 if the input is not a power of 2.
    Commonly used for "how many nodes do I need for a bottom tree layer fitting x elements?"
    Example: 0->1, 1->1, 2->2, 3->4, 4->4, 5->8, 6->8, 7->8, 8->8, 9->16.
    """
    if x <= 1:
        return 1
    elif x == 2:
        return 2
    else:
        return 2 * get_power_of_two_ceil((x + 1) // 2)

def get_power_of_two_floor(x: int) -> int:
    """
    Get the power of 2 for given input, or the closest lower power of 2 if the input is not a power of 2.
    The zero case is a placeholder and not used for math with generalized indices.
    Commonly used for "what power of two makes up the root bit of the generalized index?"
    Example: 0->1, 1->1, 2->2, 3->2, 4->4, 5->4, 6->4, 7->4, 8->8, 9->8
    """
    if x <= 1:
        return 1
    if x == 2:
        return x
    else:
        return 2 * get_power_of_two_floor(x // 2)


# # count, value
# for i, h in enumerate(current_sync_committee_branch):
#   print(i, h)

# Does it matter that I defined a sequence as a list?
def calculate_merkle_root(leaf: Bytes32, proof: Sequence[Bytes32], index: GeneralizedIndex) -> Root:
    assert len(proof) == get_generalized_index_length(index)
    for i, h in enumerate(proof):
        if get_generalized_index_bit(index, i):
            leaf = hash(h + leaf)
        else:
            leaf = hash(leaf + h)
    return leaf

def get_generalized_index_bit(index: GeneralizedIndex, position: int) -> bool:
    """
    Return the given bit of a generalized index.
    """
    return (index & (1 << position)) > 0

# changed code:     return int(log2(index))
def get_generalized_index_length(index: GeneralizedIndex) -> int:
    """
    Return the length of a path represented by a generalized index.
    """
    return int(math.log2(index))


# The generalized index gives you the list of indexes along the path!  
# Aka is a list of numbers that are the positions of the nodes
#         "Get the generalized index of the path"

# What's the difference between an SSZType and a container?
# Find ObjType from remerkleable
def get_generalized_index(typ: SSZType, path: Sequence[Union[int, SSZVariableName]]) -> GeneralizedIndex:
    """
    Converts a path (eg. `[7, "foo", 3]` for `x[7].foo[3]`, `[12, "bar", "__len__"]` for
    `len(x[12].bar)`) into the generalized index representing its position in the Merkle tree.
    """
    root = GeneralizedIndex(1)
    for p in path:
        assert not issubclass(typ, BasicValue)  # If we descend to a basic type, the path cannot continue further
        if p == '__len__':
            typ = uint64
            assert issubclass(typ, (List, ByteList))
            root = GeneralizedIndex(root * 2 + 1)
        else:
            pos, _, _ = get_item_position(typ, p)
            base_index = (GeneralizedIndex(2) if issubclass(typ, (List, ByteList)) else GeneralizedIndex(1))
            root = GeneralizedIndex(root * base_index * get_power_of_two_ceil(chunk_count(typ)) + pos)
            typ = get_elem_type(typ, p)
    return root

def get_item_position(typ: SSZType, index_or_variable_name: Union[int, SSZVariableName]) -> Tuple[int, int, int]:
    """
    Return three variables:
        (i) the index of the chunk in which the given element of the item is represented;
        (ii) the starting byte position within the chunk;
        (iii) the ending byte position within the chunk.
    For example: for a 6-item list of uint64 values, index=2 will return (0, 16, 24), index=5 will return (1, 8, 16)
    """
    if issubclass(typ, Elements):
        index = int(index_or_variable_name)
        start = index * item_length(typ.elem_type)
        return start // 32, start % 32, start % 32 + item_length(typ.elem_type)
    elif issubclass(typ, Container):
        variable_name = index_or_variable_name
        return typ.get_field_names().index(variable_name), 0, item_length(get_elem_type(typ, variable_name))
    else:
        raise Exception("Only lists/vectors/containers supported")

def item_length(typ: SSZType) -> int:
    """
    Return the number of bytes in a basic type, or 32 (a full hash) for compound types.
    """
    if issubclass(typ, BasicValue):
        return typ.byte_len
    else:
        return 32

def chunk_count(typ: SSZType) -> int:
    """
    Return the number of hashes needed to represent the top-level elements in the given type
    (eg. `x.foo` or `x[7]` but not `x[7].bar` or `x.foo.baz`). In all cases except lists/vectors
    of basic types, this is simply the number of top-level elements, as each element gets one
    hash. For lists/vectors of basic types, it is often fewer because multiple basic elements
    can be packed into one 32-byte chunk.
    """
    # typ.length describes the limit for list types, or the length for vector types.
    # Should I describe "Bits" as a list of bits?
    if issubclass(typ, BasicValue):
        return 1
    elif issubclass(typ, Bits):
        return (typ.length + 255) // 256
    elif issubclass(typ, Elements):
        return (typ.length * item_length(typ.elem_type) + 31) // 32
    elif issubclass(typ, Container):
        return len(typ.get_fields())
    else:
        raise Exception(f"Type not supported: {typ}")

def get_elem_type(typ: Union[BaseBytes, BaseList, Container],
                  index_or_variable_name: Union[int, SSZVariableName]) -> SSZType:
    """
    Return the type of the element of an object of the given type with the given index
    or member variable name (eg. `7` for `x[7]`, `"foo"` for `x.foo`)
    """
    return typ.get_fields()[index_or_variable_name] if issubclass(typ, Container) else typ.elem_type