import json
import requests
import time
import pytest
from containers import LightClientUpdate, SyncCommittee, Bytes32, NEXT_SYNC_COMMITTEE_INDEX
from specfunctions import floorlog2, compute_sync_committee_period_at_slot
from time import ctime
from mvplightclient import get_current_slot
from types import SimpleNamespace
from eth2spec.utils.hash_function import hash
from updatesapi import initializes_block_header, instantiates_sync_period_data, initializes_sync_committee, initializes_sync_aggregate
from remerkleable.core import View
from merkletreelogic import is_valid_merkle_branch
from py_ecc.bls import G2ProofOfPossession
from py_ecc.optimized_bls12_381 import (
    G1,
    Z1,
    Z2,
    multiply,
)
from py_ecc.bls.g2_primitives import (
    G1_to_pubkey,
    G2_to_signature,
)

from containers import uint64, MIN_GENESIS_TIME, BeaconBlockHeader, Root, SECONDS_PER_SLOT, SLOTS_PER_EPOCH, LightClientOptimisticUpdate


def calls_api(url):
  response = requests.get(url)
  return response

def get_sync_period(slot_number):
  sync_period = slot_number // 8192
  return sync_period

def hash_pair(left, right):
  parent_node = hash(left + right)
  return parent_node

def index_to_path(index):
  path = bin(index)
  if path[:2] == '0b':
    path = path[2:]
  return path

def get_subtree_index(generalized_index: int) -> int:
  return int(generalized_index % 2**5) 

def get_current_epoch(current_time, genesis_time):
  current_epoch = (current_time - genesis_time) // (SECONDS_PER_SLOT * SLOTS_PER_EPOCH)
  return current_epoch

def parse_hex_to_byte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def parse_list(list):
  for i in range(len(list)):
    list[i] = parse_hex_to_byte(list[i])

def updates_for_period(sync_period):
  sync_period = str(sync_period) 
  updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period="+sync_period+"&count=1" 
  response = calls_api(updates_url)

  return response



# =============================================
# Functions testing for next_sync_committee bug
# =============================================

#                                                         \\\\\\\\////////
#                                                          ==============
#                                                             TEST ZONE  
#                                                          ==============
#                                                         ////////\\\\\\\\

test_update = instantiates_sync_period_data(513)

print(test_update.attested_header)
print(test_update.finalized_header)

assert is_valid_merkle_branch(
  leaf=View.hash_tree_root(test_update.next_sync_committee),              #  Next sync committee corresponding to 'attested header' 
  branch=test_update.next_sync_committee_branch,                   
  # depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX),
  index=NEXT_SYNC_COMMITTEE_INDEX,
  root=test_update.attested_header.state_root,                           # spec said "attested_header.state_root"          Must be a bug in the branch, right?            
)
print("pass")


  #  Data problem???
  #  
  #  leaf= hash(udpate.next_sync_committee) 
  #  branch=update.next_sync_committee_branch 
  #  index= next_sync_committee_index 
  #  root = update.finalized_header.state_root







# This is saying that the update's next sync_committee is not the committee
# within the attested header's state_root 
#
# What I know:
#    - The attested header is 75 slots ahead of finalized header. 
#    - They're within the same sync period
#    - The data is organized properly
#    - 
#    -
#    -
#    -
#    -
#    -
#    -
#    -








#  calling an update for a period gives you...

# sync_period = 512
# sync_period_update = updates_for_period(sync_period).json()

# attested_block_header = initializes_block_header(sync_period_update['data'][0]['attested_header']) 
# next_sync_committee = initializes_sync_committee(sync_period_update['data'][0]['next_sync_committee'])
# finalized_block_header = initializes_block_header(sync_period_update['data'][0]['finalized_header']) 

# print("attested header: ")
# print("   slot: " + str(attested_block_header.slot))
# print("   period: " + str(compute_sync_committee_period_at_slot(attested_block_header.slot)))

# print("finalized header: ")
# print("   slot: " + str(finalized_block_header.slot))
# print("   period: " + str(compute_sync_committee_period_at_slot(finalized_block_header.slot)))











# class LightClientOptimisticUpdate(Container):
#     # The beacon block header that is attested to by the sync committee
#     attested_header: BeaconBlockHeader
#     # Sync committee aggregate signature
#     sync_aggregate: SyncAggregate
#     # Slot at which the aggregate signature was created (untrusted)
#     signature_slot: Slot


# current_finality_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/finality_update/" 
# current_finality_update_message = calls_api(current_finality_update_url).json()
# print(current_finality_update_message)

# current_header_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/optimistic_update/" 
# current_header_update_message = calls_api(current_header_update_url).json()

# print(current_header_update_message['data']['attested_header'])
# print(current_header_update_message['data']['sync_aggregate'])

# light_client_update = instantiates_finality_update_data(current_update)
# print(light_client_update)












"""
  ------------------------------------------------------------------------------------------
  CODE THAT TRACKS MY VIEW OF CURRENT HEADER SLOT AND LODESTAR'S VIEW OF CURRENT HEADER SLOT
  ------------------------------------------------------------------------------------------
"""

# #  Lodestar's attested header isn't reliable.  Maybe just follow the finalized header
# while 1>0:
#     current_time = uint64(int(time.time()))
#     current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    
#     # Make api call.  See if the call updates every cycle    
#     current_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/finality_update/" 
#     current_update = calls_api(current_update_url).json()

#     current_attested_header_message = current_update['data']['attested_header']
#     current_attested_header = initializes_block_header(current_attested_header_message)
    
#     print("\n")
#     print("Lodestar's current attested header slot: " + str(current_attested_header.slot))
#     print("My current attested header slot (based on local clock): " + str(current_slot)) 

#     time.sleep(12)














# @pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 42)])
# def test_eval(test_input, expected):
#     assert eval(test_input) == expected


# #  Checking to see if G2ProofOfPossession.FastAggregateVerify works!!!
# sample_message = b'\x12' * 32

# Z1_PUBKEY = G1_to_pubkey(Z1)
# Z2_SIGNATURE = G2_to_signature(Z2)



# def compute_aggregate_signature(SKs, message):
#     PKs = [G2ProofOfPossession.SkToPk(sk) for sk in SKs]
#     signatures = [G2ProofOfPossession.Sign(sk, message) for sk in SKs]
#     aggregate_signature = G2ProofOfPossession.Aggregate(signatures)
#     return (PKs, aggregate_signature)

# @pytest.mark.parametrize(
#     'PKs, aggregate_signature, message, result',
#     [
#         (*compute_aggregate_signature(SKs=[1], message=sample_message), sample_message, True),
#         (*compute_aggregate_signature(SKs=tuple(range(1, 5)), message=sample_message), sample_message, True),
#         ([], Z2_SIGNATURE, sample_message, False),
#         ([G2ProofOfPossession.SkToPk(1), Z1_PUBKEY], G2ProofOfPossession.Sign(1, sample_message), sample_message, False),
#     ]
# )

# def test_fast_aggregate_verify(PKs, aggregate_signature, message, result):
#     assert G2ProofOfPossession.FastAggregateVerify(PKs, message, aggregate_signature) == result


# python -m pytest .\light_client\scratch.py

# ^  This is the command to run in the terminal for testing.
#
#    It looks like FastAggregateVerify() works. Something must 
#    be wrong with my data in the spec  













#  TEST VALUES and function!


# def is_valid_merkle_branch(leaf, branch, index, root):
#   node_to_hash = leaf
#   hashed_node = 0
#   path = index_to_path(index)
#   branch_index = 0 
#   # TRAVERSE THE PATH BACKWARDS!
#   for i in range(len(branch), 0, -1):                      
#     if path[i] == '0':
#       hashed_node = hash_pair(node_to_hash, branch[branch_index])
#     if path[i] == '1':
#       hashed_node = hash_pair(branch[branch_index], node_to_hash)
#     if(i == 1):                                
#       # print("Hashed node: " + str(hashed_node))
#       # print("State root: " + str(root))
#       if hashed_node == root: 
#         return True
#       else: 
#         return False
#     node_to_hash = hashed_node
#     branch_index += 1

# next_sync_committee_leaf = b'\xa4\xa4#\xacj\x8e\x87 \xaa\x90\xb0&\\\xda\x0f\x82\x12\x96\xb7\\\xa6\xde+\\\x8c*\x1bo\x93\x9c5='
# branch = [b'\xfb6T.K.\xaf\xdc\x8a1n\xe5\xd7\xe2\x1f\xd7\x979iwO\xa1\x01\xf7Mp\xdf\x06C\xa5\xe2\x80', b']\x87\xbe\xea\xf4u\xd6&\x01\xef\x81G\xee\xa3\xad9}\x02pR\xd7t\xc7B\x83\x9b\x14h\x16\x8f(\xbc', b"\xe8\x1f\xf91\x01\x8d\xd2\xf2\x1c[=i2\x1b\x0fD\xf6\xca@\xf83\x81\x1dc\x028\xba '\x18\x9a\xb1", b'\xc7\x80\t\xfd\xf0\x7f\xc5j\x11\xf1"7\x06X\xa3S\xaa\xa5B\xedc\xe4LK\xc1_\xf4\xcd\x10Z\xb3<', b'\x1d\x85Q\x8aNdf\x0f\xd2&\x14D\xe3\x9c\x877pm\\\xab\xdcPU\x1b<\x14\x0bIS\xb0\xe1\xed']
# next_committee_index = 55
# header_state_root = b'\xcb\xaf\xb5\xd0\x8d:Yb\xed\x1d\xe3~\xf4l\x8f\xfd\xec\x04D\xd3$\x9b\xe5%}\x8b?z\xcc\n\xe0k' 

# first_hash = hash_pair(branch[0], next_sync_committee_leaf)
# second_hash = hash_pair(branch[1], first_hash)
# third_hash = hash_pair(branch[2], second_hash)
# fourth_hash = hash_pair(third_hash, branch[3])
# fifth_hash = hash_pair(branch[4], fourth_hash)
# # print(fifth_hash)
# # print(header_state_root)