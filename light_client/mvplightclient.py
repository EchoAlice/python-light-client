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
                        updates_for_period)
from specfunctions import (compute_sync_committee_period_at_slot, 
                           initialize_light_client_store,
                           process_light_client_update, 
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

"""
  Asynchronously, a light client maintains a local clock for the current slot, epoch, and sync  
  period, knowing exactly when the sync committee changes and to request a header update.
"""
def get_current_slot(current_time, genesis_time):
  current_slot = (current_time - genesis_time) // SECONDS_PER_SLOT
  return current_slot

def get_current_epoch(current_time, genesis_time):
  current_epoch = (current_time - genesis_time) // (SECONDS_PER_SLOT * SLOTS_PER_EPOCH)
  return current_epoch

def get_current_sync_period(current_time, genesis_time):
  current_sync_period = (current_time - genesis_time) // (SECONDS_PER_SLOT * SLOTS_PER_EPOCH * EPOCHS_PER_SYNC_COMMITTEE_PERIOD)
  return current_sync_period

# Incorperate syncing to period inside of this function as well
# def syncs_to_current_period(bootstrap_period) -> int:
#
def sync_to_current_period(light_client_store) -> int:
  sync_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot) 
  while 1>0:
    updates = updates_for_period(sync_period)
    updates_status_code = updates.status_code

    # Checks if api call executed properly 
    if updates_status_code == 500:
      sync_period = sync_period - 1 
      print("Sync period: " + str(sync_period)) 
      return light_client_update
    else:
      light_client_update = instantiates_sync_period_data(sync_period)

      current_time = uint64(int(time.time()))
      current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)

      #  THIS FUNCTION IS THE ANTITHESIS OF WHAT UPDATESAPI.PY IS CONVERGING TOWARDS!
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root
      )                   
      
      # Time doesn't matter when getting to the current period. Matters only once we get there
      time.sleep(1)
      # Increment the sync period until we reach the current period.  
      sync_period += 1

# This function is where the light client receives update objects of type LightClientUpdate

# Maybe I should just sync to the current finalized header... The attested header updates aren't super reliable with Lodestar
# Can I access the light_client_store and light_client_update objects outside of this function?  I'd have to break out of it first
def sync_to_current_finalized_header(light_client_store ,light_client_update):          
  previous_slot = 0
  previous_epoch = 0
  previous_period = 0 
  while 1>0:
    current_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/finality_update/" 
    current_update = calls_api(current_update_url).json()

    current_time = uint64(int(time.time()))
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
    current_period = get_current_sync_period(current_time, MIN_GENESIS_TIME)
    
    # Get to current finalized header.  Continuously call the update from here on out 
    # I need to get ALL information passed from the current_update into update containers!
    
    if current_epoch - previous_epoch == 1:
      # print("My current epoch has updated")
      current_finalized_header_message = current_update['data']['finalized_header'] 
      current_finalized_header = initializes_block_header(current_finalized_header_message)
      
      # process_slot_for_light_client_store()                                     # This function call might only be necessary if calling an update every slot 
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root
      )                   

    # Would getting rid of this sleep timer break my computer??
    previous_epoch = current_epoch 
    time.sleep(1)

  return


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
   Step 3: Sync from current period to current block header. 
   Keep up with the most recent finalized header (Maybe each slot if Lodestar's API is fire.  Ask Cayman)
  """
  sync_to_current_finalized_header(light_client_store, light_client_update)


















#               ==============================================================================
#               CHANGE CONDITIONAL STATEMENT TO THIS IF YOU WANT TO SYNC TO THE CURRENT BLOCK!
#               ==============================================================================
# 
#
#
# # Maybe I should just sync to the current finalized header... The attested header updates aren't super reliable with Lodestar
# def sync_to_current_finalized_header(light_client_store ,light_client_update) -> BeaconBlockHeader:
#   previous_slot = 0
#   previous_epoch = 0
#   previous_period = 0 
#   while 1>0:
#     current_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/finality_update/" 
#     current_update = calls_api(current_update_url).json()

#     current_time = uint64(int(time.time()))
#     current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
#     current_period = get_current_sync_period(current_time, MIN_GENESIS_TIME)
    
#     #  Change conditional statement to this if you want to sync to the current block!
#     # 
#     # current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
#     # if current_slot - previous_slot == 1 :                 
#       # current_attested_header_message = current_update['data']['attested_header'] 
#       # current_attested_header = initializes_block_header(current_attested_header_message)
#       # print("My current slot has updated")
#       # print("Lodestar's attested header slot: " + str(current_attested_header.slot))
#     # previous_slot = current_slot 


#     # Get to current finalized header.  Continuously call the update from here on out 
#     # I need to get ALL information passed from the current_update into update containers!
#     if current_epoch - previous_epoch == 1:
#       print("My current epoch has updated")
#       current_finalized_header_message = current_update['data']['finalized_header'] 
#       current_finalized_header = initializes_block_header(current_finalized_header_message)
#       # process_slot_for_light_client_store() 
#       # process_light_client_update() 
  
#     # Would getting rid of this sleep timer break my computer??
#     previous_epoch = current_epoch 
#     time.sleep(1)








  # # This gets you an updated slot.  The light client needs to ~listen~ for when it is time to ask for an update and respond accordingly  
  # while 1>0:
  #   current_time = uint64(int(time.time()))
  #   current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
  #   current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
  #   current_period = get_current_sync_period(current_time, MIN_GENESIS_TIME)
  #   print("\n")
  #   # print("current time: " + str(current_time))
  #   print("current slot: " + str(current_slot)) 
  #   # print("current epoch: " + str(current_epoch))                          #  Request a finalized update every time the current epoch increments.  
  #   # print("current period: " + str(current_period))                        #  Every epoch incremented brings a new latest finalized header 
    
  #   print("Current slot % seconds per slot = " + str(current_slot % SECONDS_PER_SLOT)) 
    
    
  #   # process_slot_for_light_client_store(light_client_store, current_slot) 
  #   time.sleep(1)













  






  

  #  Create this function! 
  # def sync_to_current_header() -> BeaconBlockHeader: 
  #   while 1>0:
  #     get_current_slot()         <---- I believe this is somewhere in beacon chain spec  
  # 
  #     process_slot_for_light_client_store()








  
"""  
                                     IMPORTANT QUESTION:

          How do I tie the finalized block header back to the bootstrap checkpoint root?
          Because right now there's a gap in the logic:  
          Yes the next sync committee hashes against merkle proof to equal the finalized state,
          but the finalized state isn't connected back to the checkpoint root.
          print(finalized_block_header_root)
 
                  For now, press on and execute spec functions properly
""" 


"""                             
  
      Get block header at slot N in period X = N // 16384
      Ask node for current sync committee + proof of checkpoint root
      Node responds with a snapshot
      
      Snapshot contains:
      A. Header- Block's header corresponding to the checkpoint root
      
            The light client stores a header so it can ask for merkle branches to 
            authenticate transactions and state against the header
  
      B. Current sync committee- Public Keys and the aggregated pub key of the current sync committee
    
            The purpose of the sync committee is to allow light clients to keep track
            of the chain of beacon block headers. 
            Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
            allowing light clients to verify the sync committee with a Merkle branch from a 
            block header that they already know about, and use the public keys 
            in the sync committee to directly authenticate signatures of more recent blocks.
    
      C. Current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 
"""


"""
                                      \\\\\\\\\\\\\\\\\\\ || ////////////////////
                                       \\\\\\\\\\\\\\\\\\\  ////////////////////
                                       =========================================
                                       INITIALIZATION/BOOTSTRAPPING TO A PERIOD:
                                       =========================================
                                       ///////////////////  \\\\\\\\\\\\\\\\\\\\
                                      /////////////////// || \\\\\\\\\\\\\\\\\\\\
"""


"""
                                   \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
                                    \\\\\\\\\\\\\\\\\\\   |   ////////////////////
                                    ==============================================
                                    GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
                                    ==============================================
                                    ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
                                   ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\

      "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."
                        Get sycn period updates from current sync period to latest sync period
"""


""" 
  Introduces a new `LightClientBootstrap` structure to allow setting up a
  `LightClientStore` with the initial sync committee and block header from
  a user-configured trusted block root.

  This leads to new cases where the `LightClientStore` is only aware of
  the current but not the next sync committee. As a side effect of these
  new cases, the store's `finalized_header` may now  advance into the next
  sync committee period before a corresponding `LightClientUpdate` with
  the new sync committee is obtained, improving responsiveness.

  Note that so far, `LightClientUpdate.attested_header.slot` needed to be
  newer than `LightClientStore.finalized_header.slot`. However, it is now
  necessary to also consider certain older updates to try and backfill the
  `next_sync_committee`. The `is_better_update` helper is also updated to
  improve `best_valid_update` tracking.

            - Etan Status:    commit 654970c6057011e407299a61610c697662c335bd
  """


"""
  A light client maintains its state in a store object of type LightClientStore and receives update objects of type LightClientUpdate. 
  Every update triggers process_light_client_update(store, update, current_slot) where current_slot is the current slot based on some local clock.
"""