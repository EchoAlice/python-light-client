from bootstrapapi import (bootstrap_object,
                          bootstrap_block_header,
                          bootstrap_sync_committee,
                          trusted_block_root)
from containers import (CURRENT_SYNC_COMMITTEE_INDEX, 
                        NEXT_SYNC_COMMITTEE_INDEX,
                        SECONDS_PER_SLOT, 
                        BeaconBlockHeader,
                        LightClientBootstrap, 
                        LightClientStore, 
                        LightClientUpdate,
                        SyncAggregate, 
                        SyncCommittee)
from merkletreelogic import is_valid_merkle_branch 
from remerkleable.core import View
from specfunctions import compute_epoch_at_slot, compute_sync_committee_period_at_slot, initialize_light_client_store, process_slot_for_light_client_store,validate_light_client_update
import time
from time import ctime
import inspect
import json
import requests
from types import SimpleNamespace

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
                                      \\\\\\\\\\\\\\\\\\\ || ////////////////////
                                       \\\\\\\\\\\\\\\\\\\  ////////////////////
                                       =========================================
                                       INITIALIZATION/BOOTSTRAPPING TO A PERIOD:
                                       =========================================
                                       ///////////////////  \\\\\\\\\\\\\\\\\\\\
                                      /////////////////// || \\\\\\\\\\\\\\\\\\\\
  
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




  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  ===================================================================
  STEP 1:  Gather snapshot from node based on finality 
            checkpoint and place data into containers
  ===================================================================
  ///////////////////////////////////////////////////////////////////



  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  =================================================
  STEP 2: Verify Merkle branch from sync committee
  =================================================
  /////////////////////////////////////////////////
 
  ---------------------------------------------------------
                 MERKLEIZE THE OBJECTS
  
    Converts the sync committee object into a merkle root.
  
    If the state root derived from the sync_committee_root 
    combined with its proof branch matches the 
    header_state_root AND the block header root with this
    state root matches the checkpoint root, you know you're
    following the right sync committee.
  ----------------------------------------------------------
  """


  #  Step 1: Initialize the light client store
 
  #  Makes sure the current sync committee hashed against the branch is equivalent to the header state root.
  #  Proof that the bootstrap sync committee is verified from the checkpoint root 
  light_client_store = initialize_light_client_store(trusted_block_root,
                                                     bootstrap_object 
  )

  print(light_client_store.finalized_header)






  #                                  \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
  #                                   \\\\\\\\\\\\\\\\\\\   |   ////////////////////
  #                                   ==============================================
  #                                   GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
  #                                   ==============================================
  #                                   ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
  #                                  ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\

"""
  "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."
  Get sycn period updates from current sync period to latest sync period
"""



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