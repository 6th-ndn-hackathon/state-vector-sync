# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2018 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU Lesser General Public License is in the file COPYING.

import logging
from pyndn.name import Name
from pyndn.interest import Interest
from pyndn.data import Data
from pyndn.util.blob import Blob
from pyndn.util.memory_content_cache import MemoryContentCache

class StateVectorSync2018(object):
    """
    Create a new StateVectorSync2018 to communicate using the given face.
    Register the applicationBroadcastPrefix to receive sync notification
    interests.
    Note: Your application must call processEvents. Since processEvents
    modifies the internal ChronoSync data structures, your application should
    make sure that it calls processEvents in the same thread as this
    constructor (which also modifies the data structures).

    :param onReceivedSyncState: When StateVectorSync receives a state
      vector, this calls onReceivedStateVector(stateVector) where stateVector
      is the list of SyncState of only the members whose sequence number has
      increased from the previous onReceivedStateVector callback. The callback
      should send interests to fetch the application data for the sequence
      numbers in the sync state.
      NOTE: The library will log any exceptions raised by this callback, but
      for better error handling the callback should catch and properly
      handle any exceptions.
    :type onReceivedSyncState: function object
    :param onInitialized: This calls onInitialized() when the first state
      vector is received.
      NOTE: The library will log any exceptions raised by this callback, but
      for better error handling the callback should catch and properly
      handle any exceptions.
    :type onInitialized: function object
    :param Name memberDataPrefix: The prefix used by this application instance
      for application data and to identify this member. (If the application uses
      a new session number on startup, it needs to include this in the
      memberDataPrefix.) For example, "/my/local/prefix/ndnchat4/0K4wChff2v/123".
      In the state vector, this member is identified by the string
      memberDataPrefix.toUri().
    :param Name applicationBroadcastPrefix: The broadcast name prefix including
      the application name. For example, "/ndn/broadcast/ChronoChat-0.3/ndnchat1".
      This makes a copy of the name.
    :param Face face: The Face for calling registerPrefix and expressInterest.
      The Face object must remain valid for the life of this StateVectorSync2018
      object.
    :param KeyChain keyChain: The key chain to sign a data packet (not to sign a
      notification interest with HMAC).
    :param SigningInfo signingParams: The signing parameters to sign a data
      packet (not to sign a notification interest with HMAC).
    :param Blob hmacKey: The shared key for signing notification interests with
      HmacWithSha256.
    :param float notificationInterestLifetime: The interest lifetime in
      milliseconds for notification interests.
    :param onRegisterFailed: If failed to register the prefix to receive
      interests for the applicationBroadcastPrefix, this calls
      onRegisterFailed(applicationBroadcastPrefix).
      NOTE: The library will log any exceptions raised by this callback, but
      for better error handling the callback should catch and properly
      handle any exceptions.
    :type onRegisterFailed: function object
    :param int previousSequenceNumber (optional): The previously published
      sequence number for the same memberDataPrefix. In case the
      memberDataPrefix does not already include a unique session number, this
      can be used by the application to restore the state from a previous use.
      If omitted, this uses -1 so that the next published sequence number is 0.
    """
    def __init__(self, onReceivedSyncState, onInitialized,
      memberDataPrefix, applicationBroadcastPrefix, face, keyChain,
      signingParams, hmacKey, notificationInterestLifetime, onRegisterFailed,
      previousSequenceNumber = -1):
        pass

    class SyncState(object):
        """
        A SyncState holds the entries of a state vector which is passed to the
        onReceivedSyncState callback which was given to the StateVectorSync2018
        constructor.
        """
        def __init__(self, dataPrefixUri, sequenceNo):
            self._dataPrefixUri = dataPrefixUri
            self._sequenceNo = sequenceNo

        def getDataPrefix(self):
            """
            Get the member data prefix.

            :return: The member data prefix as a Name URI string (which is also
              the member ID).
            :rtype: str
            """
            return self._dataPrefixUri

        def getSequenceNo(self):
            """
            Get the sequence number for this member.

            :return: The sequence number.
            :rtype: int
            """
            return self._sequenceNo

    def getMemberDataPrefixes(self):
        """
        Get a copy of the current list of the Name URI for each member data
        prefix (which is the member ID). You can use these in
        getMemberSequenceNo(). This includes the prefix for this user.

        :return: A copy of the list of each member data prefix.
        :rtype: array of str
        """
        pass

    def getMemberSequenceNo(self, memberDataPrefix):
        """
        Get the current sequence number for the given memberDataPrefix in the
        current state vector.

        :param std memberDataPrefix: The member data prefix as a Name URI string.
        :return: The current sequence sequence number for the member, or -1 if
          the memberDataPrefix is not in the state vector.
        :rtype: int
        """
        pass

    def publishNextSequenceNo(self):
        """
        Increment the sequence number and send a new notification interest where
        the name is the applicationBroadcastPrefix + the encoding of the new
        state vector. Use the hmacKey given to the constructor to sign with
        HmacWithSha256.
        After this, your application should publish the content for the new
        sequence number. You can get the new sequence number with getSequenceNo().
        Note: Your application must call processEvents. Since processEvents
        modifies the internal ChronoSync data structures, your application should
        make sure that it calls processEvents in the same thread as
        publishNextSequenceNo() (which also modifies the data structures).
        """
        pass

    def getSequenceNo(self):
        """
        Get the sequence number of the latest data published by this application
        instance.

        :return: The sequence number.
        :rtype: int
        """
        return self._sequenceNo
