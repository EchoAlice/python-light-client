from containers import LightClientUpdate

# Helper functions
def is_finality_update(update: LightClientUpdate) -> bool:
  return update.finalized_header != BeaconBlockHeader()

def get_subtree_index(generalized_index: GeneralizedIndex) -> uint64:
  return uint64(generalized_index % 2**(floorlog2(generalized_index)))

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