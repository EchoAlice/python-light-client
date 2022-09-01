from msilib.schema import Error
import pytest
from py_ecc.bls import G2ProofOfPossession as py_ecc_bls
from functions import View
from helper import ( compute_signing_root,
										 parse_hex_to_bit,
)
from containers import (BeaconBlockHeader,
)

# Command for testing:   python -m pytest .\src\test.py
# Tests translated from Clara's project:   snowbridge/parachain/pallets/ethereum-beacon-client/src/tests.rs    
# Figure out how to use Etan's tests and the vectors he gave me


# Tests organized in descending order of the verification stack.

# =============================
#  bls_fast_aggregate_verify()
# =============================
def test_bls_fast_aggregate_verify_minimal():
    assert py_ecc_bls.FastAggregateVerify([
			bytes.fromhex("a73eb991aa22cdb794da6fcde55a427f0a4df5a4a70de23a988b5e5fc8c4d844f66d990273267a54dd21579b7ba6a086"),
			bytes.fromhex("b29043a7273d0a2dbc2b747dcf6a5eccbd7ccb44b2d72e985537b117929bc3fd3a99001481327788ad040b4077c47c0d"),
			bytes.fromhex("b928f3beb93519eecf0145da903b40a4c97dca00b21f12ac0df3be9116ef2ef27b2ae6bcd4c5bc2d54ef5a70627efcb7"),
			bytes.fromhex("9446407bcd8e5efe9f2ac0efbfa9e07d136e68b03c5ebc5bde43db3b94773de8605c30419eb2596513707e4e7448bb50"),
		],
		bytes.fromhex("69241e7146cdcc5a5ddc9a60bab8f378c0271e548065a38bcc60624e1dbed97f"),
		bytes.fromhex("b204e9656cbeb79a9a8e397920fd8e60c5f5d9443f58d42186f773c6ade2bd263e2fe6dbdc47f148f871ed9a00b8ac8b17a40d65c8d02120c00dca77495888366b4ccc10f1c6daa02db6a7516555ca0665bca92a647b5f3a514fa083fdc53b6e")
		)


# ==============================
#  1. participant_pubkeys logic
# ==============================


# ===========================
#  1. compute_signing_root()
# ===========================
@pytest.fixture
def update_attested_header():
    attested_header = BeaconBlockHeader(
        slot = 3529537,
        proposer_index = 192549,
        parent_root = bytes.fromhex("1f8dc05ea427f78e84e2e2666e13c3befb7106fd1d40ef8a3f67cf615f3f2a4c"), 
        state_root = bytes.fromhex("0dfb492a83da711996d2d76b64604f9bca9dc08b6c13cf63b3be91742afe724b"),
        body_root =  bytes.fromhex("66fba38f7c8c2526f7ddfe09c1a54dd12ff93bdd4d0df6a0950e88e802228bfa")
    )
    return attested_header

@pytest.fixture
def domain():
    domain_bytes = bytes.fromhex("07000000afcaaba0efab1ca832a15152469bb09bb84641c405171dfa2d3fb45f") 
    return domain_bytes

def test_compute_signing_root(update_attested_header, domain):
    assert compute_signing_root(update_attested_header, domain) == bytes.fromhex("3ff6e9807da70b2f65cdd58ea1b25ed441a1d589025d2c4091182026d7af08fb") 


# =====================
#  2. compute_domain()
# =====================






# ===========================
#  3. compute_fork_version()
# ===========================





# =======================
#  3. parse_hex_to_bit()
# =======================

# What I sent Clara:
# '0xffffffffffffffffffffffffffffffffafffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
@pytest.fixture
def hexidecimal():
	hex_string = 'fff3ffff'
	hex_string_clara = 'ffffffffffffffffffffffffffffffffafffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' 
	return hex_string_clara

@pytest.fixture
def expected_value():
	string_bits = '11111111111100111111111111111111'
	string_bits_clara = '11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111101011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
	return string_bits_clara

def test_parse_hex_to_bit(hexidecimal, expected_value):
	assert parse_hex_to_bit(hexidecimal) == expected_value
