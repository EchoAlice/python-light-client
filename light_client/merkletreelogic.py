from eth2spec.utils.hash_function import hash
from math import floor, log2

def floorlog2(x) -> int:
  return floor(log2(x))

def hash_pair(left, right):
  parent_node = hash(left + right)
  return parent_node

def index_to_path(index):
  path = bin(index)
  if path[:2] == '0b':
    path = path[2:]
  return path

def is_valid_merkle_branch(leaf, branch, index, root):
  node_to_hash = leaf
  hashed_node = 0
  path = index_to_path(index)
  branch_index = 0 
  # TRAVERSE THE PATH BACKWARDS!
  for i in range(len(branch), 0, -1):                     
  # Converts vector[Bytes32] (form of branch in container) to a string of bytes (form my function can manipulate)
    branch_value = bytes(branch[branch_index])                         
    if path[i] == '0':
      hashed_node = hash_pair(node_to_hash, branch_value)
    if path[i] == '1':
      hashed_node = hash_pair(branch_value, node_to_hash)
    if(i == 1):                                
      # print("hashed node: ") 
      # print(hashed_node)
      # print("root: ") 
      # print(bytes(root)) 
      if hashed_node == root: 
        return True
      else: 
        return False
    node_to_hash = hashed_node
    branch_index += 1









# ========================
# TEST MERKLE TREE VALUES!
# ========================

# # Encodes manual merkle leaves into bytes
# m_leaf_nodes = ['0', '1', '2', '3', '4', '5', '6', '7']
# for i in range(len(m_leaf_nodes)):
#   m_leaf_nodes[i] = m_leaf_nodes[i].encode('utf-8')

# # Create my own merkle tree.  Record hashed values.  Use these as test values
# one_a = hash_pair(m_leaf_nodes[0], m_leaf_nodes[1])
# one_b = hash_pair(m_leaf_nodes[2], m_leaf_nodes[3])
# one_c = hash_pair(m_leaf_nodes[4], m_leaf_nodes[5])
# one_d = hash_pair(m_leaf_nodes[6], m_leaf_nodes[7])
# print(one_a, "\n", one_b, "\n", one_c, "\n", one_d)
# print("\n")

# two_a = hash_pair(one_a, one_b)
# two_b = hash_pair(one_c, one_d)
# print("Level two: ")
# print(two_a, "\n", two_b)
# print("\n")

# test_root = hash_pair(two_a, two_b)
# print("Manual Root: " + str(test_root))

#   ===================
#   MANUAL INDEX VALUES
#   ===================

# leaf = '0'.encode('utf-8')
# leaf_pair = '1'.encode('utf-8')
# root = b'\xad\x8d\xa1\xae_\x1c:\xef\x19}\x02\x80\xfb\xbf"\xd6\xf1\x12\xf2\x80_\xd0Xe1F\xbf\xb9:\xd9\xaf|'
# branch = [leaf_pair, b'S_\xa3\r~%\xdd\x8aI\xf1SgysN\xc8(a\x08\xd1\x15\xdaPE\xd7\x7f;A\x85\xd8\xf7\x90', b'a#\x0e\x0fR\x14\xaa\x97\x87\xbfXZJ\x91\x1dQ\x93+\x15\xe8d\x85\xdb\xe7HZ\xfdt\xdf\xf5\x12\x02']  
# index = 8

# Hashed manually using branch
#    1. leaf_hash == one_a
# first_hash = hash_pair(leaf, branch[0])
# second_hash = hash_pair(first_hash, branch[1])
# third_hash = hash_pair(second_hash, branch[2])
# print("Final Value: " + str(third_hash))

# ETHEREUM'S PROOF FUNCTION
#
# Try to make my own work for the spec.  If I can't make it happen, then use Ethereum's
# 
#
# def is_valid_merkle_branch(leaf: Bytes32, branch: Sequence[Bytes32], depth: uint64, index: uint64, root: Root) -> bool:
#     """
#     Check if ``leaf`` at ``index`` verifies against the Merkle ``root`` and ``branch``.
#     """
#     value = leaf
#     for i in range(depth):
#         if index // (2**i) % 2:
#             value = hash(branch[i] + value)
#         else:
#             value = hash(value + branch[i])
#     return value == root


# assert is_valid_merkle_branch(
#     leaf=hash_tree_root(update.finalized_header),
#     branch=update.finality_branch,
#     depth=floorlog2(FINALIZED_ROOT_INDEX),
#     index=get_subtree_index(FINALIZED_ROOT_INDEX),
#     root=update.attested_header.state_root,
# )


# assert is_valid_merkle_branch(leaf, branch, index, root)
# print("Wahoo")