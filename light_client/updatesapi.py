import json
from turtle import update
import requests
import time
from containers import BeaconBlockHeader, LightClientStore, LightClientUpdate,SyncAggregate, SyncCommittee
from time import ctime
from specfunctions import process_light_client_update
from bootstrapapi import (bootstrap_block_header,
                          bootstrap_header, 
                          bootstrap_next_sync_committee, 
                          bootstrap_sync_committee, 
                          current_sync_committee_branch)

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



#                                                \~~~~~~~~~~~~~~~~~~/
#                                                 \ ============== /
#                                                    THE BIG BOYS
#                                                 / ============== \
#                                                /~~~~~~~~~~~~~~~~~~\

def instantiates_sync_period_data(sync_period):
  updates = updates_for_period(sync_period).json()

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
  
  print("Attested block header: " + str(attested_block_header.slot))
  print("\n")
  
  
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

  # I need to put all of this information into the state
  # Is there any way I can pass this info into another function?

  light_client_store =  LightClientStore(
    finalized_header = bootstrap_block_header, 
    current_sync_committee = bootstrap_sync_committee, 
    next_sync_committee = bootstrap_next_sync_committee,
    best_valid_update = None,
    optimistic_header = None,
    previous_max_active_participants = None,
    current_max_active_participants = None
  )

  # get_current_slot()
  #
  # RANDOM TEST VALUE! 
  # Most recent attested block header slot == 4235979...  so make current slot a few slots after
  current_slot = 4235989 
  
  light_client_update = LightClientUpdate(
    attested_header = attested_block_header,
    next_sync_committee = next_sync_committee,
    next_sync_committee_branch = next_sync_committee_branch,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    # A record of which validators in the current sync committee voted for the chain head in the previous slot.
    # Contains the sync committee's bitfield and signature required for verifying the attested header.
    #
    sync_aggregate = sync_aggregate,
    # Slot at which the aggregate signature was created (untrusted)    
    # 
    # THIS VALUE IS INCORRECT. IDK WHAT IT SHOULD BE, BUT THIS
    # VALUE ALLOWS validate_light_client_update() TO RUN
    # 
    signature_slot =  attested_block_header.slot + 1 
  )

  return light_client_store, light_client_update, fork_version



# Incorperate syncing to period inside of this function as well
# def syncs_to_current_period(bootstrap_period) -> int:
#
def sync_to_current_period(bootstrap_period) -> int:
  sync_period = bootstrap_period 
  
  while 1>0:
    response = updates_for_period(sync_period)
    updates = response.json()
    updates_status_code = response.status_code
   
    # Checks if api call executed properly 
    if updates_status_code == 500:
      sync_period = sync_period - 1 
      return sync_period
    else:

      # Should I try to pass the light client store and update functions into this function?
      # I can change the light client store's attributes from outside of the function.
      #  
      light_client_store, light_client_update, fork_version = instantiates_sync_period_data(sync_period)
      
      #  THIS FUNCTION IS THE ANTITHESIS OF WHAT UPDATESAPI.PY IS CONVERGING TOWARDS!      Ooooooooh aaaaaaah
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  # current slot   ?????
                                  # genesis_validators_root  ????
                                  fork_version
      )                   

      print('\n') 
      print("Sync period: " + str(sync_period)) 
      print('\n') 
      print("light_client_store: ")
      print(light_client_store.finalized_header.slot)
      light_client_store.finalized_header.slot = 69
      print('\n') 
      print("light_client_update: ")
      print(light_client_update.finalized_header.slot)
      
      # Increment the sync period every 12 seconds.
      time.sleep(12)
      sync_period += 1



bootstrap_period = 512
current_period = sync_to_current_period(bootstrap_period)
print("Current period: " + str(current_period))













# #                           ============================
# #                           COMMITTEE UPDATE'S VARIABLES 
# #                           ============================

# # I might need to run my clock function in here.  Is that bad design?

# bootstrap_period = 512
# current_period = sync_to_current_period(bootstrap_period)

# print("Now at current sync period")
# print(current_period)
# updates = updates_for_period(current_period).json()
# print(updates)

# # Figure out how to pass the updates variable to all objects outside of the while loop.  Global variable?
# # Place all of this code into a function so I can keep track of each sync period's data

# # ================================ 
# # ATTESTED BLOCK HEADER VARIABLES!
# # ================================ 
# attested_header = updates['data'][0]['attested_header']

# attested_block_header = BeaconBlockHeader (
#   slot = int(attested_header['slot']),
#   proposer_index = int(attested_header['proposer_index']),
#   parent_root =  parse_hex_to_byte(attested_header['parent_root']),
#   state_root =  parse_hex_to_byte(attested_header['state_root']),
#   body_root =  parse_hex_to_byte(attested_header['body_root'])
# )
# print(attested_block_header.slot)
# # Does the lodestar api serve the attested header proof?

# # ============================== 
# # NEXT SYNC COMMITTEE VARIABLES!
# # ==============================
# next_sync_committee = updates['data'][0]['next_sync_committee']
# next_list_of_keys = next_sync_committee['pubkeys']
# next_aggregate_pubkey = next_sync_committee['aggregate_pubkey']
# parse_list(next_list_of_keys)
# next_aggregate_pubkey = parse_hex_to_byte(next_aggregate_pubkey)

# next_sync_committee = SyncCommittee(
#   pubkeys = next_list_of_keys,
#   aggregate_pubkey = next_aggregate_pubkey
# )

# # -------------------------- 
# # Next Sync Committee Branch
# # --------------------------
# next_sync_committee_branch = updates['data'][0]['next_sync_committee_branch']
# parse_list(next_sync_committee_branch)


# # ==========================
# # FINALIZED BLOCK VARIABLES!
# # ========================== 
# finalized_header =  updates['data'][0]['finalized_header']

# finalized_block_header = BeaconBlockHeader (
#   slot = int(finalized_header['slot']),
#   proposer_index = int(finalized_header['proposer_index']),
#   parent_root =  parse_hex_to_byte(finalized_header['parent_root']),
#   state_root =  parse_hex_to_byte(finalized_header['state_root']),
#   body_root =  parse_hex_to_byte(finalized_header['body_root'])
# )
# # ---------------
# # Finality Branch 
# # --------------- 
# finality_branch = updates['data'][0]['finality_branch']
# parse_list(finality_branch) 

# # =========================                  
# # SYNC AGGREGATE VARIABLES!                    
# # ========================= 
# sync_aggregate = updates['data'][0]['sync_aggregate']
# sync_committee_hex = sync_aggregate['sync_committee_bits']
# sync_committee_signature = sync_aggregate['sync_committee_signature']
# sync_committee_bits = parse_hex_to_bit(sync_committee_hex) 
# sync_committee_signature = parse_hex_to_byte(sync_committee_signature)

# sync_aggregate = SyncAggregate(
#   sync_committee_bits = sync_committee_bits, 
#   sync_committee_signature = sync_committee_signature 
# )

# # ============                  
# # FORK_VERSION                    
# # ============ 
# fork_version =  updates['data'][0]['fork_version']
# fork_version = parse_hex_to_byte(fork_version)


# print(attested_block_header.slot)