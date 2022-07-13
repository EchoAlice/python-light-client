import json
from turtle import update
import requests
import time
from containers import BeaconBlockHeader, SyncAggregate, SyncCommittee
from time import ctime

def calls_api(url):
  response = requests.get(url)
  return response

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

def updates_for_period(sync_period):
  sync_period = str(sync_period) 
  updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period="+sync_period+"&count=1" 
  response = calls_api(updates_url)
  return response

# Incorperate syncing to period inside of this function as well
# def syncs_to_current_period(bootstrap_period) -> int:
#
def finds_current_period(bootstrap_period) -> int:
  # global sync_period
  sync_period = bootstrap_period 
  while 1>0:
    response = updates_for_period(sync_period)
    updates = response.json()
    updates_status_code = response.status_code
   
    # Checks if api call executed properly 
    if updates_status_code == 500:
      sync_period = sync_period - 1 
      return sync_period
    
    print(sync_period) 
    print(updates_status_code) 
    # Increment the sync period every 12 seconds.
    time.sleep(1)
    sync_period += 1


#                           ============================
#                           COMMITTEE UPDATE'S VARIABLES 
#                           ============================

# This api call needs to be updated every time the sync period changes!  Bootstrap's api call remains the same (Only used initially).
# update_sync_period = get_sync_period()   

# I might need to run my clock function in here.  Is that bad design?

bootstrap_period = 512
current_period = finds_current_period(bootstrap_period)

print("Now at current sync period")
print(current_period)
updates = updates_for_period(current_period).json()
print(updates)

# Figure out how to pass the updates variable to all objects outside of the while loop.  Global variable?
# Place all of this code into a function so I can keep track of each sync period's data

# ================================ 
# ATTESTED BLOCK HEADER VARIABLES!
# ================================ 
attested_header = updates['data'][0]['attested_header']

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
next_sync_committee = updates['data'][0]['next_sync_committee']
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
next_sync_committee_branch = updates['data'][0]['next_sync_committee_branch']
parse_list(next_sync_committee_branch)


# ==========================
# FINALIZED BLOCK VARIABLES!
# ========================== 
finalized_header =  updates['data'][0]['finalized_header']

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
finality_branch = updates['data'][0]['finality_branch']
parse_list(finality_branch) 

# =========================                  
# SYNC AGGREGATE VARIABLES!                    
# ========================= 
sync_aggregate = updates['data'][0]['sync_aggregate']
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
fork_version =  updates['data'][0]['fork_version']
fork_version = parse_hex_to_byte(fork_version)


print(attested_block_header.slot)