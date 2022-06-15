from eth2spec.utils.hash_function import hash

def hash_pair(left, right):
  parent_node = hash(left + right)
  return parent_node

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ===============================
#       MERKLE ROOT TESTING
# ===============================
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Figure out how this indexing thing works for merkle proofs!
# See if the merkle root I get from hashing this manually is the same as below

#   ========================
#   TEST MERKLE TREE VALUES!
#   ========================

# Encodes manual merkle leaves into bytes
m_leaf_nodes = ['0', '1', '2', '3', '4', '5', '6', '7']
for i in range(len(m_leaf_nodes)):
  m_leaf_nodes[i] = m_leaf_nodes[i].encode('utf-8')

# Create my own merkle tree.  Record hashed values.  Use these as test values
one_a = hash_pair(m_leaf_nodes[0], m_leaf_nodes[1])
one_b = hash_pair(m_leaf_nodes[2], m_leaf_nodes[3])
one_c = hash_pair(m_leaf_nodes[4], m_leaf_nodes[5])
one_d = hash_pair(m_leaf_nodes[6], m_leaf_nodes[7])
# print(one_a, "\n", one_b, "\n", one_c, "\n", one_d)
# print("\n")

two_a = hash_pair(one_a, one_b)
two_b = hash_pair(one_c, one_d)
# print("Level two: ")
# print(two_a, "\n", two_b)
# print("\n")

test_root = hash_pair(two_a, two_b)
# print("Level 3: ")
print("\n")
print("Root: " + str(test_root))








leaf_nodes = ['0', '1', '2', '3', '4', '5', '6', '7']
for i in range(len(leaf_nodes)):
  leaf_nodes[i] = leaf_nodes[i].encode('utf-8')

# Record the whole tree instead of errasing each level below 
def naive_merkle_tree(nodes):
  parent_nodes = [] 
  if len(nodes) == 1:
    print("\n") 
    return 
  for i in range(len(nodes)):
    if i % 2 == 0: 
      parent_node = hash_pair(nodes[i], nodes[i + 1])
      parent_nodes.append(parent_node)
  nodes = parent_nodes 
  naive_merkle_tree(nodes) 
  return

# naive_merkle_tree(leaf_nodes)











i_leaf_nodes = ['0', '1', '2', '3', '4', '5', '6', '7']
for i in range(len(i_leaf_nodes)):
  i_leaf_nodes[i] = i_leaf_nodes[i].encode('utf-8')

# # count, value
# for i, h in enumerate(current_sync_committee_branch):
#   print(i, h)

# Created my own index to check merkle proof
def checkMerkleProof(leaf, root, branch, index):
  node_to_hash = leaf
  for i in range(len(index)):                      
    # Not sure which way you organize the left and right nodes for 0 and 1 bits 
    if index[i] == 0:
      hashed_node = hash_pair(node_to_hash, branch[i])
    if index[i] == 1:
      hashed_node = hash_pair(branch[i], node_to_hash)
    node_to_hash = hashed_node
  
  print("Merkle Proof root: " + str(node_to_hash))
  print("Trusted root: " + str(root)) 



# Use index, witness, and leaf to get to the root!
# Find:    root of i_leaf_nodes[5]          ( == b'4)

witness = [i_leaf_nodes[5], one_d, two_a]
index = [0, 0, 1]
leaf = i_leaf_nodes[4]
# Manually instantiate witness
# print(witness)


checkMerkleProof(leaf, test_root, witness, index)



# Debugging index

# first_hash = hash_pair(i_leaf_nodes[4], witness[0])
# print("\n")
# print("First hash: " + str(first_hash))
# print("left: " + str(i_leaf_nodes[4]))
# print("right: " + str(witness[0]))
# print("\n")

# print("One C: " + str(one_c))
# print("left: " + str(m_leaf_nodes[4]))
# print("right: " + str(m_leaf_nodes[5]))
# print("\n")








#     !!!!!!!!!!!! 
#     EXTRA CREDIT
#     !!!!!!!!!!!!



#  Functions were implemented for me automatically.  Make 'em from scratch!
#
#                     |
#                     |
#                     V
#
# Steps to merkleize:
# (Current_sync_committee_branch contains 5 nodes)  
#     1. serialize individual nodes
#     2. hash the serialized nodes

# def merkleizeSyncCommittee(sync_committee):
#   hash_tree_root = hash(sync_committee)
#   return hash_tree_root





# # Make the merkle proof validating function from scratch! Fuck the noise.

# def validateMerkleProof(sync_committee, merkle_branch, checkpoint_root):
#   sync_committee_root = merkleizeSyncCommittee(sync_committee)
#   if checkMerkleProof(sync_committee_root, merkle_branch, checkpoint_root) == True:
#     return "This thaaaaang's legit!"
