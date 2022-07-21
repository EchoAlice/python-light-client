from bootstrapapi import (bootstrap_object,
                          bootstrap_block_header,
                          bootstrap_sync_committee,
                          trusted_block_root)
from containers import (genesis_validators_root,
                        Root,
                        EPOCHS_PER_SYNC_COMMITTEE_PERIOD,
                        MIN_GENESIS_TIME, 
                        SECONDS_PER_SLOT,
                        SLOTS_PER_EPOCH,
                        uint64,
                        BeaconBlockHeader)
from updatesapi import (calls_api, 
                        initializes_block_header, 
                        instantiates_sync_period_data,
                        instantiates_finality_update_data, 
                        instantiates_optimistic_update_data, 
                        updates_for_period)
from specfunctions import (compute_sync_committee_period_at_slot, 
                           initialize_light_client_store,
                           process_light_client_update,
                           process_light_client_finality_update,
                           process_light_client_optimistic_update, 
                           process_slot_for_light_client_store)
import time
import json
import requests


def parse_hex_to_bit(hex_string):
  int_representation = int(hex_string, 16)
  binary_vector = bin(int_representation) 
  if binary_vector[:2] == '0b':
    binary_vector = binary_vector[2:]
  return binary_vector 

def parse_hex_to_byte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def parse_list(list):
  for i in range(len(list)):
    list[i] = parse_hex_to_byte(list[i])

def get_current_slot(current_time, genesis_time):
  current_slot = (current_time - genesis_time) // SECONDS_PER_SLOT
  return current_slot

def get_current_epoch(current_time, genesis_time):
  current_epoch = (current_time - genesis_time) // (SECONDS_PER_SLOT * SLOTS_PER_EPOCH)
  return current_epoch

def get_current_sync_period(current_time, genesis_time):
  current_sync_period = (current_time - genesis_time) // (SECONDS_PER_SLOT * SLOTS_PER_EPOCH * EPOCHS_PER_SYNC_COMMITTEE_PERIOD)
  return current_sync_period

def sync_to_current_period(light_client_store) -> int:
  sync_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)     # Which variable should I use to compute the sync period?
  while 1>0:
    current_time = uint64(int(time.time()))
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    updates = updates_for_period(sync_period)
    updates_status_code = updates.status_code

    # Checks if api call executed properly 
    if updates_status_code == 500:
      sync_period = sync_period - 1 
      return light_client_update
    else:
      light_client_update = instantiates_sync_period_data(sync_period)
      print("Sync period: " + str(compute_sync_committee_period_at_slot(light_client_update.finalized_header.slot)))
      #  THIS FUNCTION IS THE ANTITHESIS OF WHAT UPDATESAPI.PY IS CONVERGING TOWARDS!
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
      time.sleep(1)
      # Increment the sync period until we reach the current period.  
      sync_period += 1


# This function is where the light client receives current updates
def sync_to_current_finalized_header(light_client_store, light_client_update):          
  previous_sync_period = 0 
  previous_epoch = 0
  previous_slot = 0
  while 1>0:
    current_time = uint64(int(time.time()))                          # Where should i put the time variables?  I want them to be outside of these functions 
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
    current_sync_period = get_current_sync_period(current_time, MIN_GENESIS_TIME) 

    #  Is it ok for all these conditions to be triggered?  
    #  Or do I need to only allow one condition occur per loop?  (if, elif) 
    #
    #  More work to be done here! 
    if current_sync_period - previous_sync_period == 1:
      light_client_update = instantiates_sync_period_data(current_sync_period) 
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
    if current_epoch - previous_epoch == 1:
      current_finality_update_message = calls_api(current_finality_update_url).json()
      finality_update = instantiates_finality_update_data(current_finality_update_message) 
      process_light_client_finality_update(light_client_store, 
                                           finality_update, 
                                           current_slot, 
                                           genesis_validators_root) 

    if current_slot - previous_slot == 1:
      current_header_update_message = calls_api(current_header_update_url).json()                #    Where should this go? If it's outside of the function, 
      print("light_client_store.optimistic_header")                                              #    the calls_api() just returns the first value it called 
      print(light_client_store.optimistic_header) 
      process_slot_for_light_client_store(light_client_store, current_slot)               
      optimistic_update = instantiates_optimistic_update_data(current_header_update_message)     # Bug inside of here
      process_light_client_optimistic_update(light_client_store,
                                             optimistic_update,
                                             current_slot,
                                             genesis_validators_root) 


    previous_sync_period = current_sync_period
    previous_epoch = current_epoch 
    previous_slot = current_slot 
    time.sleep(1)
  return



# ================
# UPDATE VARIABLES
# ================
current_finality_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/finality_update/" 
current_header_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/optimistic_update/" 

if __name__ == "__main__":
  """ 
    Step 1: Initialize the light client store
  """
  light_client_store = initialize_light_client_store(trusted_block_root, bootstrap_object)
  
  """  
    Step 2: Sync from bootstrap period to current period 
  """
  light_client_update = sync_to_current_period(light_client_store)

  """
   Step 3: Sync from current period to current finalized block header. 
   Keep up with the most recent finalized header (Maybe each slot if Lodestar's API is fire.  Ask Cayman)
  """
  sync_to_current_finalized_header(light_client_store, light_client_update)


  # ^^^^ Can I access the light_client_store and light_client_update objects outside of this function?  














#               ==============================================================================
#               CHANGE CONDITIONAL STATEMENT TO THIS IF YOU WANT TO SYNC TO THE CURRENT BLOCK!
#               ==============================================================================
# 
#
#
# # Maybe I should just sync to the current finalized header... The attested header updates aren't super reliable with Lodestar
    
#  Change conditional statement to this if you want to sync to the current block!
#   
# 
#     process_light_client_optimistic update 
#  
#     previous_slot = 0
#
#     current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
#     if current_slot - previous_slot == 1 :                 
#       current_attested_header_message = current_update['data']['attested_header'] 
#       current_attested_header = initializes_block_header(current_attested_header_message)
#       print("My current slot has updated")
#       print("Lodestar's attested header slot: " + str(current_attested_header.slot))
#     previous_slot = current_slot 
