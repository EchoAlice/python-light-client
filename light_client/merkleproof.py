from typing import Sequence
from containers import Bytes32, GeneralizedIndex, Root

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

# Does it matter that I defined a sequence as a list?
# def calculate_merkle_root(leaf: Bytes32, proof: Sequence[Bytes32], index: GeneralizedIndex) -> Root:
#     assert len(proof) == get_generalized_index_length(index)
#     for i, h in enumerate(proof):
#         if get_generalized_index_bit(index, i):
#             leaf = hash(h + leaf)
#         else:
#             leaf = hash(leaf + h)
#     return leaf
