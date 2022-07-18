from bootstrapapi import (bootstrap_object,
                          bootstrap_block_header,
                          bootstrap_sync_committee,
                          trusted_block_root)
from containers import (current_time, 
                        Root, 
                        MIN_GENESIS_TIME, 
                        SECONDS_PER_SLOT,
                        BeaconBlockHeader)
from updatesapi import instantiates_sync_period_data, updates_for_period
from specfunctions import (compute_sync_committee_period_at_slot, 
                           initialize_light_client_store,
                           process_light_client_update, 
                           process_slot_for_light_client_store)
import time
from time import ctime
import json
import requests

def calls_api(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

"""
  Asynchronously, a light client maintains a local clock for the current slot, epoch, and sync  
  period, knowing exactly when the sync committee changes and to request a header update.
"""
def get_current_slot(current_time, genesis_time):
  current_slot = (current_time - genesis_time) // SECONDS_PER_SLOT
  return current_slot

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

# Incorperate syncing to period inside of this function as well
# def syncs_to_current_period(bootstrap_period) -> int:
#
def sync_to_current_period(light_client_store) -> int:
  sync_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot) 
  while 1>0:
    response = updates_for_period(sync_period)
    updates = response.json()
    updates_status_code = response.status_code
  
    # Checks if api call executed properly 
    if updates_status_code == 500:
      sync_period = sync_period - 1 
      return sync_period
    else:
      light_client_update = instantiates_sync_period_data(sync_period)

      # TEST VALUE!                   Current attested slot + 1000000
      current_slot = 42527410                                        
      genesis_validators_root = Root()

      #  THIS FUNCTION IS THE ANTITHESIS OF WHAT UPDATESAPI.PY IS CONVERGING TOWARDS!
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root
      )                   

      # When process_light_client_update() is running smoothly, this state transition has already occured.  (Within apply_light_client_update())
      # 
      # For testing purposes:
      # light_client_store.finalized_header = light_client_update.finalized_header
      
      # Increment the sync period until we reach the current period.  
      # Time doesn't matter when getting to the current period. Matters only once we get there
      time.sleep(1)
      sync_period += 1

def sync_to_current_slot(current_period) -> BeaconBlockHeader:
  while 1>0:
    # Make update beacon_block_header calls to _________
    
    # Random to stop warning 
    print(current_period) 

  current_block_header = "dummy" 
  return current_block_header


if __name__ == "__main__":
  #  Step 1: Initialize the light client store
  light_client_store = initialize_light_client_store(trusted_block_root,
                                                     bootstrap_object 
  )
  #  Step 2: Sync from bootstrap period to current period 
  current_period = sync_to_current_period(light_client_store)

  current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
  print(current_slot)



  #  Step 3: Sync from current period to current block header
  # current_block_header = sync_to_current_slot(current_period)

  #  ^ Where should I put the while loop?  Right here, or within sync_to_current_slot()?
  #    First trying it within sync_to_current_slot function 




  # THIS WAS CHAINSAFE'S TYPESCRIPT FUNCTION FOR CURRENT SLOT.  Maybe I can implement something similar?
  #
  # export function getCurrentSlot(config: IChainConfig, genesisTime: number): Slot {
  #   const diffInSeconds = Date.now() / 1000 - genesisTime;
  #   return Math.floor(diffInSeconds / config.SECONDS_PER_SLOT);
  # }




  






  

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