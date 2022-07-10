from constants import EPOCHS_PER_SYNC_COMMITTEE_PERIOD,FINALIZED_ROOT_INDEX, GENESIS_SLOT, MIN_SYNC_COMMITTEE_PARTICIPANTS, NEXT_SYNC_COMMITTEE_INDEX, SLOTS_PER_EPOCH
from containers import  Bytes32, Root, Slot, Version, BeaconBlockHeader, LightClientStore, LightClientUpdate, SyncCommittee
from merkletreelogic import floorlog2, is_valid_merkle_branch
from remerkleable.core import View

def compute_epoch_at_slot(slot_number):
  epoch = slot_number // SLOTS_PER_EPOCH 
  return epoch

def compute_domain(domain_type: DomainType, fork_version: Version=None, genesis_validators_root: Root=None) -> Domain:
    """
    Return the domain for the ``domain_type`` and ``fork_version``.
    """
    if fork_version is None:
        fork_version = GENESIS_FORK_VERSION
    if genesis_validators_root is None:
        genesis_validators_root = Root()  # all bytes zero by default
    fork_data_root = compute_fork_data_root(fork_version, genesis_validators_root)
    return Domain(domain_type + fork_data_root[:28])

def compute_sync_committee_period(epoch_number):
  sync_period = epoch_number // EPOCHS_PER_SYNC_COMMITTEE_PERIOD
  return sync_period

def is_finality_update(update: LightClientUpdate) -> bool:
    return update.finality_branch != [Bytes32() for _ in range(floorlog2(FINALIZED_ROOT_INDEX))]

def is_sync_committee_update(update: LightClientUpdate) -> bool:
    return update.next_sync_committee_branch != [Bytes32() for _ in range(floorlog2(NEXT_SYNC_COMMITTEE_INDEX))]

def get_active_header(update: LightClientUpdate) -> BeaconBlockHeader:
    # The "active header" is the header that the update is trying to convince us
    # to accept. If a finalized header is present, it's the finalized header,
    # otherwise it's the attested header
    if is_finality_update(update):
        return update.finalized_header
    else:
        return update.attested_header



#                               ==============
#                                THE BIG BOYS
#                               ==============

def validate_light_client_update(store: LightClientStore,
                                 update: LightClientUpdate,
                                #  current_slot: Slot,
                                #  genesis_validators_root: Root
                                fork_version: Version
                                 ) -> None:
    # Verify update slot is larger than slot of current best finalized header
    active_header = get_active_header(update)
    
    # THIS IS THE REAL ONE 
    # assert current_slot >= update.signature_slot > active_header.slot > store.finalized_header.slot
    
    # TEST ZONE!
    assert  update.signature_slot > active_header.slot > store.finalized_header.slot


    # Verify update does not skip a sync committee period
    finalized_period = compute_sync_committee_period(compute_epoch_at_slot(store.finalized_header.slot))
    update_period = compute_sync_committee_period(compute_epoch_at_slot(active_header.slot))
    signature_period = compute_sync_committee_period(compute_epoch_at_slot(update.signature_slot))
    assert signature_period in (finalized_period, finalized_period + 1)

    # Verify that the `finality_branch`, if present, confirms `finalized_header`
    # to match the finalized checkpoint root saved in the state of `attested_header`.
    # Note that the genesis finalized checkpoint root is represented as a zero hash.
    if not is_finality_update(update):
        assert update.finalized_header == BeaconBlockHeader()
    else:
        if update.finalized_header.slot == GENESIS_SLOT:
            finalized_root = Bytes32()
            assert update.finalized_header == BeaconBlockHeader()
        else:
            finalized_root = View.hash_tree_root(update.finalized_header)
        assert is_valid_merkle_branch(
            leaf=finalized_root,
            branch=update.finality_branch,
            # depth=floorlog2(FINALIZED_ROOT_INDEX),
            index=FINALIZED_ROOT_INDEX,                       # index=get_subtree_index(FINALIZED_ROOT_INDEX),        <--- Ethereum's version of this parameter         
            root=update.attested_header.state_root,
        )

    # Verify that the `next_sync_committee`, if present, actually is the next sync committee saved in the
    # state of the `active_header`
    if not is_sync_committee_update(update):
        assert update_period == finalized_period
        assert update.next_sync_committee == SyncCommittee()
    else:
        if update_period == finalized_period:
            assert update.next_sync_committee == store.next_sync_committee
        assert is_valid_merkle_branch(
            leaf=View.hash_tree_root(update.next_sync_committee),
            branch=update.next_sync_committee_branch,
            # depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX),
            index=NEXT_SYNC_COMMITTEE_INDEX,
            root=active_header.state_root,
        )

    sync_aggregate = update.sync_aggregate

    # Verify sync committee has sufficient participants
    assert sum(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS
    
    # Verify sync committee aggregate signature
    if signature_period == finalized_period:
        sync_committee = store.current_sync_committee
    else:
        sync_committee = store.next_sync_committee
    participant_pubkeys = [                                                                                   
        pubkey for (bit, pubkey) in zip(sync_aggregate.sync_committee_bits, sync_committee.pubkeys)
        if bit
    ]
    # fork_version = compute_fork_version(compute_epoch_at_slot(update.signature_slot))            # What if I just use the fork version given to me in the update api?
    print(fork_version) 
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)
    # signing_root = compute_signing_root(update.attested_header, domain)
    # assert bls.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)