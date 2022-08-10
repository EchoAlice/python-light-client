import json
import requests
import time
import pytest
from eth_utils import encode_hex
from containers import LightClientUpdate, SyncCommittee, Bytes32, NEXT_SYNC_COMMITTEE_INDEX
from specfunctions import floorlog2, compute_sync_committee_period_at_slot
from time import ctime
from mvplightclient import get_current_slot
from types import SimpleNamespace
from eth2spec.utils.hash_function import hash
from updatesapi import initialize_block_header, instantiate_sync_period_data, initialize_sync_committee, initialize_sync_aggregate
from remerkleable.core import View
from merkletreelogic import is_valid_merkle_branch, hash_pair, index_to_path
from containers import(uint64, 
                       MIN_GENESIS_TIME, 
                       BeaconBlockHeader, 
                       Root,
                       SECONDS_PER_SLOT,
                       SLOTS_PER_EPOCH, 
                       LightClientOptimisticUpdate,
)
from helper import (call_api,
                    get_current_epoch,
                    parse_hex_to_byte,
                    parse_list,
                    updates_for_period, 
)

from py_ecc.bls import G2ProofOfPossession                   # <----- This doesn't exist
from py_ecc.optimized_bls12_381 import (
    G1,
    Z1,
    Z2,
    multiply,
)
from py_ecc.bls.g2_primatives import(
    G1_to_pubkey,
    G2_to_signature,
)

def get_sync_period(slot_number):
  sync_period = slot_number // 8192
  return sync_period

def get_subtree_index(generalized_index: int) -> int:
  return int(generalized_index % 2**5) 

#  TO DO:
#
#     Create helper functions file (for small tings)
#     Figure out why I came to the conclusion that the test in scratch is bunk
#     Merge bootstrapapi with updateapi




# =============================================
# Functions testing for next_sync_committee bug
# =============================================

#                                                         \\\\\\\\////////
#                                                          ==============
#                                                             TEST ZONE  
#                                                          ==============
#                                                         ////////\\\\\\\\

"""
fork_version = compute_fork_version(compute_epoch_at_slot(update.signature_slot))            
domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)        
signing_root = compute_signing_root(update.attested_header, domain)

assert G2ProofOfPossession.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)       # spec uses bls.FastAggregateVerify()
"""

# THE TEST IS BUNK!  G2PROOFOFPOSSESSION DOESNT EXIST!

# @pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 42)])
# def test_eval(test_input, expected):
#     assert eval(test_input) == expected

sample_message = b'\x12' * 32

Z1_PUBKEY = G1_to_pubkey(Z1)
Z2_SIGNATURE = G2_to_signature(Z2)

# assert G2ProofOfPossession.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)

def compute_aggregate_signature(SKs, message):
    PKs = [G2ProofOfPossession.SkToPk(sk) for sk in SKs]
    signatures = [G2ProofOfPossession.Sign(sk, message) for sk in SKs]
    aggregate_signature = G2ProofOfPossession.Aggregate(signatures)
    return (PKs, aggregate_signature)

@pytest.mark.parametrize(
    'PKs, aggregate_signature, message, result',
    [
        (*compute_aggregate_signature(SKs=[1], message=sample_message), sample_message, True),
        (*compute_aggregate_signature(SKs=tuple(range(1, 5)), message=sample_message), sample_message, True),
        ([], Z2_SIGNATURE, sample_message, False),
        ([G2ProofOfPossession.SkToPk(1), Z1_PUBKEY], G2ProofOfPossession.Sign(1, sample_message), sample_message, False),
    ]
)

def test_fast_aggregate_verify(PKs, aggregate_signature, message, result):
    assert G2ProofOfPossession.FastAggregateVerify(PKs, message, aggregate_signature) == result




# python -m pytest .\light_client\scratch.py

# ^  This is the command to run in the terminal for testing.
#
#    It looks like FastAggregateVerify() works. Something must 
#    be wrong with my data in the spec  










# What I know about attested_header but:
#    - The attested header is 75 slots ahead of finalized header. 
#    - They're within the same sync period
#    - The data is organized properly
#    - 
#    
#
#  Maybe this isn't a bug at all? Before the new updated spec, 
#  the finalized header was the header being checked
