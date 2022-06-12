import requests
from remerkleable.basic import bit, uint, uint8, uint64
from remerkleable.complex import List
from remerkleable.core import View
from containers import Checkpoint
from containers import SyncCommittee

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
  #                                      Initialization/Bootstrapping to a period:
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
  finalized_checkpoint_epoch = checkpoint['data']['finalized']['epoch']
  finalized_checkpoint_root = checkpoint['data']['finalized']['root']  

  # SNAPSHOT-
  snapshot_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/snapshot/0x354946e0e14432c9671317d826c10cc3b91d0690c4e8099dce1749f950cd63b3" 
  snapshot = callsAPI(snapshot_url)
  list_of_keys = snapshot['data']['current_sync_committee']['pubkeys']
  hex_aggregate_pubkey = snapshot['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = snapshot['data']['current_sync_committee_branch']

  # "When the pubkey is encoded to hex, every byte becomes two characters.  All data sent is
  # in json format, and the unofficial standard is to send binary data as 0x prefixed hex.
  # You'll need to parse keys back into byte arrays to do crypto on it"      <-- Do crypto on it???
  #                                       - Cayman
  # 

  # ----------------------------------------
  # PARSE JSON INFORMATION FROM HEX TO BYTES
  # ----------------------------------------

  #   CHECKPOINT-
  finalized_checkpoint_epoch = parseHexToByte(finalized_checkpoint_epoch) 
  finalized_checkpoint_root =  parseHexToByte(finalized_checkpoint_root)

  #   SYNC COMMITTEE- 
  #       List of Keys 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parseHexToByte(list_of_keys[i])
  
  #       Aggregate Key
  current_aggregate_pubkey = parseHexToByte(hex_aggregate_pubkey)

  #       Sync Committee Branch 
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parseHexToByte(current_sync_committee_branch[i])

  # ------------------
  # CREATE SSZ OBJECTS
  # ------------------
 
  # Checkpoint
  # Hold up- I might not need this object
  trusted_checkpoint = Checkpoint(
    epoch = finalized_checkpoint_epoch, 
    root = finalized_checkpoint_root 
  )
  
  # SyncCommittee
  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )
 
  

  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  #  Current_sync_committee_branch contains 5 nodes.  
  # 
  #  Merkleize the sync committee object, then hash it against the merkle branch
  #  If the output matches the checkpoint root... Yaaaay 

  # ------------------
  # MERKLEIZE THE SYNC COMMITTEE OBJECT
  # ------------------
  # This was too easy.  Do this myself!!!
  sync_committee_root = View.hash_tree_root(current_sync_committee) 
  print(sync_committee_root)

  # merkleizeSyncCommittee(current_sync_committee)
  
  
  
  # ------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # ------------------
  # checkMerkleProof(checkpoint_root, current_sync_committee, current_sync_committee_branch)
  
  
  
  # ------------------
  # CHECK VALIDITY
  # ------------------
  
