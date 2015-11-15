# Security Design Document

## How it works

OnionShare is a tool that helps users securely and anonymously share files over the internet.

First, the sender chooses files and folders they wish to share with the recipient. OnionShare then starts a web server at `127.0.0.1` on a random port. It generates a random string called a slug, and makes the files available for download at `http://127.0.0.1:[port]/[slug]/`. It then makes the web server accessible as Tor hidden service, and displays the URL `http://[hiddenservice].onion/[slug]` to the sender to share. A final OnionShare URL looks something like `http://szbjzh4ndjo4wexv.onion/sad4vq2qvvp3bbszwioh2jwlgi`.

The sender is responsible for securely sharing that URL with the recipient using a communication channel of their choice, such as in an encrypted email, chat, or voice call, or something less secure like a Twitter or Facebook message, depending on their threat model.

The recipient must use Tor Browser to load the URL and download the files.

As soon as the shared files get downloaded, or when the sender closes OnionShare, the Tor hidden service and web servers shut down, completely removing the files from the internet (there is an option to not shut down after the first download, to allow the files to be downloaded multiple times). Because of this, OnionShare is most useful if it's used in real-time. For example, if a user runs OnionShare on their laptop, and then suspends their laptop before the files have been downloaded, the service will not be available until the laptop is unsuspended and connected to the internet again.

## What it protects against

* **Third parties don't have access to files being shared.** The files are hosted directly on the sender's computer and don't get uploaded to any server. Instead, the sender's computer becomes the server. Traditional ways of sending files, like in an email or using a cloud hosting service, require trusting the service with access to the files being shared.
* **Network eavesdroppers can't spy on files in transit.** Because connections between Tor hidden services and Tor Browser are end-to-end encrypted, no network attackers can eavesdrop on the shared files while the recipient is downloading them. If the eavesdropper is positioned on the sender's end, the recipient's end, or is a malicious Tor node, they will only see Tor traffic. If the eavesdropper is a malicious rendezvous node used to connect the recipient's Tor client with the sender's hidden service, the traffic will be encrypted using the hidden service key.
* **Anonymity of sender and recipient are protected by Tor.** OnionShare and Tor Browser protect the anonymity of the users. As long as the sender anonymously communicates the OnionShare URL with the recipient, the recipient and eavesdroppers can't learn the identity of the sender.
* **If an attacker enumerates the hidden service, the shared files remain safe.** There have been attacks against the Tor network that can enumerate hidden services. If someone discovers the .onion address of an OnionShare hidden service, they still cannot download the shared files without knowing the slug. The slug is generated using 16 bytes of entropy, and the OnionShare server checks request URIs using a constant time string comparison function, so timing attacks can't be used to guess the slug.

## What it doesn't protect against

* **Communicating the OnionShare URL might not be secure.** The sender is responsible for securely communicating the OnionShare URL with the recipient. If they send it insecurely (such as through an email message, and their email is being monitored by an attacker), the eavesdropper will learn that they're sending files with OnionShare. If the attacker loads the URL in Tor Browser before the legitimate recipient gets to it, they can download the files being shared. If this risk fits the sender's threat model, they must find a more secure way to communicate the URL, such as in an encrypted email, chat, or voice call. This isn't necessary in cases where the files being shared aren't secret.
* **Communicating the OnionShare URL might not be anonymous.** While OnionShare and Tor Browser allow for anonymously sending files, if the sender wishes to remain anonymous they must take extra steps to ensure this while communicating the OnionShare URL. For example, they might need to use Tor to create a new anonymous email or chat account, and only access it over Tor, to use for sharing the URL. This isn't necessary in cases where there's no need to protect anonymity, such as coworkers who know each other sharing work documents.
