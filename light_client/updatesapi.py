import json
import requests
from containers import BeaconBlockHeader, SyncAggregate, SyncCommittee

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

# Does the lodestar api serve the attested header proof?

# ============================== 
# NEXT SYNC COMMITTEE VARIABLES!
# ==============================
next_sync_committee = committee_updates['data'][0]['next_sync_committee']
next_list_of_keys = next_sync_committee['pubkeys']
next_aggregate_pubkey = next_sync_committee['aggregate_pubkey']
parse_list(next_list_of_keys)
next_aggregate_pubkey = parse_hex_to_byte(next_aggregate_pubkey)

next_sync_committee = SyncCommittee(
  pubkeys = next_list_of_keys,
  aggregate_pubkey = next_aggregate_pubkey
)

# -------------------------- 
# Next Sync Committee Branch
# --------------------------
next_sync_committee_branch = committee_updates['data'][0]['next_sync_committee_branch']
parse_list(next_sync_committee_branch)


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
# ---------------
# Finality Branch 
# --------------- 
finality_branch = committee_updates['data'][0]['finality_branch']
parse_list(finality_branch) 

# =========================                  
# SYNC AGGREGATE VARIABLES!                    
# ========================= 
sync_aggregate = committee_updates['data'][0]['sync_aggregate']
sync_committee_hex = sync_aggregate['sync_committee_bits']
sync_committee_signature = sync_aggregate['sync_committee_signature']
sync_committee_bits = parse_hex_to_bit(sync_committee_hex) 
sync_committee_signature = parse_hex_to_byte(sync_committee_signature)

sync_aggregate = SyncAggregate(
  sync_committee_bits = sync_committee_bits, 
  sync_committee_signature = sync_committee_signature 
)

# ============                  
# FORK_VERSION                    
# ============ 
fork_version =  committee_updates['data'][0]['fork_version']
fork_version = parse_hex_to_byte(fork_version)