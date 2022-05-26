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

def getsCurrentBlockHeader(url):
  return callsAPI(url)

if __name__ == "__main__":
  # Initialization:
  block_header_url =  "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/headers"
  block_header = getsCurrentBlockHeader(block_header_url)
  beacon_block_header_container = block_header['data'][0]['header']['message']
  print(beacon_block_header_container) 
  
  # Figure out how to instantiate container with API message 
  # Do the message, or individual data types within the container need to be serialized?
    
  # print(BeaconBlockHeader)