import inspect
import time
from time import ctime
import json
from types import SimpleNamespace
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
from specfunctions import compute_epoch_at_slot, compute_sync_committee_period ,validate_light_client_update
import requests

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

class InitializedBeaconBlockHeader:
  def __init__(self, slot, proposer_index, parent_root, state_root, body_root):
    self.slot = slot
    self.proposer_index = proposer_index
    self.parent_root = parent_root
    self.state_root = state_root
    self.body_root = body_root

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
"""

  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # ===================================================================
  # STEP 1:  Gather snapshot from node based on finality 
  #           checkpoint and place data into containers
  # ===================================================================
  # ///////////////////////////////////////////////////////////////////

  # ------------------------------------------
  # MAKE API CALLS FOR CHECKPOINT AND SNAPSHOT
  # ------------------------------------------

  #  ==========
  #  CHECKPOINT
  #  ==========
  checkpoint_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/finalized/finality_checkpoints"
  checkpoint = calls_api(checkpoint_url)
  finalized_checkpoint_root = checkpoint['data']['finalized']['root']  
  
  #  =========
  #  BOOTSTRAP
  #  =========
  bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/bootstrap/0x64f23b5e736a96299d25dc1c1f271b0ce4d666fd9a43f7a0227d16b9d6aed038" 
  bootstrap = calls_api(bootstrap_url)

  #  Block Header Data
  bootstrap_header_dict = bootstrap['data']['header']
  bootstrap_data = json.dumps(bootstrap_header_dict)                                            #  Converts dictionary to string that json.loads can utilize
  bootstrap_header = json.loads(bootstrap_data, object_hook=lambda d: SimpleNamespace(**d))     # Parse JSON into an object with attributes corresponding to dict keys.

  # Clean Block Header Data
  bootstrap_header.slot = int(bootstrap_header.slot)
  bootstrap_header.proposer_index = int(bootstrap_header.proposer_index)
  
  # Create a for loop that cycles through each item in the header, converting hex values to bytes 
  # parse_object(bootstrap_header)       Currently hard coded.  Fix this
  bootstrap_header.state_root = parse_hex_to_byte(bootstrap_header.state_root)
  bootstrap_header.parent_root = parse_hex_to_byte(bootstrap_header.parent_root) 
  bootstrap_header.body_root = parse_hex_to_byte(bootstrap_header.body_root) 



  # # This is going to be useless once I get this situation situated

  # bootstrap_header = bootstrap['data']['header']

  # # print(inspect.getmembers(bootstrap_header))


  # bootstrap_slot = int(bootstrap_header['slot'])
  # bootstrap_proposer_index = int(bootstrap_header['proposer_index'])
  # bootstrap_parent_root = bootstrap_header['parent_root']
  # bootstrap_state_root = bootstrap_header['state_root']
  # bootstrap_body_root = bootstrap_header['body_root']


  # bootstrap_object = InitializedBeaconBlockHeader(
  #   slot= int(bootstrap_header['slot']),
  #   proposer_index= int(bootstrap_header['proposer_index']),
  #   parent_root= bootstrap_header['parent_root'],
  #   state_root= bootstrap_header['state_root'],
  #   body_root= bootstrap_header['body_root']
  # ) 
 
 
 
  #  Sync Committee Data
  list_of_keys = bootstrap['data']['current_sync_committee']['pubkeys']
  current_aggregate_pubkey = bootstrap['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = bootstrap['data']['current_sync_committee_branch']
  
  # ---------------------------------------------------------
  # PARSE JSON INFORMATION ON BLOCK_HEADER AND SYNC_COMMITTEE
  # ---------------------------------------------------------

  #       Aggregate Key and Header Roots
  current_aggregate_pubkey = parse_hex_to_byte(current_aggregate_pubkey)
  # bootstrap_parent_root = parse_hex_to_byte(bootstrap_parent_root)
  # bootstrap_state_root = parse_hex_to_byte(bootstrap_state_root)
  # bootstrap_body_root = parse_hex_to_byte(bootstrap_body_root)

  #       List of Keys
  parse_list(list_of_keys) 
  
  #       Sync Committee Branch 
  parse_list(current_sync_committee_branch) 

  # ------------------------------------------------------
  # CREATE BOOTSTRAP BLOCK_HEADER AND SYNC COMMITTEE OBJECTS
  # ------------------------------------------------------
  
  # Bootstrap_block_header information has been reorganized.  Now do this with the other things 
  bootstrap_block_header =  BeaconBlockHeader(
    slot = bootstrap_header.slot, 
    proposer_index = bootstrap_header.proposer_index, 
    parent_root = bootstrap_header.parent_root,
    state_root = bootstrap_header.state_root,
    body_root = bootstrap_header.body_root
  )

  bootstrap_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )



  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  # ---------------------------------------------------------
  #                MERKLEIZE THE OBJECTS
  #
  #   Converts the sync committee object into a merkle root.
  # 
  #   If the state root derived from the sync_committee_root 
  #   combined with its proof branch matches the 
  #   header_state_root AND the block header root with this
  #   state root matches the checkpoint root, you know you're
  #   following the right sync committee.
  # ----------------------------------------------------------

  bootstrap_header_root =  View.hash_tree_root(bootstrap_block_header)
  bootstrap_committee_root = View.hash_tree_root(bootstrap_sync_committee) 
  # print("Current sync_committee_root: ")
  # print(sync_committee_root)

  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------

  #  Makes sure the current sync committee hashed against the branch is equivalent to the header state root.
  #  However, all of this information was given to us from the same server.  Hash the information given to us 
  #  (each attribute in BeaconBlockHeader(Container)) against the trusted, finalized checkpoint root to make sure
  #  server serving the bootstrap information for a specified checkpoint root wasn't lying.
  
  assert is_valid_merkle_branch(bootstrap_committee_root, 
                                current_sync_committee_branch, 
                                CURRENT_SYNC_COMMITTEE_INDEX, 
                                bootstrap_header.state_root) 
  
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
  """
  
  #                                    ////////////////////////////////////
  #                                    ====================================
  #                                    TURN DATA FROM UPDATE INTO VARIABLES
  #                                    ====================================
  #                                    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  
  # ==========================================
  # BOOTSTRAP'S NEXT SYNC COMMITTEE VARIABLES!
  # ==========================================
  
  bootstrap_sync_period = compute_sync_committee_period(compute_epoch_at_slot(bootstrap_header.slot))   #  511
  bootstrap_committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period=511&count=1" 
  bootstrap_committee_updates = calls_api(bootstrap_committee_updates_url)
  
  bootstrap_next_sync_committee = bootstrap_committee_updates['data'][0]['next_sync_committee']
  bootstrap_next_list_of_keys = bootstrap_next_sync_committee['pubkeys']
  bootstrap_next_aggregate_pubkey = bootstrap_next_sync_committee['aggregate_pubkey']

  # From hex to bytes
  parse_list(bootstrap_next_list_of_keys)
  bootstrap_next_aggregate_pubkey = parse_hex_to_byte(bootstrap_next_aggregate_pubkey)

  # Create bootstrap's next sync committee 
  bootstrap_next_sync_committee = SyncCommittee(
    pubkeys = bootstrap_next_list_of_keys,
    aggregate_pubkey = bootstrap_next_aggregate_pubkey
  )
  
  
  
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
  
  attested_header_slot_number = int(attested_header['slot'])
  attested_header_proposer_index = int(attested_header['proposer_index'])
  attested_header_parent_root =  attested_header['parent_root']
  attested_header_state_root =  attested_header['state_root']
  attested_header_body_root =  attested_header['body_root']
  
  # From hex to bytes
  attested_header_parent_root = parse_hex_to_byte(attested_header_parent_root)
  attested_header_state_root = parse_hex_to_byte(attested_header_state_root)
  attested_header_body_root = parse_hex_to_byte(attested_header_body_root)

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
  
  finalized_updates_slot_number = int(finalized_header['slot'])
  finalized_updates_proposer_index = int(finalized_header['proposer_index'])
  finalized_updates_parent_root =  finalized_header['parent_root']
  finalized_updates_state_root =  finalized_header['state_root']
  finalized_updates_body_root =  finalized_header['body_root']
  
  # From hex to bytes
  finalized_updates_parent_root = parse_hex_to_byte(finalized_updates_parent_root)
  finalized_updates_state_root = parse_hex_to_byte(finalized_updates_state_root)
  finalized_updates_body_root = parse_hex_to_byte(finalized_updates_body_root)

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



  """
                          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
                          !!!!!!!! IMPORTANT BLOCK VALUES !!!!!!!!!
                          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  """

  # print("attested header slot: " + str(attested_header_slot_number)) 
  # print("finalized header slot: " + str(finalized_updates_slot_number)) 
  # print("bootstrap header slot: " + str(bootstrap_slot)) 
  # print("Difference between bootstrap root and finalized root: " + str(finalized_updates_slot_number - bootstrap_slot)) 
  # print('\n') 
   
  # print("Bootstrap block's epoch: " + str(compute_epoch_at_slot(bootstrap_slot)))
  # print("Finalized block's epoch: " + str(compute_epoch_at_slot(finalized_updates_slot_number)))
  # print("Attested block's epoch: " + str(compute_epoch_at_slot(attested_header_slot_number)))

  # print("Bootstrap block's sync period: " + str(compute_sync_committee_period(compute_epoch_at_slot(bootstrap_slot))))
  # print("Finalized block's sync period: " + str(compute_sync_committee_period(compute_epoch_at_slot(finalized_updates_slot_number))))
  # print("Attested block's sync period: " + str(compute_sync_committee_period(compute_epoch_at_slot(attested_header_slot_number))))



  # ///////////////////////////////////////////////
  # ----------------------------------------------
  # CREATE COMMITTEE UPDATES OBJECTS AND MERKLEIZE
  # ----------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  attested_block_header =  BeaconBlockHeader(
    slot = attested_header_slot_number, 
    proposer_index = attested_header_proposer_index, 
    parent_root = attested_header_parent_root,
    state_root = attested_header_state_root,
    body_root = attested_header_body_root 
  )
  
  next_sync_committee = SyncCommittee(
    pubkeys = updates_list_of_keys,
    aggregate_pubkey = updates_aggregate_pubkey
  )

  finalized_block_header =  BeaconBlockHeader(
    slot = finalized_updates_slot_number, 
    proposer_index = finalized_updates_proposer_index, 
    parent_root = finalized_updates_parent_root,
    state_root = finalized_updates_state_root,
    body_root = finalized_updates_body_root 
  )

  sync_aggregate = SyncAggregate(
    sync_committee_bits = sync_committee_bits, 
    sync_committee_signature = sync_committee_signature 
  )

  attested_block_header_root =  View.hash_tree_root(attested_block_header)
  next_sync_committee_root = View.hash_tree_root(next_sync_committee) 
  finalized_block_header_root =  View.hash_tree_root(finalized_block_header)
  sync_aggregate_root =  View.hash_tree_root(sync_aggregate)



  # //////////////////////////////////////////////////////////////
  # -------------------------------------------------------------
  # PLACE OBJECTS INTO LIGHT CLIENT STORE AND LIGHT CLIENT UPDATE 
  # -------------------------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\/\\\\\\\\\\\
  
  """  
                                     IMPORTANT QUESTION:

          How do I tie the finalized block header back to the bootstrap checkpoint root?
          Because right now there's a gap in the logic:  
          Yes the next sync committee hashes against merkle proof to equal the finalized state,
          but the finalized state isn't connected back to the checkpoint root.
          print(finalized_block_header_root)
 
                  For now, press on and execute spec functions properly
  """ 
  # ===================
  # LIGHT CLIENT STORE
  # ===================
  light_client_store =  LightClientStore(
    finalized_header = bootstrap_block_header, 
    current_sync_committee = bootstrap_sync_committee, 
    next_sync_committee = bootstrap_next_sync_committee,

    #                              Figure out what these values are 
    # best_valid_update = ,
    # optimistic_header = ,
    # previous_max_active_participants = ,
    # current_max_active_participants = 
  )

  # ====================
  #  LIGHT CLIENT UPDATE 
  # ====================
  
  light_client_update = LightClientUpdate(
    attested_header = attested_block_header,
    next_sync_committee = next_sync_committee,
    next_sync_committee_branch = next_sync_committee_branch,
    finalized_header = finalized_block_header,
    finality_branch = finalized_updates_branch,
    # A record of which validators in the current sync committee voted for the chain head in the previous slot
    #
    # Contains the sync committee's bitfield and signature required for verifying the attested header
    sync_aggregate = sync_aggregate,
    # Slot at which the aggregate signature was created (untrusted)    I don't know this value
    signature_slot =  attested_header_slot_number - 1 
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

  current_slot = 420                                   # Where do I get this information?


  # Everything that relies on this local clock needs to go inside of this for loop
  # while 1>0:
  #   time.sleep(SECONDS_PER_SLOT)
  #   current_slot += 1 
  #   print(ctime())
    # print(current_slot)

  # process_slot_for_light_client_store(store: LightClientStore, current_slot: Slot) -> None:
  



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