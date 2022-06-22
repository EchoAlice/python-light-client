from email import header
import requests
from remerkleable.core import View
from containers import SyncCommittee
from merkletreelogic import checkMerkleProof 

# A first milestone for a light client implementation is to HAVE A LIGHT CLIENT THAT SIMPLY TRACKS THE LATEST STATE/BLOCK ROOT.
def callsAPI(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

def parseHexToByte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def index_to_path(index):
  path = bin(index)
  if path[:2] == '0b':
    path = path[2:]
  return path

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

  # CHECKPOINT-
  checkpoint_url = "https://api.allorigins.win/raw?url=https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/head/finality_checkpoints" 
  checkpoint = callsAPI(checkpoint_url)
  finalized_checkpoint_root = checkpoint['data']['finalized']['root']  

  # SNAPSHOT-
  snapshot_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/snapshot/0xe7ec5a97896da6166bb56b89f9fcb426e13b620b1587dbedda258fd4faa00ab5" 
  snapshot = callsAPI(snapshot_url)
  print(snapshot) 
  header_state_root = snapshot['data']['header']['state_root']
  list_of_keys = snapshot['data']['current_sync_committee']['pubkeys']
  hex_aggregate_pubkey = snapshot['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = snapshot['data']['current_sync_committee_branch']


  # ----------------------------------------------------------
  # PARSE JSON INFORMATION ON SYNC COMMITTEE FROM HEX TO BYTES
  # ----------------------------------------------------------

  #       Aggregate Key and Header State Root
  current_aggregate_pubkey = parseHexToByte(hex_aggregate_pubkey)
  header_state_root = parseHexToByte(header_state_root)
  
  #       List of Keys 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parseHexToByte(list_of_keys[i])
  
  #       Sync Committee Branch 
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parseHexToByte(current_sync_committee_branch[i])

  # ----------------------------
  # CREATE SYNC COMMITTEE OBJECT
  # ----------------------------

  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )



  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  # -----------------------------------------------------
  #         MERKLEIZE THE SYNC COMMITTEE OBJECT
  #
  # Converts the sync committee object into a merkle root
  # -----------------------------------------------------
  
  sync_committee_root = View.hash_tree_root(current_sync_committee) 
  
  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------

  # 54 in binary, flipped around 
  index = 54
  path = '011011' 
  
  # Compare hashed answer to the BEACON BLOCK STATE ROOT that the sync committee is a part of!
  assert checkMerkleProof(sync_committee_root, current_sync_committee_branch, path) == header_state_root
  
  
  #                                  \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
  #                                   \\\\\\\\\\\\\\\\\\\   |   ////////////////////
  #                                   ==============================================
  #                                   GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
  #                                   ==============================================
  #                                   ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
  #                                  ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\


  # "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."

  # What sync periods do I need to get committee_updates for? 
  
  #              |
  #              V
  # From current sync period to latest sync period




  # Fill in these containers and see if the information matches up where it should 
  
  # //////////////////////////
  # ==========================
  # UNDERSTANDING THE SNAPSHOT
  # ==========================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\


  #           PROBLEM:
  # Do I need to hash the beacon block header container together and compare that to the checkpoint root?  
  # I think I do.  This way I'm not blindly trusting that the state root given to me is legitimate 

  # Don't worry about verifying the block header to the checkpoint root right now.
  # Implement that after understanding the committee_update



  # Snapshot gives you... 
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
  #                               Why is the sync committee so important? 




  # =============================================================
  # Compare values between the snapshot and the committee updates             (Make pretty program comparing bytes in containers later)
  # =============================================================
  #                                                            Merkleizing this beacon block header (should) give you the finalized block root. 
  # Snapshot Beacon Block header:                              Finalized block root --->    root: 0xe7ec5a97896da6166bb56b89f9fcb426e13b620b1587dbedda258fd4faa00ab5  
  #            slot: 4090208                                                                       epoch: 127819 
  #            proposer_index: 169657
  #            parent_root: 0x9509dd922c5627b4580f32ae4fbdff01b987b84be1b217d9fce5106dd1b02bb5
  #            state_root: 0xf4f0a5782f3cac46abc52441e32e960e31307a3144120223d83833c110ef5aa5                
  #            body_root:  0x55e7dc7935d59e3e0aeb61fd8957f33d6f0f63e0027af5322778f55bb277a04c
  #         
  #     SyncCommittee():   
  #            current_sync_committee:  pubkeys[]
  #            aggregate_pubkey: 0xb48a95f1b812e42065686ed2ea1a9c094c7aa697d82914294c12c53b5b2c9a53ef8b86d2a8b95b139ca72f8e37741d8f
  # 
  #            current_sync_committee_branch': ['0x0ba8314228d581dff1a3c6dd3cfb56613127ffd33953bfdb9bd7aac80aa283b0', 
  #                                             '0xd771018516266d2dfe5a497468c30bd147e444315a8fc2717c0bf73e66416794', 
  #                                             '0x843daed3ecbb35a0d6ec7cd388ea2a3bd286817aafa273f30213a8091c77bd02', 
  #                                             '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c', 
  #                                             '0xd03297844f949c061d54184b78608b07a0ef6c3d44966a9848c8d3e9f8862174']


  # Current sync period:                        (Based off of snapshot slot number)
  # sync_period = 4090208 // 8192                 # Period: 499
  # print(sync_period)

  #                                    Check tomorrow if committee update holds true.  DON'T UPDATE CHECKKPOINT ROOT!

  # I believe "from" serves last information from a specified period
  # while "to" serves the first information from a specified period.

  
  #     Committee Update Attested Block header():                 
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:
  #            body_root:
  #
  #     SyncCommittee():   
  #            next_sync_committee: pubkeys[]
  #            aggregate_pubkey:
  #     next_sync_committee_branch:
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







  # //////////////////////////////////
  # ==================================
  # UNDERSTANDING THE COMMITTEE_UPDATE
  # ==================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/committee_updates?from=499&to=500" 
  committee_updates = callsAPI(committee_updates_url)
  print("\n") 
  print("Committee_updates: ") 
  print(committee_updates)
   
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
  #     ** FIND OUT WHERE THIS DATA STRUCTURE LIES **
  #
  #
  #     Finalized Block header():                    <---- This might not be the correct label.  Figure out what I'm looking at!
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
  
  # print(committee_updates)
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  # Compare the merkleized next_sync committee to the state root from the snapshot
  



  # # This only gives current sync committee
  # # Call the snapshot of the next beacon state given in checkpoint 



  # # What periods do I sync from?
  # committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/committee_updates?from=497&to=498" 
  # committee_updates = callsAPI(committee_updates_url)
  # # print(committee_updates)
  # committee_updates_slot_number = int(committee_updates['data'][0]['attested_header']['slot'])
  # # Snapshot 
  # #    'slot': '4075744'
  # # Committee_updates: 
  # #    'slot': '4071629'

  # # Sync period:
  # sync_period = 4075744 // 8192
  # print(sync_period)
  
  
  
  # # Is committee updates information one sync period ahead of current period?
  # # Why is the slot difference negative?
  # slot_difference =  committee_updates_slot_number - snapshot_slot_number
  # print("Slot difference: " + str(slot_difference)) 
  
 
  # # if slot_difference <= 8192 & slot_difference > 0:
  # #   print("Probably next slot.")               #  I still dont know if the checkpoint is the final block of a period or the first block of the next     

  
  # print('Snapshot state root: ' + str()) 
  # committee_updates_parent_root = committee_updates['data'][0]['attested_header']['parent_root']
  # print("Committee update parent root: " + str(committee_updates_parent_root)) 

  # # next_list_keys = "dummy" 
  # # next_aggregate_pubkey = "dummy" 
  
  # # # Call lightclient/committee_updates to get committee updates from that period to the current period
  # # next_sync_committee = SyncCommittee(
  # #   pubkeys = next_list_keys,
  # #   aggregate_pubkey = next_aggregate_pubkey
  # # )

  # # next_sync_committee_root = View.hash_tree_root(next_sync_committee) 

  # # 55 in binary, flipped around 
  # next_index = 55
  # next_path = "111011"

  # # checkMerkleProof(next_sync_committee_root, next_sync_branch, next_path)







  # Figure out what all I need to store in the LightClientStore Container
  # Do I need to have light client store container initialized first? 



  #                                   \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                    \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                    ========================================
  #                                    SYNC TO THE LATEST FINALIZED CHECKPOINT:
  #                                    ========================================
  #                                    ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                   /////////////////// || \\\\\\\\\\\\\\\\\\\\