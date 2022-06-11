import requests
from merkletreelogic import checkMerkleProof
from remerkleable.basic import bit, uint, uint8, uint64
from remerkleable.complex import List
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
  # Initialization/Bootstrapping to a period:
  #
  # Place all information relating to initialization and syncronization in the LightClientStore data class.
  # This information needs to follow SSZ container specifications
  #
  #   Get block header at slot N in period X = N // 16384
  #   Ask node for current sync committee + proof of checkpoint root
  #   
  #   Node responds with a snapshot --> A snapshot contains:
  #
  #   1. Header- Block's header corresponding to the checkpoint root
  #   
  #      A word on Headers:
  #         The light client stores a header so it can ask for merkle branches to 
  #         authenticate transactions and state against the header (I want to learn about how this happens)
  #
  #   2. Current sync committee- Public Keys and the aggregated pub key of the current sync committee
  #   
  #      A word on Sync committees: 
  #         The purpose of the sync committee is to allow light clients to keep track
  #         of the chain of beacon block headers. 
  #         Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
  #         allowing light clients to verify the sync committee with a Merkle branch from a 
  #         block header that they already know about, and use the public keys 
  #         in the sync committee to directly authenticate signatures of more recent blocks.
  #   
  #   3. Current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 



  # ===================================================================
  # STEP 1:  Gather most recent finality (weak subjectivity) checkpoint
  # ===================================================================
  

  checkpoint_url = "https://api.allorigins.win/raw?url=https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/head/finality_checkpoints" 
  checkpoint = callsAPI(checkpoint_url)
  checkpoint_root = checkpoint['data']['finalized']['root']  
  
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
  # Parses keys back into byte arrays 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parseHexToByte(list_of_keys[i])
  
  current_aggregate_pubkey = parseHexToByte(hex_aggregate_pubkey)

  # Creates SyncCommittee container
  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )
  # print(current_sync_committee)
  
  # Parses current_sync_committee_branch into byte arrays
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parseHexToByte(current_sync_committee_branch[i])
  print(current_sync_committee_branch[0])
  


  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================


  # We'll describe paths as lists, which can have two representations. In "human-readable form",
  # they are ["x"], ["y", "__len__"] and ["y", 5, "w"] respectively. In "encoded form", they are 
  #     lists of uint64 values (Bytes8) 

  #  Current_sync_committee_branch contains 5 nodes.  
  #  I have the nodes, now I need to find the leaf node to check and the root node I trust.
  #  How do you hash these bad boys? 
  #
  # What is the trusted root?  Where is the sync committee stored? <--- Is that question even relevant? 
  checkMerkleProof(checkpoint_root, given_root, current_sync_committee_branch)
  