# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2018 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
# Author: Haitao Zhang <zhtaoxiang@gmail.com>
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

import bisect
import logging
from pyndn.name import Name
from pyndn.interest import Interest
from pyndn.security import KeyChain
from pyndn.util.blob import Blob
from pyndn.encoding.tlv.tlv_encoder import TlvEncoder
from pyndn.encoding.tlv.tlv_decoder import TlvDecoder

class StateVectorSync2018(object):
    """
    Create a new StateVectorSync2018 to communicate using the given face.
    Register the applicationBroadcastPrefix to receive sync notification
    interests.
    Note: Your application must call processEvents. Since processEvents
    modifies the internal ChronoSync data structures, your application should
    make sure that it calls processEvents in the same thread as this
    constructor (which also modifies the data structures).

    :param onReceivedSyncState: When StateVectorSync2018 receives a state
      vector, this calls onReceivedSyncState(syncStates) where syncStates
      is the list of SyncState of only the members whose sequence number has
      increased from the previous onReceivedSyncState callback. The callback
      should send interests to fetch the application data for the sequence
      numbers in the sync state.
      NOTE: The library will log any exceptions raised by this callback, but
      for better error handling the callback should catch and properly
      handle any exceptions.
    :type onReceivedSyncState: function object
    :param onInitialized: This calls onInitialized() when this has registered
      the broadcast prefix and is initialized.
      NOTE: The library will log any exceptions raised by this callback, but
      for better error handling the callback should catch and properly
      handle any exceptions.
    :type onInitialized: function object
    :param Name applicationDataPrefix: The prefix used by this application
      instance for others to fetch application data and to identify this member.
      (If the application restarts with sequence 0 on startup, it needs to
      include a unique session number in the applicationDataPrefix.) For example,
      "/my/local/prefix/ndnchat4/0K4wChff2v/123". In the state vector, this
      member is identified by the string applicationDataPrefix.toUri().
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
      sequence number for the same applicationDataPrefix. In case the
      applicationDataPrefix does not already include a unique session number, this
      can be used by the application to restore the state from a previous use.
      If omitted, this uses -1 so that the next published sequence number is 0.
    """
    def __init__(self, onReceivedSyncState, onInitialized,
      applicationDataPrefix, applicationBroadcastPrefix, face, keyChain,
      signingParams, hmacKey, notificationInterestLifetime, onRegisterFailed,
      previousSequenceNumber = -1):
        self._onReceivedSyncState = onReceivedSyncState
        self._onInitialized = onInitialized
        self._applicationDataPrefixUri = applicationDataPrefix.toUri()
        self._applicationBroadcastPrefix = Name(applicationBroadcastPrefix)
        self._face = face
        self._keyChain = keyChain
        self._signingParams = signingParams
        self._hmacKey = hmacKey
        self._notificationInterestLifetime = notificationInterestLifetime

        # The dictionary key is member ID string. The value is the sequence number.
        self._stateVector = {}
        # The keys of _stateVector in sorted order, kept in sync with _stateVector.
        # (We don't use OrderedDict because it doesn't sort keys on insert.)
        self._sortedStateVectorKeys = []
        self._sequenceNo = previousSequenceNumber
        self._enabled = True

        # Register to receive broadcast interests.
        self._face.registerPrefix(
          self._applicationBroadcastPrefix, self._onInterest, onRegisterFailed,
          self._onRegisterSuccess)

    class SyncState(object):
        """
        A SyncState holds the values of one entry of a state vector which is
        passed to the onReceivedSyncState callback which was given to the
        StateVectorSync2018 constructor.
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

        def __str__(self):
            return "SyncState(" + self._dataPrefixUri + ", " + str(self._sequenceNo) + ")"

        def __repr__(self):
            return self.__str__()

        def __eq__(self, other):
            return (isinstance(other, StateVectorSync2018.SyncState) and
              self._dataPrefixUri == other._dataPrefixUri and
              self._sequenceNo == other._sequenceNo)

        def __ne__(self, other):
            return not self == other

    def getProducerPrefixes(self):
        """
        Get a copy of the current list of the Name URI for each producer data
        prefix (which is their member ID). You can use these in
        getProducerSequenceNo(). This includes the prefix for this user.

        :return: A copy of the list of each producer data prefix.
        :rtype: array of str
        """
        # Just return a copy of the keys of the state vector dictionary.
        return self._sortedStateVectorKeys[:]

    def getProducerSequenceNo(self, producerDataPrefix):
        """
        Get the current sequence number for the given producerDataPrefix in the
        current state vector.

        :param str producerDataPrefix: The producer's application data prefix as
          a Name URI string (also the member ID).
        :return: The current sequence sequence number for the member, or -1 if
          the producerDataPrefix is not in the state vector.
        :rtype: int
        """
        if producerDataPrefix in self._stateVector:
            return self._stateVector[producerDataPrefix]
        else:
            return -1

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
        self._sequenceNo += 1
        self._setSequenceNumber(self._applicationDataPrefixUri, self._sequenceNo)

        logging.getLogger(__name__).info(
          "Broadcast new seq # %s. State vector %s", str(self._sequenceNo),
          str(self._stateVector))
        self._broadcastStateVector()

    def getSequenceNo(self):
        """
        Get the sequence number of the latest data published by this application
        instance.

        :return: The sequence number.
        :rtype: int
        """
        return self._sequenceNo

    def shutdown(self):
        """
        Unregister callbacks so that this does not respond to interests anymore.
        If you will discard this StateVectorSync2018 object while your
        application is still running, you should call shutdown() first.  After
        calling this, you should not call publishNextSequenceNo() again since
        the behavior will be undefined.
        Note: Because this modifies internal data structures, your application
        should make sure that it calls processEvents in the same thread as
        shutdown() (which also modifies the data structures).
        """
        self._enabled = False
        self._contentCache.unregisterAll()

    @staticmethod
    def encodeStateVector(stateVector, stateVectorKeys):
        """
        Encode the stateVector as TLV.

        :param dict<str,int> stateVector: The state vector dictionary where
          the key is the member ID string and the value is the sequence number.
        :param list<str> stateVectorKeys: The key strings of stateVector,
          sorted in the order to be encoded.
        :return: A Blob containing the encoding.
        :rtype: Blob
        """
        encoder = TlvEncoder(256)
        saveLength = len(encoder)

        # Encode backwards.
        for i in range(len(stateVectorKeys) - 1, -1, -1):
            saveLengthForEntry = len(encoder)

            encoder.writeNonNegativeIntegerTlv(
              StateVectorSync2018.TLV_StateVector_SequenceNumber,
              stateVector[stateVectorKeys[i]])
            encoder.writeBlobTlv(StateVectorSync2018.TLV_StateVector_MemberId,
              Blob(stateVectorKeys[i]).buf())
            encoder.writeTypeAndLength(StateVectorSync2018.TLV_StateVectorEntry,
              len(encoder) - saveLengthForEntry)

        encoder.writeTypeAndLength(StateVectorSync2018.TLV_StateVector,
          len(encoder) - saveLength)

        return Blob(encoder.getOutput(), False)

    @staticmethod
    def decodeStateVector(input):
        """
        Decode the input as a TLV state vector.

        :param input: The array with the bytes to decode.
        :type input: An array type with int elements
        :return: A new dictionary where the key is the member ID string and the
          value is the sequence number. If the input encoding has repeated
          entries with the same member ID, this uses only the last entry.
        :rtype: dict<str,int>
        :raises ValueError: For invalid encoding.
        """
        stateVector = {}

        # If input is a blob, get its buf().
        decodeBuffer = input.buf() if isinstance(input, Blob) else input
        decoder = TlvDecoder(decodeBuffer)

        endOffset = decoder.readNestedTlvsStart(StateVectorSync2018.TLV_StateVector)

        while decoder.getOffset() < endOffset:
            entryEndOffset = decoder.readNestedTlvsStart(
              StateVectorSync2018.TLV_StateVectorEntry)

            memberIdBlob = Blob(decoder.readBlobTlv(
              StateVectorSync2018.TLV_StateVector_MemberId), False)
            stateVector[str(memberIdBlob)] = decoder.readNonNegativeIntegerTlv(
              StateVectorSync2018.TLV_StateVector_SequenceNumber)
            decoder.finishNestedTlvs(entryEndOffset)

        decoder.finishNestedTlvs(endOffset)

        return stateVector

    def _makeNotificationInterest(self):
        """
        Make and return a new Interest where the name is
        _applicationBroadcastPrefix plus the encoding of _stateVector. Also
        use _hmacKey to sign it with HmacWithSha256.

        :return: The new signed notification interest.
        :rtype: Interest
        """
        interest = Interest(self._applicationBroadcastPrefix)
        interest.setInterestLifetimeMilliseconds(self._notificationInterestLifetime)
        interest.getName().append(StateVectorSync2018.encodeStateVector
          (self._stateVector, self._sortedStateVectorKeys))

        # TODO: Should we just use key name /A ?
        KeyChain.signWithHmacWithSha256(interest, self._hmacKey, Name("/A"))

        return interest

    def _broadcastStateVector(self):
        """
        Call _makeNotificationInterest() and then expressInterest to broadcast
        the notification interest.
        """
        interest = self._makeNotificationInterest()
        # A response is not required, so ignore the timeout and Data packet.
        self._face.expressInterest(interest, StateVectorSync2018._dummyOnData)

    def _setSequenceNumber(self, memberId, sequenceNumber):
        """
        An internal method to update the _stateVector by setting memberId to
        sequenceNumber. This is needed because we also have to update
        _sortedStateVectorKeys.

        :param str memberId: The member ID string.
        :param int sequenceNumber: The sequence number for the member.
        """
        if not memberId in self._sortedStateVectorKeys:
            # We need to keep _sortedStateVectorKeys synced with _stateVector.
            bisect.insort(self._sortedStateVectorKeys, memberId)

        self._stateVector[memberId] = sequenceNumber

    def _onInterest(self, prefix, interest, face, interestFilterId, filter):
        """
        Process a received broadcast interest.
        """
        # Verify the HMAC signature.
        verified = False
        try:
            verified = KeyChain.verifyInterestWithHmacWithSha256(
              interest, self._hmacKey)
        except:
            # Treat a decoding failure as verification failure.
            pass
        if not verified:
            # Signature verification failure.
            logging.getLogger(__name__).info("Dropping Interest with failed signature: %s",
              interest.getName().toUri())
            return

        encoding = interest.getName().get(
          self._applicationBroadcastPrefix.size()).getValue()
        receivedStateVector = StateVectorSync2018.decodeStateVector(encoding)
        logging.getLogger(__name__).info("Received broadcast state vector %s",
          str(receivedStateVector))

        (syncStates, needToReply) = self._mergeStateVector(receivedStateVector)
        if len(syncStates) > 0:
            # Inform the application up new sync states.
            try:
                self._onReceivedSyncState(syncStates)
            except:
                logging.exception("Error in onReceivedSyncState")

        if needToReply:
            # Inform other members who may need to be updated.
            logging.getLogger(__name__).info(
              "Received state vector was outdated. Broadcast state vector %s",
              str(self._stateVector))
            self._broadcastStateVector()

    def _mergeStateVector(self, receivedStateVector):
        """
        Merge receivedStateVector into self._stateVector and return the
        updated entries.

        :param dict<str,int> receivedStateVector: The received state vector
          dictionary where the key is the member ID string and the value is
          the sequence number.
        :return: A tuple of (syncStates, needToReply) where syncStates is the
          list of new StateVectorSync2018.SyncState giving the entries in
          self._stateVector that were updated, and needToReply is True if
          receivedStateVector is lacking more current information which was in
          self._stateVector.
        :rtype: (list<StateVectorSync2018.SyncState>, bool)
        """
        needToReply = False
        result = []
        if self._stateVector == receivedStateVector:
            return (result, needToReply)
        for k, v in receivedStateVector.items():
            if self._stateVector.get(k) == None or self._stateVector.get(k) < v:
                result.append(StateVectorSync2018.SyncState(k,v))
                self._setSequenceNumber(k, v)
        for k, v in self._stateVector.items():
            if receivedStateVector.get(k) == None or receivedStateVector.get(k) < v:
                needToReply = True
                break
        return (result, needToReply)

    def _onRegisterSuccess(self, prefix, registeredPrefixId):
        try:
            self._onInitialized()
        except:
            logging.exception("Error in onInitialized")

    @staticmethod
    def _dummyOnData(interest, data):
        """
        This is a do-nothing onData for using expressInterest when we don't
        expect a response Data packet.
        """
        pass

    # Assign TLV types as crtitical values for application use.
    TLV_StateVector = 129
    TLV_StateVectorEntry = 131
    TLV_StateVector_MemberId = 133
    TLV_StateVector_SequenceNumber = 135
