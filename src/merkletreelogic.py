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
      if hashed_node == root: 
        return True
      else: 
        return False
    node_to_hash = hashed_node
    branch_index += 1
