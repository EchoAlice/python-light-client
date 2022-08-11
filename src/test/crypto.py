import pytest
from py_ecc.bls.ciphersuites import G2ProofOfPossession                   
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

# @pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 42)])
# def test_eval(test_input, expected):
#     assert eval(test_input) == expected

sample_message = b'\x12' * 32

Z1_PUBKEY = G1_to_pubkey(Z1)
Z2_SIGNATURE = G2_to_signature(Z2)

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