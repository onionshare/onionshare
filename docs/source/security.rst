Security Design
===============

Read :ref:`how_it_works` first to get a handle on how OnionShare works.

Like all software, OnionShare may contain bugs or vulnerabilities.

What OnionShare protects against
--------------------------------

**Third parties don't have access to anything that happens in OnionShare.** Using OnionShare means hosting services directly on your computer. When sharing files with OnionShare, they are not uploaded to any server. If you make an OnionShare chat room, your computer acts as a server for that too. This avoids the traditional model of having to trust the computers of others.

**Network eavesdroppers can't spy on anything that happens in OnionShare in transit.** The connection between the Tor onion service and Tor Browser is end-to-end encrypted. This means network attackers can't eavesdrop on anything except encrypted Tor traffic. Even if an eavesdropper is a malicious rendezvous node used to connect the Tor Browser with OnionShare's onion service, the traffic is encrypted using the onion service's private key.

**Anonymity of OnionShare users are protected by Tor.** OnionShare and Tor Browser protect the anonymity of the users. As long as the OnionShare user anonymously communicates the OnionShare address with the Tor Browser users, the Tor Browser users and eavesdroppers can't learn the identity of the OnionShare user.

**If an attacker learns about the onion service, it still can't access anything.** Prior attacks against the Tor network to enumerate onion services allowed the attacker to discover private ``.onion`` addresses. If an attack discovers a private OnionShare address, they will also need to guess the private key used for client authentication in order to access it (unless the OnionShare user chooses make their service public by turning off the private key -- see :ref:`turn_off_private_key`).

What OnionShare doesn't protect against
---------------------------------------

**Communicating the OnionShare address and private key might not be secure.** Communicating the OnionShare address to people is the responsibility of the OnionShare user. If sent insecurely (such as through an email message monitored by an attacker), an eavesdropper can tell that OnionShare is being used. If the eavesdropper loads the address in Tor Browser while the service is still up, they can access it. To avoid this, the address must be communicated securely, via encrypted text message (probably with disappearing messages enabled), encrypted email, or in person. This isn't necessary when using OnionShare for something that isn't secret.

**Communicating the OnionShare address and private key might not be anonymous.** Extra precautions must be taken to ensure the OnionShare address is communicated anonymously. A new email or chat account, only accessed over Tor, can be used to share the address. This isn't necessary unless anonymity is a goal.
