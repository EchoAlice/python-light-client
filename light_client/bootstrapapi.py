import json
import requests
from containers import BeaconBlockHeader, LightClientBootstrap, SyncCommittee

def calls_api(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

def parse_hex_to_byte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def parse_list(list):
  for i in range(len(list)):
    list[i] = parse_hex_to_byte(list[i])



#                                 =================================
#                                 CREATE BOOTSTRAP CONTAINER OBJECT
#                                 =================================

checkpoint_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/finalized/finality_checkpoints"
checkpoint = calls_api(checkpoint_url)
finalized_checkpoint_root = checkpoint['data']['finalized']['root']  

trusted_block_root =  parse_hex_to_byte("0x64f23b5e736a96299d25dc1c1f271b0ce4d666fd9a43f7a0227d16b9d6aed038")

bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/bootstrap/0x64f23b5e736a96299d25dc1c1f271b0ce4d666fd9a43f7a0227d16b9d6aed038" 
bootstrap = calls_api(bootstrap_url)

bootstrap_header = bootstrap['data']['header']

bootstrap_block_header = BeaconBlockHeader (
  slot = int(bootstrap_header['slot']),
  proposer_index = int(bootstrap_header['proposer_index']),
  parent_root = parse_hex_to_byte(bootstrap_header['parent_root']),
  state_root = parse_hex_to_byte(bootstrap_header['state_root']),
  body_root = parse_hex_to_byte(bootstrap_header['body_root']),
)

bootstrap_sync_committee = bootstrap['data']['current_sync_committee']['pubkeys']
bootstrap_sync_committee_branch = bootstrap['data']['current_sync_committee_branch']
parse_list(bootstrap_sync_committee) 
parse_list(bootstrap_sync_committee_branch) 
bootstrap_aggregate_pubkey = bootstrap['data']['current_sync_committee']['aggregate_pubkey']
bootstrap_aggregate_pubkey = parse_hex_to_byte(bootstrap_aggregate_pubkey)

bootstrap_sync_committee = SyncCommittee(
  pubkeys = bootstrap_sync_committee,
  aggregate_pubkey = bootstrap_aggregate_pubkey
)


bootstrap_object = LightClientBootstrap(
  header= bootstrap_block_header,
  current_sync_committee= bootstrap_sync_committee,
  current_sync_committee_branch= bootstrap_sync_committee_branch
)