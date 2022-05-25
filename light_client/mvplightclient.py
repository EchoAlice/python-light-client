import requests
import json
from containers import LightClientUpdate
from containers import LightClientStore
from helperfunctions import is_finality_update
from helperfunctions import get_subtree_index
from helperfunctions import get_active_header
from helperfunctions import get_safety_threshold

#  MVP Light Client:  Track latest state/block root

if __name__ == "__main__":