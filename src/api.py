from containers import ( LightClientBootstrap,
                         LightClientFinalityUpdate,
                         LightClientOptimisticUpdate, 
                         LightClientUpdate, 
)
from helper import( call_api,
                    initialize_block_header,
                    initialize_sync_aggregate,
                    initialize_sync_committee,
                    parse_hex_to_byte,
                    parse_list,
)


# ======
#  URLs
# ======
checkpoint_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/finalized/finality_checkpoints"
bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/bootstrap/0x705db40cc768f3d3b515fa36fde616f7a934c22d40e08eb2e2fa7bdd59c086ff" 
current_finality_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/finality_update/" 
current_header_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/optimistic_update/" 

# Create conditional statements for api calls
checkpoint = call_api(checkpoint_url).json()
bootstrap = call_api(bootstrap_url).json()

finalized_checkpoint_root = checkpoint['data']['finalized']['root']    # Print to get the hex encoded bootstrap block root
trusted_block_root =  parse_hex_to_byte("0x705db40cc768f3d3b515fa36fde616f7a934c22d40e08eb2e2fa7bdd59c086ff")  # trusted_block_root == finalized_checkpoint_root
bootstrap_header_message = bootstrap['data']['header']
bootstrap_committee_message = bootstrap['data']['current_sync_committee']

#  =================================
#  CREATE BOOTSTRAP CONTAINER OBJECT
#  =================================
bootstrap_object = LightClientBootstrap(
  header= initialize_block_header(bootstrap_header_message),
  current_sync_committee= initialize_sync_committee(bootstrap_committee_message),
  current_sync_committee_branch=  parse_list(bootstrap['data']['current_sync_committee_branch'])
)

#  ================
#  UPDATE FUNCTIONS
#  ================ 
def instantiate_sync_period_data(update_message):
  # print("Sync aggregate message: "+str(update_message['data'][0]['sync_aggregate'])) 
  # sync_aggregate = initialize_sync_aggregate(update_message['data'][0]['sync_aggregate']),
  # print("Sync aggregate: "+str(sync_aggregate))
  return LightClientUpdate(
    attested_header = initialize_block_header(update_message['data'][0]['attested_header']),
    next_sync_committee = initialize_sync_committee(update_message['data'][0]['next_sync_committee']),
    next_sync_committee_branch = parse_list(update_message['data'][0]['next_sync_committee_branch']),
    finalized_header = initialize_block_header(update_message['data'][0]['finalized_header']),
    finality_branch = parse_list(update_message['data'][0]['finality_branch']),
    sync_aggregate = initialize_sync_aggregate(update_message['data'][0]['sync_aggregate']),
  )
    # sync aggregate - A record of which validators in the current sync committee voted for the chain head in the previous slot.               <---- This statement could be interpretted in different ways...
    # Contains the sync committee's bitfield and signature required for verifying the attested header.                                   @ben_eddington

def instantiate_finality_update_data(update_message):
  return LightClientFinalityUpdate (
    attested_header = initialize_block_header(update_message['data']['attested_header']),
    finalized_header = initialize_block_header(update_message['data']['finalized_header']),
    finality_branch = parse_list(update_message['data']['finality_branch']),
    sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate']),
  )

def instantiate_optimistic_update_data(update_message):
  return LightClientOptimisticUpdate (
    attested_header = initialize_block_header(update_message['data']['attested_header']), 
    sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate']), 
  )