from turtle import update
from containers import (BeaconBlockHeader,
                        LightClientBootstrap,
                        LightClientFinalityUpdate,
                        LightClientOptimisticUpdate, 
                        LightClientUpdate, 
                        SyncAggregate, 
                        SyncCommittee,)
from helper import(call_api,
                   parse_hex_to_byte,
                   parse_hex_to_bit,
                   parse_list,
                   updates_for_period,
)

# Should the return objects be written like this? 
#   light_client_update = LightClientUpdate(...)
#   return light_client_update
def initialize_block_header(header_message):
  return BeaconBlockHeader (
    slot =  int(header_message['slot']),
    proposer_index = int(header_message['proposer_index']),
    parent_root = parse_hex_to_byte(header_message['parent_root']),
    state_root = parse_hex_to_byte(header_message['state_root']),
    body_root = parse_hex_to_byte(header_message['body_root'])
  )

def initialize_sync_aggregate(aggregate_message):
  return SyncAggregate(
    sync_committee_bits = parse_hex_to_bit(aggregate_message['sync_committee_bits']), 
    sync_committee_signature = parse_hex_to_byte(aggregate_message['sync_committee_signature'])
  )

def initialize_sync_committee(committee_message):
  return SyncCommittee(
    pubkeys = parse_list(committee_message['pubkeys']),
    aggregate_pubkey = parse_hex_to_byte(committee_message['aggregate_pubkey'])
  )


#  =================================
#  CREATE BOOTSTRAP CONTAINER OBJECT
#  =================================
checkpoint_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/finalized/finality_checkpoints"
bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/bootstrap/0xd475339cea53c7718fd422d6583e4c1700d7492f94b5b83cf871899b2701846b" 
trusted_block_root =  parse_hex_to_byte("0xd475339cea53c7718fd422d6583e4c1700d7492f94b5b83cf871899b2701846b")

checkpoint = call_api(checkpoint_url).json()
bootstrap = call_api(bootstrap_url).json()

# Print finalized_checkpoint_root to get the hex encoded bootstrap block root
finalized_checkpoint_root = checkpoint['data']['finalized']['root']  
bootstrap_header_message = bootstrap['data']['header']
bootstrap_committee_message = bootstrap['data']['current_sync_committee']

bootstrap_object = LightClientBootstrap(
  header= initialize_block_header(bootstrap_header_message),
  current_sync_committee= initialize_sync_committee(bootstrap_committee_message),
  current_sync_committee_branch=  parse_list(bootstrap['data']['current_sync_committee_branch'])
)

#  ================
#  UPDATE FUNCTIONS
#  ================ 

def instantiate_sync_period_data(update_message):
  # What should I do with attested_block_header? I currently need to define this outside of the object because of signature_slot
  attested_block_header = initialize_block_header(update_message['data'][0]['attested_header']) 
  
  return LightClientUpdate(
    attested_header = initialize_block_header(update_message['data'][0]['attested_header']),
    next_sync_committee = initialize_sync_committee(update_message['data'][0]['next_sync_committee']),
    next_sync_committee_branch = parse_list(update_message['data'][0]['next_sync_committee_branch']),
    finalized_header = initialize_block_header(update_message['data'][0]['finalized_header']),
    finality_branch = parse_list(update_message['data'][0]['finality_branch']),
    # A record of which validators in the current sync committee voted for the chain head in the previous slot.               <---- This statement could be interpretted in different ways...
    # Contains the sync committee's bitfield and signature required for verifying the attested header.                                   @ben_eddington
    #
    sync_aggregate = initialize_sync_aggregate(update_message['data'][0]['sync_aggregate']),
    signature_slot =  attested_block_header.slot + 1     # Slot at which the aggregate signature was created (untrusted)    
  )
  # fork_version =  parse_hex_to_byte(sync_period_update['data'][0]['fork_version'])

def instantiate_finality_update_data(update_message):
  attested_block_header = initialize_block_header(update_message['data']['attested_header']) 
  return LightClientFinalityUpdate (
    attested_header = initialize_block_header(update_message['data']['attested_header']),
    finalized_header = initialize_block_header(update_message['data']['finalized_header']),
    finality_branch = parse_list(update_message['data']['finality_branch']),
    sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate']),
    signature_slot =  attested_block_header.slot + 1     
  )

def instantiate_optimistic_update_data(update_message):
  attested_block_header = initialize_block_header(update_message['data']['attested_header']) 
  return LightClientOptimisticUpdate (
    attested_header = initialize_block_header(update_message['data']['attested_header']), 
    sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate']), 
    signature_slot = attested_block_header.slot + 1 
  )