from containers import ( MIN_GENESIS_TIME, 
                         current_time, 
                         genesis_validators_root,
                         uint64, 
                         time,
)
from functions import ( get_current_sync_period,
                        initialize_light_client_store,
                        process_light_client_update,
                        # sync_to_current_period,
                        sync_to_current_updates,
)
from helper import ( bootstrap_url,
                     checkpoint_url,
                    #  trusted_block_root,
                     call_api, 
                     compute_sync_committee_period_at_slot, 
                     get_current_slot, 
                     initialize_bootstrap_object, 
                     initialize_light_client_update,
                     parse_hex_to_byte,
                     updates_for_period,
)

# checkpoint = call_api(checkpoint_url)
# checkpoint_message = checkpoint.json()
# finalized_checkpoint_root = checkpoint_message['data']['finalized']['root']    # Print to get the hex encoded bootstrap block root
trusted_block_root =  parse_hex_to_byte("0x705db40cc768f3d3b515fa36fde616f7a934c22d40e08eb2e2fa7bdd59c086ff")  # trusted_block_root == finalized_checkpoint_root
# trusted_block_root =  parse_hex_to_byte("0xc55890e1754b77059cea7e98cec96faa0c860a260991831cdeb23c063a974adf")  # trusted_block_root == finalized_checkpoint_root


if __name__ == "__main__":
  # ========================================= 
  # Step 1: Initialize the light client store
  # ========================================= 
  bootstrap = call_api(bootstrap_url)
  assert bootstrap.status_code == 200 
  bootstrap_object = initialize_bootstrap_object(bootstrap.json())
  light_client_store = initialize_light_client_store(trusted_block_root, bootstrap_object)
  print(type(light_client_store.finalized_header.state_root))  


  # ============================================================ 
  # Step 2:     Sync from bootstrap period to current period
  #         (if already up to current period, move on to step 3) 
  # ============================================================ 
  count = 0 
  store_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)
  current_slot =  get_current_slot(uint64(int(time.time())), MIN_GENESIS_TIME)
  current_period = compute_sync_committee_period_at_slot(current_slot) 
  
  if store_period == current_period: 
    updates = updates_for_period(store_period)
    light_client_update = initialize_light_client_update(updates.json())

  # Sync to current period logic is out here now.
  while store_period < current_period:
    # Define within while loop to continually get updates on the current time
    store_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)
    current_slot =  get_current_slot(uint64(int(time.time())), MIN_GENESIS_TIME)
    current_period = compute_sync_committee_period_at_slot(current_slot) 

    # Store period gets updated within process light client update!
    updates = updates_for_period(store_period+count)
    # Account for store period being the same during bootstrap and period after. 
    if count == 0: 
      count += 1
    if updates.status_code == 200:
      light_client_update = initialize_light_client_update(updates.json())
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
      time.sleep(1)

  # ====================================================================================================== 
  # Step 3: Sync from current period to      current block header slot - 1    and stay synced every slot.
  #         We're always one slot behind the actual current header, because we need the sync aggregate's
  #         signature to verify our slot.  (The sync aggregate is always block n + 1) 
  # ====================================================================================================== 
  
  # This was the old way
  sync_to_current_updates(light_client_store, light_client_update)
  
  
  # Sync to current block logic is out here now.
  # while True: 
    # store_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)
    # current_period = get_current_sync_period(uint64(int(time.time())), MIN_GENESIS_TIME) 
  