import requests
import json

# from containers import BeaconBlockHeader
# from containers import LightClientUpdate
# from containers import LightClientStore
# from helperfunctions import is_finality_update
# from helperfunctions import get_subtree_index
# from helperfunctions import get_active_header
# from helperfunctions import get_safety_threshold

#  MVP Light Client:  Track latest state/block root
def callsAPI(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

if __name__ == "__main__":
  # Initialization:
  #
  # Place all initialization and sync info into the LightClientStore data class
  #
  # Ask node for current sync committee + proof of checkpoint root
  # Node responds with:
  #    header- Block's header corresponding to the checkpoint root (What's the checkpoint root?)
  #    current sync committee- Public Keys and the aggregated pub keyof the current sync committee
  #    current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 

  # Gets checkpoint root
  checkpoint_url = "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/states/head/finality_checkpoints" 
  checkpoint = callsAPI(checkpoint_url)
  checkpoint_root = checkpoint['data']['finalized']['root']  
  print(checkpoint_root) 

  # Place checkpoint root in block_header_url API call 
  block_header_url =  "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/headers"
  block_header = callsAPI(block_header_url)
  
  beacon_block_header_container = block_header['data'][0]['header']['message']
  # print(beacon_block_header_container)
  
  # Figure out how to instantiate container with API message 
  # Do the message, or individual data types within the container need to be serialized?
    
  # print(BeaconBlockHeader)