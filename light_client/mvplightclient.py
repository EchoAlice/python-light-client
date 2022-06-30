from msilib.schema import Upgrade
import requests
from remerkleable.core import View
from containers import BeaconBlockHeader, SyncAggregate, SyncCommittee  #  LightClientStore,
from merkletreelogic import is_valid_merkle_branch 

# CONSTANTS
EPOCHS_PER_SYNC_COMMITTEE_PERIOD = 256      #   2**8
FINALIZED_ROOT_INDEX = 105   
CURRENT_SYNC_COMMITTEE_INDEX = 54 
NEXT_SYNC_COMMITTEE_INDEX = 55 

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

def get_sync_period(slot_number):
  sync_period = slot_number // 8192
  return sync_period

if __name__ == "__main__":
  #                                    
  #                                     \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                      \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                      =========================================
  #                                      INITIALIZATION/BOOTSTRAPPING TO A PERIOD:
  #                                      =========================================
  #                                      ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                     /////////////////// || \\\\\\\\\\\\\\\\\\\\
  #
  #     Get block header at slot N in period X = N // 16384
  #     Ask node for current sync committee + proof of checkpoint root
  #     Node responds with a snapshot
  #     
  #     Snapshot contains:
  #     A. Header- Block's header corresponding to the checkpoint root
  #     
  #           The light client stores a header so it can ask for merkle branches to 
  #           authenticate transactions and state against the header
  #
  #     B. Current sync committee- Public Keys and the aggregated pub key of the current sync committee
  #   
  #           The purpose of the sync committee is to allow light clients to keep track
  #           of the chain of beacon block headers. 
  #           Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
  #           allowing light clients to verify the sync committee with a Merkle branch from a 
  #           block header that they already know about, and use the public keys 
  #           in the sync committee to directly authenticate signatures of more recent blocks.
  #   
  #     C. Current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 


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
  # print(finalized_checkpoint_root)

  #  =========
  #  BOOTSTRAP
  #  =========
  bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/bootstrap/0x229f88ef9dad77baa53dc507ae23a60261968b54aebbe7875144cdf2e7c548d8" 
  bootstrap = calls_api(bootstrap_url)
  # print(bootstrap)

  #  Block Header Data
  bootstrap_header = bootstrap['data']['header']
  
  bootstrap_slot = int(bootstrap_header['slot'])
  bootstrap_proposer_index = int(bootstrap_header['proposer_index'])
  bootstrap_parent_root = bootstrap_header['parent_root']
  bootstrap_state_root = bootstrap_header['state_root']
  bootstrap_body_root = bootstrap_header['body_root']
  
  #  Sync Committee Data
  list_of_keys = bootstrap['data']['current_sync_committee']['pubkeys']
  current_aggregate_pubkey = bootstrap['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = bootstrap['data']['current_sync_committee_branch']
  
  # ---------------------------------------------------------
  # PARSE JSON INFORMATION ON BLOCK_HEADER AND SYNC_COMMITTEE
  # ---------------------------------------------------------

  #       Aggregate Key and Header Roots
  current_aggregate_pubkey = parse_hex_to_byte(current_aggregate_pubkey)
  bootstrap_parent_root = parse_hex_to_byte(bootstrap_parent_root)
  bootstrap_state_root = parse_hex_to_byte(bootstrap_state_root)
  bootstrap_body_root = parse_hex_to_byte(bootstrap_body_root)

  #       List of Keys 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parse_hex_to_byte(list_of_keys[i])
  
  #       Sync Committee Branch 
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parse_hex_to_byte(current_sync_committee_branch[i])

  # ------------------------------------------------------
  # CREATE CURRENT BLOCK_HEADER AND SYNC COMMITTEE OBJECTS
  # ------------------------------------------------------
  current_block_header =  BeaconBlockHeader(
    slot = bootstrap_slot, 
    proposer_index = bootstrap_proposer_index, 
    parent_root = bootstrap_parent_root,
    state_root = bootstrap_state_root,
    body_root = bootstrap_body_root
  )

  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )



  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  # ------------------------------------------------------
  #                MERKLEIZE THE OBJECTS
  #
  # Converts the sync committee object into a merkle root.
  # 
  # If the state root derived from the sync_committee_root 
  # combined with its proof branch matches the 
  # header_state_root AND the block header root with this
  # state root matches the checkpoint root, you know you're
  #  following the right sync committee.
  # ------------------------------------------------------

  block_header_root =  View.hash_tree_root(current_block_header)
  sync_committee_root = View.hash_tree_root(current_sync_committee) 
  # print("Current sync_committee_root: ")
  # print(sync_committee_root)

  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------

  #  Makes sure the current sync committee hashed against the branch is equivalent to the header state root.
  #  However, all of this information was given to us from the same server.  Hash the information given to us 
  #  (each attribute in BeaconBlockHeader(Container)) against the trusted, finalized checkpoint root to make sure
  #  server serving the bootstrap information for a specified checkpoint root wasn't lying.
  
  assert is_valid_merkle_branch(sync_committee_root, current_sync_committee_branch, CURRENT_SYNC_COMMITTEE_INDEX, bootstrap_state_root) 
  # assert block_header_root == finalized_checkpoint_root   #  <--- Don't think this works right now. Need the bootstrap  
  #                                                                 api call to contain variable checkpoint 

  # print("Header state root: " + str(header_state_root)) 
  # checkpoint_in_question = '0x229f88ef9dad77baa53dc507ae23a60261968b54aebbe7875144cdf2e7c548d8'
  # checkpoint_in_question = parse_hex_to_byte(checkpoint_in_question)     # finalized_checkpoint_root
  
  # print("block_header_root: ") 
  # print(block_header_root)
  # print(checkpoint_in_question)
  # print("Tahhhh daaaahh") 




  #                                  \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
  #                                   \\\\\\\\\\\\\\\\\\\   |   ////////////////////
  #                                   ==============================================
  #                                   GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
  #                                   ==============================================
  #                                   ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
  #                                  ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\


  # "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."

  # Get sycn period updates from current sync period to latest sync period

  # Fill in these containers and see if the information matches up where it should 
  
  # ////////////////////////////
  # ===========================
  # UNDERSTANDING THE BOOTSTRAP
  # ===========================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\

  # Bootstrap gives you... 
  # 
  #     Beacon Block header():          corresponding to Checkpoint root (or any block root specified)
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:                       <------------------------- The god object that every validator must agree on
  #            body_root:
  #         
  #     SyncCommittee():   
  #            current_sync_committee:  pubkeys[]
  #            aggregate_pubkey:
  
  #     *Additional information given*           <---------- Allows you to verify that the sync committee given is legitimate 
  #            current_sync_committee_branch:
  #
  #  Hashing the merkleized current_sync_committee root against the current_sync_committee_branch and
  #  comparing this to the given state root verifies that the current sync committee is legitamite.  
  # 
  
  #           The sync committee is so important because it allows the light client to keep up with the head of the blockchain
  #           efficiently and in real time by only having to check the signature that goes with the head block.  If majority of 
  #           committee signed the block, then you know that is the head of the chain.  Compare all information you want to check
  #           against the beacon state for validity. 
   
  
  # //////////////////////////////////
  # ==================================
  # UNDERSTANDING THE COMMITTEE_UPDATE
  # ==================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  # Committee update gives you...
  # 
  #     Attested Block header():          for sync period
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:                       <------------------------- The god object that every validator must agree on
  #            body_root:
  #
  #     SyncCommittee():   
  #            next_sync_committee: pubkeys[]
  #            aggregate_pubkey:
  #  
  #     next_sync_committee_branch:
  #
  #
  #
  #     Finalized Block header():                    
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:
  #            body_root:
  # 
  #     finality_branch:
  #
  #     sync_aggregate:
  #            sync_committee_bits:
  #            sync_committee_signature:
  #     fork_version:          
  #
  #
  # 
  #  
  # ... for each period you want:   from -> to 

  
  # ////////////////////////////////////
  # ====================================
  # TURN DATA FROM UPDATE INTO VARIABLES
  # ====================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  # Should I be getting the update for the period AFTER the bootstrap period or for the CURRENT period? 
  bootstrap_sync_period = get_sync_period(bootstrap_slot)   #  505
  committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period=505&count=1" 
  committee_updates = calls_api(committee_updates_url)
  print(committee_updates)

  # ================================ 
  # ATTESTED BLOCK HEADER VARIABLES!
  # ================================ 
  attested_header = committee_updates['data'][0]['attested_header']
  
  committee_updates_slot_number = int(attested_header['slot'])
  committee_updates_proposer_index = int(attested_header['proposer_index'])
  committee_updates_parent_root =  attested_header['parent_root']
  committee_updates_state_root =  attested_header['state_root']
  committee_updates_body_root =  attested_header['body_root']
  
  # From hex to bytes
  committee_updates_parent_root = parse_hex_to_byte(committee_updates_parent_root)
  committee_updates_state_root = parse_hex_to_byte(committee_updates_state_root)
  committee_updates_body_root = parse_hex_to_byte(committee_updates_body_root)

  # ================================= 
  # UPDATES SYNC COMMITTEE VARIABLES!
  # ================================= 
  updates_list_of_keys = committee_updates['data'][0]['next_sync_committee']['pubkeys']
  updates_aggregate_pubkey = committee_updates['data'][0]['next_sync_committee']['aggregate_pubkey']
  
  # From hex to bytes
  for i in range(len(updates_list_of_keys)):
    updates_list_of_keys[i] = parse_hex_to_byte(updates_list_of_keys[i])
  
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
  for i in range(len(next_sync_committee_branch)):
    next_sync_committee_branch[i] = parse_hex_to_byte(next_sync_committee_branch[i])
  
  # =================================================== 
  # Finalized Sync Committee Branch - from hex to bytes 
  # =================================================== 
  finalized_updates_branch = committee_updates['data'][0]['finality_branch']
  for i in range(len(finalized_updates_branch)):
    finalized_updates_branch[i] = parse_hex_to_byte(finalized_updates_branch[i])

  # =========================                  
  # SYNC AGGREGATE VARIABLES!                    
  # ========================= 
  sync_aggregate = committee_updates['data'][0]['sync_aggregate']
  sync_committee_hex = sync_aggregate['sync_committee_bits']
  sync_committee_signature = sync_aggregate['sync_committee_signature']
  
  # From hex to bytes (and bits)
  sync_committee_bits = parse_hex_to_bit(sync_committee_hex) 
  sync_committee_signature = parse_hex_to_byte(sync_committee_signature)
  

  # ///////////////////////////////////////////////
  # ----------------------------------------------
  # CREATE COMMITTEE UPDATES OBJECTS AND MERKLEIZE
  # ----------------------------------------------
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  next_block_header =  BeaconBlockHeader(
    slot = committee_updates_slot_number, 
    proposer_index = committee_updates_proposer_index, 
    parent_root = committee_updates_parent_root,
    state_root = committee_updates_state_root,
    body_root = committee_updates_body_root 
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

  next_block_header_root =  View.hash_tree_root(next_block_header)
  next_sync_committee_root = View.hash_tree_root(next_sync_committee) 
  finalized_block_header =  View.hash_tree_root(finalized_block_header)
  sync_aggregate =  View.hash_tree_root(sync_aggregate)
  



  assert is_valid_merkle_branch(next_sync_committee_root, next_sync_committee_branch, NEXT_SYNC_COMMITTEE_INDEX, finalized_updates_state_root) 
  print("TAHHHDAAAHHHH") 
  # finalized_checkpoint_root = parseHexToByte(finalized_checkpoint_root)



  # ====================
  #  LIGHT CLIENT STORE
  # ====================

  # Remember to turn all values that are roots into bytes!
  # current_light_client_store =  LightClientStore(
  #   finalized_header = finalized_checkpoint_root, 
  #   current_sync_committee = current_sync_committee, 
  #   next_sync_committee = next_sync_committee,

  #   #                              Figure out what these values are 
  #   # best_valid_update = ,
  #   # optimistic_header = ,
  #   # previous_max_active_participants = ,
  #   # current_max_active_participants = 
  # )


  # # Repeat call lightclient/committee_updates until you're at the current sync period. 

  














  #                                   \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                    \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                    ========================================
  #                                            SYNC TO THE LATEST BLOCK:
  #                                    ========================================
  #                                    ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                   /////////////////// || \\\\\\\\\\\\\\\\\\\\