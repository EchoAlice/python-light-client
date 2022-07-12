from containers import (DOMAIN_SYNC_COMMITTEE,
                        EPOCHS_PER_SYNC_COMMITTEE_PERIOD,
                        FINALIZED_ROOT_INDEX,
                        GENESIS_FORK_VERSION, 
                        GENESIS_SLOT, 
                        MIN_SYNC_COMMITTEE_PARTICIPANTS, 
                        NEXT_SYNC_COMMITTEE_INDEX, 
                        SLOTS_PER_EPOCH,
                        UPDATE_TIMEOUT,
                        Bytes32,
                        Domain, 
                        DomainType, 
                        Root, 
                        Slot,
                        SSZObject, 
                        Version,
                        uint64,
                        BeaconBlockHeader,
                        ForkData,
                        LightClientStore, 
                        LightClientUpdate, 
                        SigningData, 
                        SyncCommittee)
from merkletreelogic import floorlog2, is_valid_merkle_branch
from py_ecc import bls
from remerkleable.core import View


genesis_validators_root = Root()                                         #  Is this correct?

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

def compute_fork_data_root(current_version: Version, genesis_validators_root: Root) -> Root:
    """
    Return the 32-byte fork data root for the ``current_version`` and ``genesis_validators_root``.
    This is used primarily in signature domains to avoid collisions across forks/chains.
    """
    return View.hash_tree_root(ForkData(
        current_version=current_version,
        genesis_validators_root=genesis_validators_root,
    ))

def compute_signing_root(ssz_object: SSZObject, domain: Domain) -> Root:
    """
    Return the signing root for the corresponding signing data.
    """
    return View.hash_tree_root(SigningData(
        object_root=View.hash_tree_root(ssz_object),
        domain=domain,
    ))

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

def get_safety_threshold(store: LightClientStore) -> uint64:
    return max(
        store.previous_max_active_participants,
        store.current_max_active_participants,
    ) // 2


#                               ==============
#                                THE BIG BOYS
#                               ==============

def process_slot_for_light_client_store(store: LightClientStore, current_slot: Slot) -> None:
    if current_slot % UPDATE_TIMEOUT == 0:
        store.previous_max_active_participants = store.current_max_active_participants
        store.current_max_active_participants = 0
    if (
        current_slot > store.finalized_header.slot + UPDATE_TIMEOUT
        and store.best_valid_update is not None
    ):
        # Forced best update when the update timeout has elapsed
        apply_light_client_update(store, store.best_valid_update)
        store.best_valid_update = None

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
    
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)
    signing_root = compute_signing_root(update.attested_header, domain)
    assert bls.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)
    print("Validation successful")

def apply_light_client_update(store: LightClientStore, update: LightClientUpdate) -> None:
    active_header = get_active_header(update)
    finalized_period = compute_sync_committee_period(compute_epoch_at_slot(store.finalized_header.slot))
    update_period = compute_sync_committee_period(compute_epoch_at_slot(active_header.slot))
    if update_period == finalized_period + 1:
        store.current_sync_committee = store.next_sync_committee
        store.next_sync_committee = update.next_sync_committee
    store.finalized_header = active_header
    if store.finalized_header.slot > store.optimistic_header.slot:
        store.optimistic_header = store.finalized_header

def process_light_client_update(store: LightClientStore,
                                update: LightClientUpdate,
                                current_slot: Slot,
                                genesis_validators_root: Root) -> None:
    validate_light_client_update(store, update, current_slot, genesis_validators_root)

    sync_committee_bits = update.sync_aggregate.sync_committee_bits

    # Update the best update in case we have to force-update to it if the timeout elapses
    if (
        store.best_valid_update is None
        or sum(sync_committee_bits) > sum(store.best_valid_update.sync_aggregate.sync_committee_bits)
    ):
        store.best_valid_update = update

    # Track the maximum number of active participants in the committee signatures
    store.current_max_active_participants = max(
        store.current_max_active_participants,
        sum(sync_committee_bits),
    )

    # Update the optimistic header
    if (
        sum(sync_committee_bits) > get_safety_threshold(store)
        and update.attested_header.slot > store.optimistic_header.slot
    ):
        store.optimistic_header = update.attested_header

    # Update finalized header
    if (
        sum(sync_committee_bits) * 3 >= len(sync_committee_bits) * 2
        and is_finality_update(update)
    ):
        # Normal update through 2/3 threshold
        apply_light_client_update(store, update)
        store.best_valid_update = None