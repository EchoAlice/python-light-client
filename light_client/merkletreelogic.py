from eth2spec.utils.hash_function import hash

def hash_pair(left, right):
  parent_node = hash(left + right)
  return parent_node

#   ========================
#   TEST MERKLE TREE VALUES!
#   ========================

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
# Flipped binary path for now. Fix the function to go backwards later
# path = "0001"

# Hashed manually using branch
#    1. leaf_hash == one_a
# first_hash = hash_pair(leaf, branch[0])
# second_hash = hash_pair(first_hash, branch[1])
# third_hash = hash_pair(second_hash, branch[2])
# print("Final Value: " + str(third_hash))


# Created my own index to check merkle proof
def checkMerkleProof(leaf, branch, path):
  node_to_hash = leaf
  hashed_node = 0
  for i in range(len(branch)):                      
    if path[i] == '0':
      hashed_node = hash_pair(node_to_hash, branch[i])
    if path[i] == '1':
      hashed_node = hash_pair(branch[i], node_to_hash)
    if(i == len(branch) - 1):
      return hashed_node
    node_to_hash = hashed_node
