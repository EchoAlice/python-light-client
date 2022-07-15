from containers import (CURRENT_SYNC_COMMITTEE_INDEX,
                        DOMAIN_SYNC_COMMITTEE,
                        EPOCHS_PER_SYNC_COMMITTEE_PERIOD,
                        FINALIZED_ROOT_INDEX,
                        GENESIS_FORK_VERSION, 
                        GENESIS_SLOT, 
                        MIN_SYNC_COMMITTEE_PARTICIPANTS, 
                        NEXT_SYNC_COMMITTEE_INDEX, 
                        SLOTS_PER_EPOCH,
                        SLOTS_PER_SYNC_PERIOD,
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
                        LightClientBootstrap,
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

def compute_sync_committee_period_at_slot(slot_number):
  sync_period = slot_number // SLOTS_PER_SYNC_PERIOD 
  return sync_period

def is_finality_update(update: LightClientUpdate) -> bool:
    return update.finality_branch != [Bytes32() for _ in range(floorlog2(FINALIZED_ROOT_INDEX))]

def is_better_update(new_update: LightClientUpdate, old_update: LightClientUpdate) -> bool:
    # Compare supermajority (> 2/3) sync committee participation
    max_active_participants = len(new_update.sync_aggregate.sync_committee_bits)
    new_num_active_participants = sum(new_update.sync_aggregate.sync_committee_bits)
    old_num_active_participants = sum(old_update.sync_aggregate.sync_committee_bits)
    new_has_supermajority = new_num_active_participants * 3 >= max_active_participants * 2
    old_has_supermajority = old_num_active_participants * 3 >= max_active_participants * 2
    if new_has_supermajority != old_has_supermajority:
        return new_has_supermajority > old_has_supermajority
    if not new_has_supermajority and new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # Compare indication of any finality
    new_has_finality = is_finality_update(new_update)
    old_has_finality = is_finality_update(old_update)
    if new_has_finality != old_has_finality:
        return new_has_finality

    # Compare sync committee finality
    if new_has_finality:
        new_has_sync_committee_finality = (
            compute_sync_committee_period_at_slot(new_update.finalized_header.slot)
            == compute_sync_committee_period_at_slot(new_update.attested_header.slot)
        )
        old_has_sync_committee_finality = (
            compute_sync_committee_period_at_slot(old_update.finalized_header.slot)
            == compute_sync_committee_period_at_slot(old_update.attested_header.slot)
        )
        if new_has_sync_committee_finality != old_has_sync_committee_finality:
            return new_has_sync_committee_finality

    # Tiebreaker 1: Sync committee participation beyond supermajority
    if new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # Tiebreaker 2: Prefer older data (fewer changes to best)
    if new_update.attested_header.slot != old_update.attested_header.slot:
        return new_update.attested_header.slot < old_update.attested_header.slot
    return new_update.signature_slot < old_update.signature_slot

def is_sync_committee_update(update: LightClientUpdate) -> bool:
    # If the next sync committee branch is not null
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

#                                           \~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
#                                            \ =========================== /
#                                              Light Client Initialization
#                                            / =========================== \
#                                           /~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\

def initialize_light_client_store(trusted_block_root: Root,
                                  bootstrap: LightClientBootstrap) -> LightClientStore:
    assert View.hash_tree_root(bootstrap.header) == trusted_block_root

    assert is_valid_merkle_branch(
        leaf=View.hash_tree_root(bootstrap.current_sync_committee),
        branch=bootstrap.current_sync_committee_branch,
        # depth=floorlog2(CURRENT_SYNC_COMMITTEE_INDEX),
        index=CURRENT_SYNC_COMMITTEE_INDEX,
        root=bootstrap.header.state_root,
    )

    return LightClientStore(
        finalized_header=bootstrap.header,
        current_sync_committee=bootstrap.current_sync_committee,
        next_sync_committee=SyncCommittee(),
        best_valid_update=None,
        optimistic_header=bootstrap.header,
        previous_max_active_participants=0,
        current_max_active_participants=0,
    )


#                                           \~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
#                                            \ ========================== /
#                                              Light Client State Updates
#                                            / ========================== \
#                                           /~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\

def process_slot_for_light_client_store(store: LightClientStore, current_slot: Slot) -> None:
    # This indicates a shift from one sync period to the next 
    if current_slot % UPDATE_TIMEOUT == 0:
        store.previous_max_active_participants = store.current_max_active_participants
        store.current_max_active_participants = 0
    #  if the current slot is past the next finalized header AND the store has a best valid update
    if (
        current_slot > store.finalized_header.slot + UPDATE_TIMEOUT                               
        and store.best_valid_update is not None
    ):
        # Forced best update when the update timeout has elapsed.
        # Because the apply logic waits for `finalized_header.slot` to indicate sync committee finality,
        # the `attested_header` may be treated as `finalized_header` in extended periods of non-finality
        # to guarantee progression into later sync committee periods according to `is_better_update`.
        if store.best_valid_update.finalized_header.slot <= store.finalized_header.slot:
            store.best_valid_update.finalized_header = store.best_valid_update.attested_header
        apply_light_client_update(store, store.best_valid_update)
        store.best_valid_update = None


def validate_light_client_update(store: LightClientStore,
                                 update: LightClientUpdate,
                                 current_slot: Slot,
                                 genesis_validators_root: Root,
                                 fork_version: Version                # I added in fork version because idk how to calculate it
                                 ) -> None:
    
    print("Store's finalized_header: ")
    print("Slot: " + str(store.finalized_header.slot))
    print("Sync period: " + str(compute_sync_committee_period_at_slot(store.finalized_header.slot)))
    print('\n') 
    print("Update's finalized_header: ")
    print("Slot: " + str(update.finalized_header.slot))
    print("Sync period: " + str(compute_sync_committee_period_at_slot(update.finalized_header.slot)))
    print('\n') 
    print("Update's attested_header: ")
    print("Slot: " + str(update.attested_header.slot))
    print("Sync period: " + str(compute_sync_committee_period_at_slot(update.attested_header.slot)))
    print('\n') 

    # All differences are multiples of 32 --> which means that all finalized headers in question are at the beginning of an epoch.  Epic 
    print("Diff btwn store.finalized_header.slot and update.finalized_header.slot: " + str(update.finalized_header.slot - store.finalized_header.slot )) 
    print("Diff btwn update.attested_header.slot and update.finalized_header.slot: " + str(update.attested_header.slot - update.finalized_header.slot )) 
    print('\n') 
    
    print("current_slot: " + str(current_slot)) 
    print("update.signature_slot: " + str(update.signature_slot)) 
    print("update.attested_header.slot: " + str(update.attested_header.slot)) 
    print("update.finalized_header.slot: " + str(update.finalized_header.slot)) 
    
    
    # Verify sync committee has sufficient participants
    sync_aggregate = update.sync_aggregate
    assert sum(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS

    # Verify update does not skip a sync committee period
    assert current_slot >= update.signature_slot > update.attested_header.slot >= update.finalized_header.slot 
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.slot)
    update_signature_period = compute_sync_committee_period_at_slot(update.signature_slot)
    assert update_signature_period in (store_period, store_period + 1)

    # Verify update is relevant
    update_attested_period = compute_sync_committee_period_at_slot(update.attested_header.slot)
    assert update.attested_header.slot > store.finalized_header.slot

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
    # state of the `attested_header`
    if not is_sync_committee_update(update):
        assert update_attested_period == store_period
        assert update.next_sync_committee == SyncCommittee()
    else:
        if update_attested_period == store_period:
            assert update.next_sync_committee == store.next_sync_committee
        assert is_valid_merkle_branch(
            leaf=View.hash_tree_root(update.next_sync_committee),
            branch=update.next_sync_committee_branch,
            # depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX),
            index=NEXT_SYNC_COMMITTEE_INDEX,
            root=update.attested_header.state_root,                    # spec said "attested_header.state_root"                      
        )

    # My branch works for verifying the next sync committee against the finalized header, but not against
    # the attested header.  They should have the same next sync committee though because they're in the
    # same sync period.
    # 
    # "The next_sync_committee can no longer be considered finalized based
    # on is_finality_update. Instead, waiting until finalized_header is
    # in the attested_header's sync committee period is now necessary."  - Etan-Status PR #2932  
    #  
    print('Both proofs work')
    
    # Verify sync committee aggregate signature
    if update_signature_period == store_period:
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
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.slot)
    update_finalized_period = compute_sync_committee_period_at_slot(update.finalized_header.slot)
    if update_finalized_period == store_period + 1:
        store.current_sync_committee = store.next_sync_committee
        store.next_sync_committee = update.next_sync_committee
    store.finalized_header = update.finalized_header
    if store.finalized_header.slot > store.optimistic_header.slot:
        store.optimistic_header = store.finalized_header


def process_light_client_update(store: LightClientStore,
                                update: LightClientUpdate,
                                current_slot: Slot,
                                genesis_validators_root: Root,
                                fork_version: Version             # I added in fork version because idk how to calculate it   
                                ) -> None:
    validate_light_client_update(store, update, current_slot, genesis_validators_root, fork_version)

    sync_committee_bits = update.sync_aggregate.sync_committee_bits

    # Update the best update in case we have to force-update to it if the timeout elapses
    if (
        store.best_valid_update is None
        or is_better_update(update, store.best_valid_update)
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
        and update.finalized_header.slot > store.finalized_header.slot
    ):
        # Normal update through 2/3 threshold
        apply_light_client_update(store, update)
        store.best_valid_update = None