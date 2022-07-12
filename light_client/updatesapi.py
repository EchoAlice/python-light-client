import json
import requests
from types import SimpleNamespace
from containers import BeaconBlockHeader, SyncAggregate, SyncCommittee
from specfunctions import compute_epoch_at_slot, compute_sync_committee_period

def calls_api(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

def parse_hex_to_byte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def parse_hex_to_bit(hex_string):
  int_representation = int(hex_string, 16)
  binary_vector = bin(int_representation) 
  if binary_vector[:2] == '0b':
    binary_vector = binary_vector[2:]
  return binary_vector 

def parse_list(list):
  for i in range(len(list)):
    list[i] = parse_hex_to_byte(list[i])

class InitializedBeaconBlockHeader:
  def __init__(self, slot, proposer_index, parent_root, state_root, body_root):
    self.slot = slot
    self.proposer_index = proposer_index
    self.parent_root = parent_root
    self.state_root = state_root
    self.body_root = body_root

#                           ============================
#                           COMMITTEE UPDATE'S VARIABLES 
#                           ============================

# This api call needs to be updated every time the sync period changes!  Bootstrap's api call remains the same (Only used initially).
# update_sync_period = get_sync_period()   
committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period=512&count=1" 
committee_updates = calls_api(committee_updates_url)

# ================================ 
# ATTESTED BLOCK HEADER VARIABLES!
# ================================ 

attested_header = committee_updates['data'][0]['attested_header']
attested_block_header = BeaconBlockHeader (
  slot = int(attested_header['slot']),
  proposer_index = int(attested_header['proposer_index']),
  parent_root =  parse_hex_to_byte(attested_header['parent_root']),
  state_root =  parse_hex_to_byte(attested_header['state_root']),
  body_root =  parse_hex_to_byte(attested_header['body_root'])
)

# attested_header_slot_number = int(attested_header['slot'])
# attested_header_proposer_index = int(attested_header['proposer_index'])
# attested_header_parent_root =  attested_header['parent_root']
# attested_header_state_root =  attested_header['state_root']
# attested_header_body_root =  attested_header['body_root']



# ================================= 
# UPDATES SYNC COMMITTEE VARIABLES!
# =================================
next_sync_committee = committee_updates['data'][0]['next_sync_committee']
updates_list_of_keys = next_sync_committee['pubkeys']
updates_aggregate_pubkey = next_sync_committee['aggregate_pubkey']

# From hex to bytes
parse_list(updates_list_of_keys)
updates_aggregate_pubkey = parse_hex_to_byte(updates_aggregate_pubkey)




# ==========================
# FINALIZED BLOCK VARIABLES!
# ========================== 
finalized_header =  committee_updates['data'][0]['finalized_header']


finalized_block_header = BeaconBlockHeader (
  slot = int(finalized_header['slot']),
  proposer_index = int(finalized_header['proposer_index']),
  parent_root =  parse_hex_to_byte(finalized_header['parent_root']),
  state_root =  parse_hex_to_byte(finalized_header['state_root']),
  body_root =  parse_hex_to_byte(finalized_header['body_root'])
)


# finalized_updates_slot_number = int(finalized_header['slot'])
# finalized_updates_proposer_index = int(finalized_header['proposer_index'])
# finalized_updates_parent_root =  finalized_header['parent_root']
# finalized_updates_state_root =  finalized_header['state_root']
# finalized_updates_body_root =  finalized_header['body_root']

# From hex to bytes
# finalized_updates_parent_root = parse_hex_to_byte(finalized_updates_parent_root)
# finalized_updates_state_root = parse_hex_to_byte(finalized_updates_state_root)
# finalized_updates_body_root = parse_hex_to_byte(finalized_updates_body_root)



# ============================================== 
# Next Sync Committee Branch - from hex to bytes 
# ============================================== 
next_sync_committee_branch = committee_updates['data'][0]['next_sync_committee_branch']
parse_list(next_sync_committee_branch)


# =================================================== 
# Finalized Sync Committee Branch - from hex to bytes 
# =================================================== 
finalized_updates_branch = committee_updates['data'][0]['finality_branch']
parse_list(finalized_updates_branch) 

# =========================                  
# SYNC AGGREGATE VARIABLES!                    
# ========================= 
sync_aggregate = committee_updates['data'][0]['sync_aggregate']
sync_committee_hex = sync_aggregate['sync_committee_bits']
sync_committee_signature = sync_aggregate['sync_committee_signature']

# From hex to bytes (and bits)
sync_committee_bits = parse_hex_to_bit(sync_committee_hex) 
sync_committee_signature = parse_hex_to_byte(sync_committee_signature)

# ============                  
# FORK_VERSION                    
# ============ 
fork_version =  committee_updates['data'][0]['fork_version']
# From hex to bytes
fork_version = parse_hex_to_byte(fork_version)





next_sync_committee = SyncCommittee(
  pubkeys = updates_list_of_keys,
  aggregate_pubkey = updates_aggregate_pubkey
)


sync_aggregate = SyncAggregate(
  sync_committee_bits = sync_committee_bits, 
  sync_committee_signature = sync_committee_signature 
)