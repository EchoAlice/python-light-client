from api import bootstrap_object, trusted_block_root
from functions import ( initialize_light_client_store,
                        sync_to_current_period,
                        sync_to_current_updates,
)


if __name__ == "__main__":
  # Step 1: Initialize the light client store
  light_client_store = initialize_light_client_store(trusted_block_root, bootstrap_object)
   
  # Step 2: Sync from bootstrap period to current period 
  light_client_update = sync_to_current_period(light_client_store)
   
  # Step 3: Sync from current period to      current block header slot - 1    and stay synced every slot.
  #         We're always one slot behind the actual current header, because we need the sync aggregate's
  #         signature to verify our slot.  (The sync aggregate is always block n + 1) 
  sync_to_current_updates(light_client_store, light_client_update)