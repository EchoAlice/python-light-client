import requests
import remerkleable.core

# from containers import BeaconBlockHeader

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
  #   Node responds with a snapshot
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

  # A first milestone for a light client implementation is to HAVE A LIGHT CLIENT THAT SIMPLY TRACKS THE LATEST STATE/BLOCK ROOT.

  # Summary of what light client needs to do: 
  # checkpoint_root = request(finality_checkpoint)
  # snapshot = request(snapshot(checkpoint_root))
  # verifyCurrentSyncCommitteeBranch(snapshot)
  # LightClientStore = syncLightClientTo(block_header)
  # if update_light_client() == true:
  #   updateLightClient(LightClientStore)

  # Step 1:  Gather most recent finality checkpoint (pretty much a weak subjectivity checkpoint)
  checkpoint_url = "https://api.allorigins.win/raw?url=https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/head/finality_checkpoints" 
  checkpoint = callsAPI(checkpoint_url)
  checkpoint_root = checkpoint['data']['finalized']['root']  
  print(checkpoint_root)

  # Call lightclient/snapshot with most recent checkpoint root to bootstrap to a period (How do you bootstrap to a period)
  # A snapshot contains:
  #     header- Block's header corresponding to the checkpoint root
  #     current sync committee- Public Keys and the aggregated pub keyof the current sync committee
  #     current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 
  
  snapshot_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/snapshot/0x354946e0e14432c9671317d826c10cc3b91d0690c4e8099dce1749f950cd63b3" 
  snapshot = callsAPI(snapshot_url) 
  print(snapshot) 
  list_of_keys = snapshot['data']['current_sync_committee']['pubkeys']
  
  # Figure out how to instantiate container with API message 
  # Do the message, or individual data types within the container need to be serialized?