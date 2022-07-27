import json
import requests
from specfunctions import floorlog2
from containers import (Bytes32, 
                        Slot, 
                        NEXT_SYNC_COMMITTEE_INDEX, 
                        BeaconBlockHeader, 
                        LightClientFinalityUpdate,
                        LightClientOptimisticUpdate, 
                        LightClientUpdate, 
                        SyncAggregate, 
                        SyncCommittee)

def calls_api(url):
  response = requests.get(url)
  return response

def parse_hex_to_byte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def parse_hex_to_bit(hex_string):
  int_representation = int(hex_string, 16)
  binary_vector = bin(int_representation) 
  if binary_vector[:2] == '0b':
    binary_vector = binary_vector[2:]
  return binary_vector 

def parse_list(list):
  for i in range(len(list)):
    list[i] = parse_hex_to_byte(list[i])

def updates_for_period(sync_period):
  sync_period = str(sync_period) 
  updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/updates?start_period="+sync_period+"&count=1" 
  response = calls_api(updates_url)

  return response


def initializes_block_header(header_message):
  block_header = BeaconBlockHeader (
    slot =  int(header_message['slot']),
    proposer_index = int(header_message['proposer_index']),
    parent_root = parse_hex_to_byte(header_message['parent_root']),
    state_root = parse_hex_to_byte(header_message['state_root']),
    body_root = parse_hex_to_byte(header_message['body_root'])
  )
  return block_header

# For some reason, I can't parse the list of keys or the agg pub key within the sync committee object
def initializes_sync_committee(committee_message):
  list_of_keys = committee_message['pubkeys']
  aggregate_pubkey = committee_message['aggregate_pubkey']
  parse_list(list_of_keys)
  aggregate_pubkey = parse_hex_to_byte(aggregate_pubkey)
  
  sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = aggregate_pubkey
  )
  return sync_committee

# See if I can compress this... I run into errors when i try  :/  
def initializes_sync_aggregate(aggregate_message):
  sync_committee_hex = aggregate_message['sync_committee_bits']
  sync_committee_signature = aggregate_message['sync_committee_signature']
  sync_committee_bits = parse_hex_to_bit(sync_committee_hex) 
  sync_committee_signature = parse_hex_to_byte(sync_committee_signature)

  sync_aggregate = SyncAggregate(
    sync_committee_bits = sync_committee_bits, 
    sync_committee_signature = sync_committee_signature 
  )
  return sync_aggregate



#                                                \~~~~~~~~~~~~~~~~~~/
#                                                 \ ============== /
#                                                    THE BIG BOYS
#                                                 / ============== \
#                                                /~~~~~~~~~~~~~~~~~~\


def instantiates_sync_period_data(sync_period):
  sync_period_update = updates_for_period(sync_period).json()

  attested_block_header = initializes_block_header(sync_period_update['data'][0]['attested_header']) 
  next_sync_committee = initializes_sync_committee(sync_period_update['data'][0]['next_sync_committee'])
  finalized_block_header = initializes_block_header(sync_period_update['data'][0]['finalized_header']) 
  sync_aggregate = initializes_sync_aggregate(sync_period_update['data'][0]['sync_aggregate'])
 
  next_sync_committee_branch = sync_period_update['data'][0]['next_sync_committee_branch']
  parse_list(next_sync_committee_branch)
  
  finality_branch = sync_period_update['data'][0]['finality_branch']
  parse_list(finality_branch) 

  fork_version =  sync_period_update['data'][0]['fork_version']
  fork_version = parse_hex_to_byte(fork_version)

  light_client_update = LightClientUpdate(
    attested_header = attested_block_header,
    next_sync_committee = next_sync_committee,
    next_sync_committee_branch = next_sync_committee_branch,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    # A record of which validators in the current sync committee voted for the chain head in the previous slot.               <---- This statement could be interpretted in different ways...
    # Contains the sync committee's bitfield and signature required for verifying the attested header.                                   @ben_eddington
    #
    sync_aggregate = sync_aggregate,
    signature_slot =  attested_block_header.slot + 1                  # Slot at which the aggregate signature was created (untrusted)    
  )
  return light_client_update


def instantiates_finality_update_data(update_message):
  attested_block_header = initializes_block_header(update_message['data']['attested_header']) 
  finalized_block_header = initializes_block_header(update_message['data']['finalized_header']) 
  sync_aggregate = initializes_sync_aggregate(update_message['data']['sync_aggregate'])
  
  finality_branch = update_message['data']['finality_branch']
  parse_list(finality_branch) 

  light_client_finality_update = LightClientFinalityUpdate (
    attested_header = attested_block_header,
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    sync_aggregate = sync_aggregate,
    signature_slot =  attested_block_header.slot + 1     
  )
  return light_client_finality_update


def instantiates_optimistic_update_data(update_message):
  attested_block_header = initializes_block_header(update_message['data']['attested_header']) 
  attested_sync_aggregate = initializes_sync_aggregate(update_message['data']['sync_aggregate'])

  light_client_optimistic_update = LightClientOptimisticUpdate (
    attested_header = attested_block_header, 
    sync_aggregate = attested_sync_aggregate, 
    signature_slot = attested_block_header.slot + 1 
  )
  return light_client_optimistic_update
