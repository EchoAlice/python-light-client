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

def getBeaconBlockHeader():
  print("Get information needed for a block header")

if __name__ == "__main__":
  # If I want to make this light client for the cross chain bridge, the code will need to be written in Solidity.
  # Light client for cross chain bridge is ran as a smart contract on the destination chain!
  # 
  # Initialization:
  #
  # Place all information relating to initialization and syncronization in the LightClientStore data class.
  # This information needs to follow SSZ container specifications
  #
  #   Get block header at slot N in period X = N // 16384
  #   Ask node for current sync committee + proof of checkpoint root
  #   
  #   Node responds with:
  #     header- Block's header corresponding to the checkpoint root (What's the checkpoint root?)
  #     current sync committee- Public Keys and the aggregated pub keyof the current sync committee
  #     current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 
  #
  #   A word on Headers:
  #     The light client stores a header so it can ask for merkle breanches to 
  #     authenticate transactions and state against the header (I want to learn about how this happens)
  #
  #   A word on Sync committees: 
  #     The purpose of the sync committee is to allow light clients to keep track
  #     of the chain of beacon block headers. 
  #     
  #     Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
  #     allowing light clients to verify the sync committee with a Merkle branch from a 
  #     block header that they already know about, and use the public keys 
  #     in the sync committee to directly authenticate signatures of more recent blocks.


  # A first milestone for a light client implementation is to simply HAVE A LIGHT CLIENT THAT SIMPLY TRACKS THE LATEST STATE/BLOCK ROOT.

  # Summary of what light client needs to do 
  # block_header = getBeaconBlockHeader()
  # verifyBlockHeader(block_header, sync_committee, sync_committee_branch)
  # LightClientStore = syncLightClientTo(block_header)
  # if update_light_client() == true:
  #   updateLightClient(LightClientStore)


  # Gets finalized checkpoint root
  checkpoint_url = "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/states/finalized/finality_checkpoints"
  checkpoint = callsAPI(checkpoint_url)
  print(checkpoint['data']['finalized']) 
  checkpoint_root = checkpoint['data']['finalized']['root']  
  # Returns finality checkpoints for finalized state id
  print(checkpoint_root)
  print("\n") 

  # Place checkpoint root in block_header_url API call 
  # Returns specified block header
  specified_block_header_url = "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/headers/0x3cf0393a193a9a95568700946fba64cdca2fdadbb571f40f230e93e5c457032f" 
  specified_block_header = callsAPI(specified_block_header_url)
  print("Specified: ") 
  print(specified_block_header['data']['header']['message'])
  print("\n")
  print("Finalized: ")

  # I believe the finalized block header is the header I need to use to initialize the LC 
  # Returns finalized block header
  # The header is the key trusted piece of data we use to verify merkle proofs against.
  # From a beacon block, we can use merkle proofs to verify data about everything
  finalized_block_header_url = "https://api.allorigins.win/raw?url=http://testing.mainnet.beacon-api.nimbus.team/eth/v1/beacon/headers/finalized"
  finalized_block_header = callsAPI(finalized_block_header_url)
  print(finalized_block_header['data']['header']['message']) 
  
  # Figure out how to instantiate container with API message 
  # Do the message, or individual data types within the container need to be serialized?
    