import requests
from remerkleable.basic import uint64
from remerkleable.core import View
from containers import BeaconBlockHeader, SyncCommittee
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
  #           authenticate transactions and state against the header (I want to learn about how this happens)
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
  snapshot_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/snapshot/0x6b1a3fd7565d41ae1860d976e836842c71f9aee7aeada03ca1e4abf1dd789aef" 
  snapshot = callsAPI(snapshot_url)
  header_state_root = snapshot['data']['header']['state_root']
  list_of_keys = snapshot['data']['current_sync_committee']['pubkeys']
  hex_aggregate_pubkey = snapshot['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = snapshot['data']['current_sync_committee_branch']

  # ----------------------------------------
  # PARSE JSON INFORMATION FROM HEX TO BYTES
  # ----------------------------------------

  # #   CHECKPOINT-
  # finalized_checkpoint_root =  parseHexToByte(finalized_checkpoint_root)

  #   SYNC COMMITTEE- 
  #       Aggregate Key and Header State Root
  current_aggregate_pubkey = parseHexToByte(hex_aggregate_pubkey)
  header_state_root = parseHexToByte(header_state_root)
  
  #       List of Keys 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parseHexToByte(list_of_keys[i])
  
  #       Sync Committee Branch 
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parseHexToByte(current_sync_committee_branch[i])

  # ------------------
  # CREATE SSZ OBJECT
  # ------------------

  # SyncCommittee
  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )

  #--------------------------------------------
  # MERKLEIZE SYNC ROOT AND VERIFY MERKLE PROOF  
  #--------------------------------------------
  
  sync_committee_root = View.hash_tree_root(current_sync_committee) 
  # checkMerkleProof(sync_committee_root, finalized_checkpoint_root, current_sync_committee_branch)
  checkMerkleProof(sync_committee_root, header_state_root, current_sync_committee_branch)
  
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  # 
  #  Merkleize the sync committee object, then hash it against the merkle branch
  #  If the output matches the hash_tree_root(beacon block header)... Yaaaay 

  # -----------------------------------
  # MERKLEIZE THE SYNC COMMITTEE OBJECT
  # -----------------------------------

  # beacon_block_header_root = View.hash_tree_root(beacon_block_header) 
  sync_committee_root = View.hash_tree_root(current_sync_committee) 
  # This was too easy.  Do this myself!!!
  # merkleizeSyncCommittee(current_sync_committee)
  
  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------

  # Check proof function works, BUT the values still aren't matching up
  # Am I comparing this hashed value to the wrong hash_tree_root?
  # The answer isn't just to hash tree root the checkpoint container
  #
  # 2^5 == 32 <--- number of nodes in the merkle tree that proves hash_tree_root(BeaconState).   
  # This is the number of nodes needed to create a merkle tree for BeaconState 
  #
  # Compare hashed answer to the BEACON STATE ROOT that the sync committee is a part of!

  # checkMerkleProof(beacon_block_header_root, sync_committee_root, current_sync_committee_branch)
  # checkMerkleProof(sync_committee_root, finalized_checkpoint_root, current_sync_committee_branch)



  #                                     \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
  #                                      \\\\\\\\\\\\\\\\\\\   |   ////////////////////
  #                                      ==============================================
  #                                      GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
  #                                      ==============================================
  #                                      ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
  #                                     ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\




  #                                       \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                        \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                        ========================================
  #                                        SYNC TO THE LATEST FINALIZED CHECKPOINT:
  #                                        ========================================
  #                                        ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                       /////////////////// || \\\\\\\\\\\\\\\\\\\\