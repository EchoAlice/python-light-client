from bootstrapapi import (bootstrap_block_header,
                          bootstrap_header, 
                          bootstrap_next_sync_committee, 
                          bootstrap_sync_committee, 
                          current_sync_committee_branch)
from updatesapi import (attested_block_header,
                        finalized_block_header,
                        finality_branch,
                        fork_version,
                        next_aggregate_pubkey,
                        next_list_of_keys,
                        next_sync_committee,
                        next_sync_committee_branch,
                        sync_aggregate,
                        sync_committee_bits,
                        sync_committee_signature,
)
from containers import (CURRENT_SYNC_COMMITTEE_INDEX, 
                        NEXT_SYNC_COMMITTEE_INDEX,
                        SECONDS_PER_SLOT, 
                        BeaconBlockHeader, 
                        LightClientStore, 
                        LightClientUpdate,
                        SyncAggregate, 
                        SyncCommittee)
from merkletreelogic import is_valid_merkle_branch 
from remerkleable.core import View
from specfunctions import compute_epoch_at_slot, compute_sync_committee_period_at_slot, process_slot_for_light_client_store,validate_light_client_update
import time
from time import ctime
import inspect
import json
import requests
from types import SimpleNamespace

# ctime()

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
  
  bootstrap_header_root =  View.hash_tree_root(bootstrap_block_header)
  bootstrap_committee_root = View.hash_tree_root(bootstrap_sync_committee) 
  # print("Current sync_committee_root: ")
  # print(sync_committee_root)

  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------
  
  """
   Makes sure the current sync committee hashed against the branch is equivalent to the header state root.
   However, all of this information was given to us from the same server.  Hash the information given to us 
   (each attribute in BeaconBlockHeader(Container)) against the trusted, finalized checkpoint root to make sure
   server serving the bootstrap information for a specified checkpoint root wasn't lying.
  """
  assert is_valid_merkle_branch(bootstrap_committee_root, 
                                current_sync_committee_branch, 
                                CURRENT_SYNC_COMMITTEE_INDEX, 
                                bootstrap_block_header.state_root) 
  
  # assert block_header_root == finalized_checkpoint_root   #  <--- Don't think this works right now. Need the bootstrap  
  #                                                                 api call to contain variable checkpoint 

  # checkpoint_in_question = '0x64f23b5e736a96299d25dc1c1f271b0ce4d666fd9a43f7a0227d16b9d6aed038'
  # checkpoint_root = parse_hex_to_byte(checkpoint_in_question)     # finalized_checkpoint_root
  
  # print("block_header_root: ") 
  # print(bootstrap_header_root)
  # print("checkpoint_root: ")
  # print(checkpoint_root)
  # assert bootstrap_header_root == checkpoint_root     
  # print("Proof that the bootstrap sync committee is verified from the checkpoint root") 




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

                          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
                          !!!!!!!! IMPORTANT BLOCK VALUES !!!!!!!!!
                          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  """

  print('\n') 
  print("attested header slot: " + str(attested_block_header.slot)) 
  print("finalized header slot: " + str(finalized_block_header.slot)) 
  print("bootstrap header slot: " + str(bootstrap_block_header.slot)) 
  print("Difference between bootstrap root and finalized root: " + str(finalized_block_header.slot-bootstrap_block_header.slot)) 
  print('\n') 
  print("Bootstrap block's epoch: " + str(compute_epoch_at_slot(bootstrap_block_header.slot)))
  print("Finalized block's epoch: " + str(compute_epoch_at_slot(finalized_block_header.slot)))
  print("Attested block's epoch: " + str(compute_epoch_at_slot(attested_block_header.slot)))
  print('\n') 
  print("Bootstrap block's sync period: " + str(compute_sync_committee_period_at_slot(bootstrap_block_header.slot)))
  print("Finalized block's sync period: " + str(compute_sync_committee_period_at_slot(finalized_block_header.slot)))
  print("Attested block's sync period: " + str(compute_sync_committee_period_at_slot(attested_block_header.slot)))
  print('\n') 



  # ///////////////////////////////////////////////
  # ----------------------------------------------
  # CREATE COMMITTEE UPDATES OBJECTS AND MERKLEIZE
  # ----------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  attested_block_header_root =  View.hash_tree_root(attested_block_header)
  next_sync_committee_root = View.hash_tree_root(next_sync_committee) 
  finalized_block_header_root =  View.hash_tree_root(finalized_block_header)
  sync_aggregate_root =  View.hash_tree_root(sync_aggregate)

  
  """  
                                     IMPORTANT QUESTION:

          How do I tie the finalized block header back to the bootstrap checkpoint root?
          Because right now there's a gap in the logic:  
          Yes the next sync committee hashes against merkle proof to equal the finalized state,
          but the finalized state isn't connected back to the checkpoint root.
          print(finalized_block_header_root)
 
                  For now, press on and execute spec functions properly
  """ 


  # //////////////////////////////////////////////////////////////
  # -------------------------------------------------------------
  # PLACE OBJECTS INTO LIGHT CLIENT STORE AND LIGHT CLIENT UPDATE 
  # -------------------------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\/\\\\\\\\\\\
  
  # ===================
  # LIGHT CLIENT STORE
  # ===================                                Should the finalized header be the bootstrap header?  Do I have the right things in the store container?  Look at Clara's code
  light_client_store =  LightClientStore(
    finalized_header = bootstrap_block_header, 
    current_sync_committee = bootstrap_sync_committee, 
    next_sync_committee = bootstrap_next_sync_committee,

    #                              Figure out what these values are.     I believe all "None" until we get to the current sync period 
    # best_valid_update = ,
    # optimistic_header = ,
    # previous_max_active_participants = ,
    # current_max_active_participants = 
  )


  current_slot = 4198846 + 6                                   # Where do I get this information?

  # ====================
  #  LIGHT CLIENT UPDATE 
  # ====================

  light_client_update = LightClientUpdate(
    attested_header = attested_block_header,
    next_sync_committee = next_sync_committee,
    next_sync_committee_branch = next_sync_committee_branch,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    # A record of which validators in the current sync committee voted for the chain head in the previous slot
    #
    # Contains the sync committee's bitfield and signature required for verifying the attested header
    sync_aggregate = sync_aggregate,
    # Slot at which the aggregate signature was created (untrusted)    I don't know this value
    signature_slot =  current_slot - 1 
  )
  # print(committee_updates) 




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


  # # Everything that relies on this local clock needs to go inside of this for loop
  # # 
  # while 1>0:
  #   # Increment the current slot every 12 seconds.  When slot increments, process slot
  #   time.sleep(SECONDS_PER_SLOT)
  #   current_slot += 1 
  #   process_slot_for_light_client_store(
  #     light_client_store,
  #     current_slot
  #   )  
  #   print(ctime())
  #   print(current_slot)

  # process_slot_for_light_client_store(store: LightClientStore, current_slot: Slot) -> None:
  

  print('All gravy')

  # validate_light_client_update(light_client_store,
  #                             light_client_update,
  #                             fork_version,
  #                             ) 















  #                                   \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                    \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                    ========================================
  #                                            SYNC TO THE LATEST BLOCK:
  #                                    ========================================
  #                                    ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                   /////////////////// || \\\\\\\\\\\\\\\\\\\\