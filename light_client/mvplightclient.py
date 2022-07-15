from bootstrapapi import (bootstrap_object,
                          bootstrap_block_header,
                          bootstrap_sync_committee,
                          trusted_block_root)
from containers import Root
from light_client.containers import BeaconBlockHeader
from light_client.specfunctions import process_slot_for_light_client_store
from updatesapi import instantiates_sync_period_data, updates_for_period
from specfunctions import compute_sync_committee_period_at_slot, initialize_light_client_store
import time
from time import ctime
import json
import requests

# A first milestone for a light client implementation is to HAVE A LIGHT CLIENT THAT SIMPLY TRACKS THE LATEST STATE/BLOCK ROOT.
def calls_api(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

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


if __name__ == "__main__":
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
  #  Step 1: Initialize the light client store
 
  #  Makes sure the current sync committee hashed against the branch is equivalent to the header state root.
  #  Proof that the bootstrap sync committee is verified from the checkpoint root 
  light_client_store = initialize_light_client_store(trusted_block_root,
                                                     bootstrap_object 
  )



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
  
  # Incorperate syncing to period inside of this function as well
  # def syncs_to_current_period(bootstrap_period) -> int:
  #
  def sync_to_current_period(bootstrap_period) -> int:
    sync_period = bootstrap_period 
    current_slot = 0 
    while 1>0:
      response = updates_for_period(sync_period)
      updates = response.json()
      updates_status_code = response.status_code
    
      # Checks if api call executed properly 
      if updates_status_code == 500:
        sync_period = sync_period - 1 
        return sync_period
      else:
        light_client_update, fork_version = instantiates_sync_period_data(sync_period)

        # TEST VALUES!
        # I need a function:      get_current_slot()         <---- I believe this is somewhere in beacon chain spec  
        current_slot = light_client_update.signature_slot
        genesis_validators_root = Root()

        # I have to update individual attributes, can't update a whole finalized header at once.  
        # Why?? The spec says you can update the entire finalized header, not just individual values
        # 
        #  THIS FUNCTION IS THE ANTITHESIS OF WHAT UPDATESAPI.PY IS CONVERGING TOWARDS!      Ooooooooh aaaaaaah
        # process_light_client_update(light_client_store, 
        #                             light_client_update, 
        #                             current_slot,
        #                             genesis_validators_root,
        #                             fork_version
        # )                   

        # When process_light_client_update() is running smoothly, this state transition has already occured.
        # Specifically, within apply_light_client_update()
        # For now, I'm updating the slots individually for testing purposes
        light_client_store.finalized_header.slot = light_client_update.finalized_header.slot
        
        # Increment the sync period every 12 seconds.
        time.sleep(1)
        sync_period += 1

  bootstrap_period = 512
  current_period = sync_to_current_period(bootstrap_period)
  # print("Current period: " + str(current_period))

  # #  Create this function! 
  # def sync_to_current_header() -> BeaconBlockHeader: 
  #   while 1>0:
  #     process_slot_for_light_client_store()







  # ///////////////////////////////////////////////
  # ----------------------------------------------
  # CREATE COMMITTEE UPDATES OBJECTS AND MERKLEIZE
  # ----------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  
"""  
                                     IMPORTANT QUESTION:

          How do I tie the finalized block header back to the bootstrap checkpoint root?
          Because right now there's a gap in the logic:  
          Yes the next sync committee hashes against merkle proof to equal the finalized state,
          but the finalized state isn't connected back to the checkpoint root.
          print(finalized_block_header_root)
 
                  For now, press on and execute spec functions properly
""" 




  # ///////////////////////////////////////////////
  # ----------------------------------------------
  #            BRING IN THE MVP SPEC!! 
  # ----------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
"""
  A light client maintains its state in a store object of type LightClientStore and receives update objects of type LightClientUpdate. 
  Every update triggers process_light_client_update(store, update, current_slot) where current_slot is the current slot based on some local clock.
"""


  # Before I start using the local clock mechanism, I need to get to the current sync committee
  # This means continually fetching the committee updates UNTIL there are no more updates to fetch.

  # How do I get the current_slot? Or should I have a while loop that continuously increments until it throws a fetch error?
  # compute_sync_committee_period_at_slot(current_slot) - compute_sync_committee_period_at_slot(bootstrap_block_header.slot) 

















  #                                   \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                    \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                    ========================================
  #                                            SYNC TO THE LATEST BLOCK:
  #                                    ========================================
  #                                    ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                   /////////////////// || \\\\\\\\\\\\\\\\\\\\