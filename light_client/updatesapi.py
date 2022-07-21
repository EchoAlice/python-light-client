import json
import requests
from containers import Bytes32, NEXT_SYNC_COMMITTEE_INDEX, BeaconBlockHeader, LightClientUpdate,SyncAggregate, SyncCommittee
from specfunctions import floorlog2

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

#
#  The api bodies from "/light_client/updates?____" and "light_client/finality_update" 
#  are slightly different from one another.  This means I have to create a seperate function
#  to initialize finality_update data    :P 
#
#         "/light_client/updates?____"                                            "/light_client/finality_update"
#
#  update_message['data'][0]['attested_header']                               update_message['data']['attested_header']
#
#
# (The [0] is used to refer to which sync period you want)
# Maybe change up the sync to current period to utilize this index


def instantiates_sync_period_data(sync_period):
  sync_period_update = updates_for_period(sync_period).json()
  
  attested_header_message = sync_period_update['data'][0]['attested_header']
  attested_block_header = initializes_block_header(attested_header_message) 

  next_sync_committee_message = sync_period_update['data'][0]['next_sync_committee']
  next_sync_committee = initializes_sync_committee(next_sync_committee_message)
  next_sync_committee_branch = sync_period_update['data'][0]['next_sync_committee_branch']
  parse_list(next_sync_committee_branch)

  finalized_header_message =  sync_period_update['data'][0]['finalized_header']
  finalized_block_header = initializes_block_header(finalized_header_message) 
  finality_branch = sync_period_update['data'][0]['finality_branch']
  parse_list(finality_branch) 

  sync_aggregate_message = sync_period_update['data'][0]['sync_aggregate']
  sync_aggregate = initializes_sync_aggregate(sync_aggregate_message)

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
  attested_header_message = update_message['data']['attested_header']
  attested_block_header = initializes_block_header(attested_header_message) 

  finalized_header_message =  update_message['data']['finalized_header']
  finalized_block_header = initializes_block_header(finalized_header_message) 
  finality_branch = update_message['data']['finality_branch']
  parse_list(finality_branch) 

  sync_aggregate_message = update_message['data']['sync_aggregate']
  sync_aggregate = initializes_sync_aggregate(sync_aggregate_message)


  light_client_finality_update = LightClientUpdate (
    attested_header = attested_block_header,
    next_sync_committee = SyncCommittee(),                
    next_sync_committee_branch = [Bytes32() for _ in range(floorlog2(NEXT_SYNC_COMMITTEE_INDEX))],     # is there a better way to write "empty branch"? Less specific like, "null"
    finalized_header = finalized_block_header,
    finality_branch = finality_branch,
    sync_aggregate = sync_aggregate,
    signature_slot =  attested_block_header.slot + 1     
  )

  return light_client_finality_update