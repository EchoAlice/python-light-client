import pytest
from py_ecc.bls.ciphersuites import G2ProofOfPossession                   
from py_ecc.bls import G2ProofOfPossession as py_ecc_bls                       # I believe both of these work

# Command for testing:
#   python -m pytest .\src\test\crypto.py

@pytest.fixture
def participant_pubkeys():
    pubkeys = [
        bytes.fromhex("a73eb991aa22cdb794da6fcde55a427f0a4df5a4a70de23a988b5e5fc8c4d844f66d990273267a54dd21579b7ba6a086"),
        bytes.fromhex("b29043a7273d0a2dbc2b747dcf6a5eccbd7ccb44b2d72e985537b117929bc3fd3a99001481327788ad040b4077c47c0d"),
        bytes.fromhex("b928f3beb93519eecf0145da903b40a4c97dca00b21f12ac0df3be9116ef2ef27b2ae6bcd4c5bc2d54ef5a70627efcb7"),
        bytes.fromhex("9446407bcd8e5efe9f2ac0efbfa9e07d136e68b03c5ebc5bde43db3b94773de8605c30419eb2596513707e4e7448bb50"),
        ]
    return pubkeys 

@pytest.fixture
def signing_root():
    root = bytes.fromhex("69241e7146cdcc5a5ddc9a60bab8f378c0271e548065a38bcc60624e1dbed97f")
    return root 

@pytest.fixture
def sync_aggregate_sync_committee_signature():
    signature = bytes.fromhex("b204e9656cbeb79a9a8e397920fd8e60c5f5d9443f58d42186f773c6ade2bd263e2fe6dbdc47f148f871ed9a00b8ac8b17a40d65c8d02120c00dca77495888366b4ccc10f1c6daa02db6a7516555ca0665bca92a647b5f3a514fa083fdc53b6e")
    return signature


def test_bls_fast_aggregate_verify_minimal(participant_pubkeys, signing_root, sync_aggregate_sync_committee_signature):
    assert py_ecc_bls.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate_sync_committee_signature)


'''

From Clara (and friends') project:    
    snowbridge/parachain/pallets/ethereum-beacon-client/src/tests.rs


test_bls_fast_aggregate_verify_minimal() {
        assert_ok!(EthereumBeaconClient::bls_fast_aggregate_verify(
			vec![
				PublicKey(hex!("a73eb991aa22cdb794da6fcde55a427f0a4df5a4a70de23a988b5e5fc8c4d844f66d990273267a54dd21579b7ba6a086").into()),
				PublicKey(hex!("b29043a7273d0a2dbc2b747dcf6a5eccbd7ccb44b2d72e985537b117929bc3fd3a99001481327788ad040b4077c47c0d").into()),
				PublicKey(hex!("b928f3beb93519eecf0145da903b40a4c97dca00b21f12ac0df3be9116ef2ef27b2ae6bcd4c5bc2d54ef5a70627efcb7").into()),
				PublicKey(hex!("9446407bcd8e5efe9f2ac0efbfa9e07d136e68b03c5ebc5bde43db3b94773de8605c30419eb2596513707e4e7448bb50").into()),
			],
			hex!("69241e7146cdcc5a5ddc9a60bab8f378c0271e548065a38bcc60624e1dbed97f").into(),
			hex!("b204e9656cbeb79a9a8e397920fd8e60c5f5d9443f58d42186f773c6ade2bd263e2fe6dbdc47f148f871ed9a00b8ac8b17a40d65c8d02120c00dca77495888366b4ccc10f1c6daa02db6a7516555ca0665bca92a647b5f3a514fa083fdc53b6e").to_vec(),
		));
	});
	}
'''