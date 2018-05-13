import sys
import logging
import time
import random
import select
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.security import SafeBag
from pyndn.util import Blob
from svs.sync import StateVectorSync2018

def main():
    stateVector = {}
    stateVector["/user1"] = 10;
    stateVector["/user2"] = 1;

    receivedStateVector = {}
    receivedStateVector["/user1"] = 9;
    receivedStateVector["/user2"] = 2;
    receivedStateVector["/user3"] = 20;

    # Merge receivedStateVector into stateVector.

main()
