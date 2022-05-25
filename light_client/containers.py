# Containers
class LightClientUpdate(Container):
  # The beacon block header that is attested to by the sync committee
  attested_header: BeaconBlockHeader
  # Next sync committee corresponding to the active header
  next_sync_committee: SyncCommittee
  next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
  # The finalized beacon block header attested to by Merkle branch
  finalized_header: BeaconBlockHeader
  finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
  # Sync committee aggregate signature
  sync_aggregate: SyncAggregate
  # Fork version for the aggregate signature
  fork_version: Version

@dataclass
class LightClientStore(object):
  # Beacon block header that is finalized
  finalized_header: BeaconBlockHeader
  # Sync committees corresponding to the header
  current_sync_committee: SyncCommittee
  next_sync_committee: SyncCommittee
  # Best available header to switch finalized head to if we see nothing else
  best_valid_update: Optional[LightClientUpdate]
  # Most recent available reasonably-safe header
  optimistic_header: BeaconBlockHeader
  # Max number of active participants in a sync committee (used to calculate safety threshold)
  previous_max_active_participants: uint64
  current_max_active_participants: uint64