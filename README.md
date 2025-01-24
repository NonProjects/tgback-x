# TGBACK-X — a library for making Telegram account backups

######  _[Check out the GUI implementation - XQt!](https://github.com/NotStatilko/tgback-x-qt)_

**TGBACK-X** is a little library which you can utilize to create an **encrypted backup of your Telegram account**. If you've been around here before then you probably heard about my old project called [TGBACK](https://github.com/NotStatilko/tgback) (without *X*). Actually, this library is an **implementation revisit** of the same concept with just about the same purpose.

The difference between the *old TGBACK* and *X version* (except completely different backup structure) is that this repository is **strictly Python library for devs** and doesn't have any App implementation (like Command line app that old *TGBACK* have). However most importantly, **this version doesn't create any backup files** (hence the *X* in name). Instead, it relies on the *Providers* — **third-party services that we use to store encrypted backup data.**

## **Idea behind:**

1. User type password or **we generate random N (default 8) mnemonic words**;
2. **We feed password to Scrypt** (1GB from defaults), obtain *Scrypt key*;
3. We make **(hash)** a unique *KeyID* from *Scrypt key* material;
4. We ask for Telegram login credentials, log into account;
5. We take account's **session** and construct a backup data;
6. We **encrypt backup data** with one of *Cryptography Protocol*;
7. We **store the encrypted backup data on Provider server by KeyID**.

In that way, User will be able to get Session only by typing secret Phrase. Obviously, this approach may impose some risks — anyone who will be able to type the same Phrase will obtain a full access to account. User should **treat its Phrase like Bitcoin seed phrase** and **never** use *X* version on a compromised Computer, e.g, with malwares / other programs that can record keyboard or screen.

Telegram session is no-special in TGBACK-X and can be killed at any time through Telegram Settings —> Devices or directly from backup data by itself. Disconnected Session is a useless pile of encoded bytes. If you feel that your Phrase may be compromised — **destroy session immediately**. You can always create a different one. Different backups keep different sessions, so they wouldn't be connected at all.

## **Default approach:**

**Default** (and currently only one implemented here) *Provider* is a `TelegramChannel`. That is, we keep your encrypted Telegram data inside Telegram! The *KeyID* would be a *Channel public link*, and *Backup data* would be regular message. We utilize interesting Telegram feature — any **public** Telegram channel can be previewed in Browser without login. [**See this for example**](https://t.me/s/X3KEK3ELMZDDJ5KXEIJMEH65L4CJCMAY) — is a backup that you can make with `TelegramChannel`. We fetch backup data (`TelegramChannel` use `JSON_AES_CBC_UB64` crypto protocol) through http requests, decrypt and give Session to User.

## Welcome, developers

I (hope I) made **TGBACK-X** library modular, so you can create your own *Provider* / *Protocol* classes. Currently there is no documentation, but I tried to describe everything in Docstrings. You can refer to them and check how default classes are implemented for basic understanding. While I don't think that there is any sense in adding new cryptography *Protocol* (`JSON_AES_CBC_UB64` seems about enough), different *Provider* would be interesting to see.

### Install
```
pip install tgback-x
```
