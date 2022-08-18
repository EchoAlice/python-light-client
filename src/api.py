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
  sync_committee_bits = parse_hex_to_bit(aggregate_message['sync_committee_bits'])
  sync_committee_signature = parse_hex_to_byte(aggregate_message['sync_committee_signature'])

  sync_aggregate = SyncAggregate(
    sync_committee_bits = sync_committee_bits, 
    sync_committee_signature = sync_committee_signature 
  )
  return sync_aggregate

def initialize_sync_committee(committee_message):
  list_of_keys = parse_list(committee_message['pubkeys'])
  aggregate_pubkey = parse_hex_to_byte(committee_message['aggregate_pubkey'])
  
  sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = aggregate_pubkey
  )
  return sync_committee


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
bootstrap_sync_committee_branch = parse_list(bootstrap['data']['current_sync_committee_branch'])

bootstrap_block_header = initialize_block_header(bootstrap_header_message)
bootstrap_sync_committee = initialize_sync_committee(bootstrap_committee_message)

bootstrap_object = LightClientBootstrap(
  header= bootstrap_block_header,
  current_sync_committee= bootstrap_sync_committee,
  current_sync_committee_branch= bootstrap_sync_committee_branch
)

#  ================
#  UPDATE FUNCTIONS
#  ================ 

def instantiate_sync_period_data(sync_period):
  sync_period_update = updates_for_period(sync_period).json()
  
  attested_block_header = initialize_block_header(sync_period_update['data'][0]['attested_header']) 
  next_sync_committee = initialize_sync_committee(sync_period_update['data'][0]['next_sync_committee'])
  next_sync_committee_branch = parse_list(sync_period_update['data'][0]['next_sync_committee_branch'])
  finalized_block_header = initialize_block_header(sync_period_update['data'][0]['finalized_header']) 
  finality_branch = parse_list(sync_period_update['data'][0]['finality_branch'])
  sync_aggregate = initialize_sync_aggregate(sync_period_update['data'][0]['sync_aggregate'])
  fork_version =  parse_hex_to_byte(sync_period_update['data'][0]['fork_version'])

  return LightClientUpdate(
    attested_header = attested_block_header,
    next_sync_committee = next_sync_committee,
    next_sync_committee_branch = next_sync_committee_branch,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    # A record of which validators in the current sync committee voted for the chain head in the previous slot.               <---- This statement could be interpretted in different ways...
    # Contains the sync committee's bitfield and signature required for verifying the attested header.                                   @ben_eddington
    #
    sync_aggregate = sync_aggregate,
    signature_slot =  attested_block_header.slot + 1     # Slot at which the aggregate signature was created (untrusted)    
  )

def instantiate_finality_update_data(update_message):
  attested_block_header = initialize_block_header(update_message['data']['attested_header']) 
  finalized_block_header = initialize_block_header(update_message['data']['finalized_header']) 
  sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate'])
  finality_branch = parse_list(update_message['data']['finality_branch'])

  return LightClientFinalityUpdate (
    attested_header = attested_block_header,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    sync_aggregate = sync_aggregate,
    signature_slot =  attested_block_header.slot + 1     
  )

def instantiate_optimistic_update_data(update_message):
  attested_block_header = initialize_block_header(update_message['data']['attested_header']) 
  attested_sync_aggregate = initialize_sync_aggregate(update_message['data']['sync_aggregate'])

  return LightClientOptimisticUpdate (
    attested_header = attested_block_header, 
    sync_aggregate = attested_sync_aggregate, 
    signature_slot = attested_block_header.slot + 1 
  )