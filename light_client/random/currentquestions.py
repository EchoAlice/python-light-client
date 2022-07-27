#  Big Question:        How does the update.finalized_header relate to the 
#                 update.attested_header (specifically during sync period updates)
#
#  Why do I care about the update.attested header when I'm updating to the current sync period?
#  Shouldn't I only be concerned about finality?
#
#  Why isn't the update trying to convince us of finalized header when syncing to the current sync period?
#
#  What does a merkle proof do?  It allows you to query a database and have proof of legitimacy if you have the trusted root.
#
#  How do you transition from bootstrap period to the next sync period trustlessly?