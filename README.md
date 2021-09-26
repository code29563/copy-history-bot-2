# README for private channels

This script is intended for copying messages from private channels to which you don't have the ability to add bots as admins.

# Features

- Messages are copied to the destination chat without the 'Forwarded from:' tag
- Dynamically switching between clients when encountering floodwaits, to avoid having to wait them out and increase the average rate at which messages are sent
- Uses bot clients to send messages wherever possible, to reduce the number of messages sent by user clients which are vulnerable to bans
- Adds a detailed caption to copied messages, giving various details about the original message
- The script doesn't terminate when it gets disconnected from the internet – it just attempts to reconnect until the connection is restored and then resumes working. Likewise when the system goes to sleep, it resumres when it wakes up and reconnects to the internet.
- Handling of MediaEmptyError and FileReferenceExpiredError
- Option to print each successfully copied message to a file

# Getting started

1. Make an app with the Telegram API: [https://my.telegram.org/apps](https://my.telegram.org/apps) and fill in the API\_ID and API\_HASH environment variables in the .env file with the App api\_id and App api\_hash respectively.
2. Choose which user clients you want to use to copy messages, and obtain Telethon session strings for each of them, e.g. using option 2 of [this script](https://github.com/code29563/Telethon-Pyrogram-session-strings).

   Generally, the more clients you use, the better. Due to the risk of a client getting banned, and especially when the number of messages you want to copy is large (in the thousands), it's worth only using clients that you can tolerate getting banned rather than e.g. your personal account with which you communicate with people. It may also be worth using older accounts rather than recently made accounts, due to the possibility that the latter are more likely to get banned.

	Once you've got the session strings, list them in the SESSION\_STRINGS environment variable, comma-separated. You can split them onto multiple lines if you want. Ensure you don't put a comma on the end of the last session string listed.

	The user clients don't have to include the one with which the API ID and Hash were obtained.

	The minimum number of session strings required is 1.

1. Fill in the BOT\_TOKENS environment variable with the bot tokens of the bots that you want to use to copy messages (you can make bots using @BotFather), following the same syntax as for the SESSION\_STRINGS environment variable.

	I recommend using around 17 bots, which should be enough to completely avoid unnecessary floodwaits from the bot clients. To make this many bots, you might have to stagger it over a few days as @BotFather could limit the number of bots you make in a single day.

	The bots don't have to be made with the account with which the API ID and Hash were obtained, or with any of the accounts that you're using with their session strings in this script.

	The minimum number of bot tokens required is 1.

1. Fill in the CLONE\_SREAMS environment variable, which gives the details of the messages to be copied and where to copy them to. A single stream contains 4 comma-separated elements which are (in order): the ID of the source channel from which messages are to be copied, the ID of the message from which to start copying (which becomes the first message to be copied), the ID of the message at which to finish copying (which becomes the last message to be copied), and the ID of the destination chat to which to copy those messages. You can list multiple streams in the CLONE\_SREAMS environment variable, separated from each other by semi-colons, and if you want you can split them onto multiple lines and leave spaces between the elements and the commas/semi-colons. The streams are copied successively, one after the other, in the order you list them in the environment variable.

	The source channel ID and message IDs can simply be obtained by right-clicking a message in the Telegram app and copying it's link, then paste it somewhere. The number after the final forward slash is the message ID, and the number before it is the channel ID, but append -100 to it before inserting it in CLONE\_SREAMS. You can also find the channel ID through other means like with @username\_to\_id\_bot.

1. Make sure all the user clients are subscribed to the channel from which messages are to be copied, and make sure both the user clients and bot clients are all able to send messages to the destination to which the messages are to be copied, i.e. they should be admins if it's a channel, or members if it's a group, or if it's an individual user they should be able to send private messages to them.
2. If you want to print the Message object of each successfully copied message to a file, set the PRINT_TO_FILE environment variable to "1". The printed object contains various details of the message not present in the (already detailed) caption.
2. Run the script using 'python app.py'. Note that the RUN environment variable in the .env file is not to be modified by the user.

# Background

Messages in Telegram can be either media messages (if they contain a media object) or text messages (if they don't). See a list of media objects [here](https://core.telegram.org/type/MessageMedia).

If a text message is retrieved from a channel by a client, then it can be copied/forwarded by another client even if they didn't have access to the original channel. Any client can access the message's text (fully formatted with its [entities](https://core.telegram.org/api/entities)).

Some media objects in Telegram require an access hash (which could be unique for each client) for a client to be able to copy/forward them, regardless of whether it's a bot client or a user client. The client can obtain an access hash when it has access to the message containing the media object. When the channel is public, then like a user client, a bot can access the channel's messages without being a subscriber, otherwise if the channel is private then it seems it needs to be a subscriber. Currently it seems bots can only be subscribed to channels as admins, so when you aren't able to add bots as admins to the private channel, the use of a bot client to copy those media messages from it is out of question. When an attempt is made to copy them with a bot client, it fails with a MediaEmptyError.

Some media objects don't seem to require a client-specific access hash, including stickers, polls, contacts, and [locations](https://core.telegram.org/constructor/messageMediaGeo). These messages can be sent by a bot client like text messages.

For those media objects that do require an access hash, the remaining option is therefore to copy them with user clients that are subscribed to the channel and hence have access to its messages.

However, user clients are at risk of getting banned if they send a lot of requests. Multiple people have mentioned this and I myself have experienced this with 7 accounts getting banned, all of which were accounts made relatively recently though, whereas I didn't experience the same with some of my older accounts even when sending the same number of messages, so it's possible that for a recently created account to start sending lots of messages as one of the first things it does is considered suspicious activity by Telegram's system and receives an automatic ban.

To mitigate this at least partly, in this script, an attempt is made to copy each message with a bot client first, in case it is a text message or a media message that can be copied by a bot. If that fails with a MediaEmptyError, indicating that it's a media type that can't be copied with a bot due to the access hash issue mentioned above, then the message is copied with a user client.

This may be one reason it's worth including as many user clients' session strings as you can when using the script, to split the job of sending messages amongst more users so each individual user is sending less messages, and hence perhaps less likely to get banned.

If you're unable to get multiple user accounts to use, and the only account you have to use is one that you're not willing to get banned, then consider uncommenting 'await asyncio.sleep(2)' in the script to wait 2 seconds (or replace 2 with another number as you see fit) between switching from a bot client to a user client to send a message, the overall effect being that the messages sent by the user client are spaced out more and the rate at which it sends messages are decreased, possibly decreasing the likelihood of getting banned.

# How it works

For each stream, the user clients all concurrently retrieve the messages to be copied. Each user client retrieves all the messages to be copied so it has its own version of the Message object with its own access hash. When just some portion of the messages to be copied has been retrieved by all user clients, those messages start to get copied to the destination chat, whilst the rest of the messages are still being retrieved. No attempt is made to copy a message until all user clients have retrieved it.

Each user client is assigned a list in which it stores the messages it retrieves. All these lists should turn out identical in the messages they contain (even if the Message objects differ due to differing access hashes), because all user clients are retrieving the same messages. So the message at any particular position k in the list of one user client should have the same ID as the message at that same position k in the list of any of the other user clients. If that doesn't turn out to be the case, it seems some of the messages to be retrieved were deleted from the source channel during the process, such that some user clients ended up retrieving them and others didn't.

E.g. if there are two user clients, and messages with IDs 1 to 10000 to be copied, then if message 5000 gets deleted after user client 1 had already retrieved it but before user client 2 had done so, then the 4999th element of user client 1's list is the message with ID 4999, and the 4999th element of user client 2's list is also the message with ID 4999, but the 5000th element of user client 1's list is the mesage with ID 5000, while the 5000th element of user client 2's list would be the message with ID 5001. The 5001th element would be message 5001 and message 5002 respectively, and so on until the end of the list, with the positions of messages in one list being offset by 1 relative to their positions in the other list.

When this happens, whereby the messages at a position k in all lists aren't the same, the script terminates with a message informing you of this. The script only proceeds with copying messages if the messages at a position k in the lists of the user clients all have the same ID.

If the reader knows what floodwaits are and isn't interested in the technical details of how the script handles switching between clients, then they can skip the next part.

## Switching between clients and handling floodwaits

The API method used when retrieving messages is messages.getHistory, and the method used when sending messages is messages.sendMessage for text messages or messages.sendMedia for media messages.

A client (be it a bot client or user client) may receive a 420 FLOOD (floodwait) error if it makes a request with a particular method more than a particular number of times within some timeframe. The error includes a time the client is required to wait before it can successfully send another request with that method.

When a client encounters a floodwait, the script switches to a different client for sending subsequent messages. This allows the process of copying messages to continue, whilst the client that encountered the floodwait waits it out, rather than waiting for that client to finish its floodwait before copying further messages with it.

As clients continue to encounter floodwaits and the script continues to switch to other clients, all the clients may at some point have encountered a floodwait. The time when the client encountered the floodwait and the required waiting time are both recorded. When any client encounters a floodwait, the time passed since each client of the same type (bot or user) encountered its most recent floodwait is calculated and subtracted from the time it was required to wait. The result is the remaining floodwait that client is required to wait. If it's zero or negative, then that client has already finished waiting out its floodwait and it can now be used to copy messages again. The client with the least remaining floodwait is the client that is switched to, and if its remaining floodwait is positive then the script waits until it is finished. This also means that if a client encounters a floodwait but the remaining floodwait of every other client of the same type is longer, then the script just waits for the current client's floodwait to finish and then re-uses it instead of switching to a different client.

The exact numbers for how many requests of a method can be sent in what timeframe seems to be information Telegram hasn't made public, but some insight can be gained from testing and from the experiences of other users.

It seems a client can send 30 requests with messages.getHistory in a 30 second timeframe before receiving a floodwait requiring it to wait until the rest of the 30 seconds have passed. Up to 100 messages can be retrieved at a time, so this amounts to 3000 messages being retrieved every 30 seconds.

It seems a bot client can send up to 5 messages in a timeframe of about 5 seconds before receiving a floodwait of 3-4 seconds. A bot client also seems to be limited to sending 20 messages per minute, after which it receives a floodwait requiring it to wait until the minute has passed.

It seems a user client on the other hand can send 50 messages within 10 seconds before receiving a floodwait until the end of the 10 seconds. It seems it's also limited to 100 messages every 30 seconds, after which it receives a floodwait requiring it to wait until the 30 seconds have passed. I've noticed though that some user clients, especially those made with VOIP numbers, may be limited further in the rate at which they can send messages, being made to wait e.g. 1-2 seconds between each message they send.

I've noticed that at least sometimes the floodwait received might be slightly less than the actual time required to complete the 10 seconds or 30 seconds – maybe the floodwait in such cases was rounded down to the nearest second. If an attempt is then made after the floodwait is over to send a message, but the 10/30 seconds is still not up, another floodwait of 3 seconds is received.

These are general patterns I've noticed whilst testing, but I have observed exceptions to some of them. Note that these aren't necessarily the only limits that apply, and floodwaits could be received at seemingly random times requiring seemingly random waiting times.

I don't think I've ever received a floodwait of less than 3 seconds, so this might be the minimum floodwait that Telegram gives. This can therefore result in waiting longer than 10/30 seconds before the 51st/101th message gets send, e.g. when the 1st message is sent at t=0 and an attempt is made to send the 51st message at about t=6.5 seconds, upon which a floodwait is received for 3 seconds, then after waiting the floodwait another attempt is made to send the 51st message at t=9.5 seconds, upon which another floodwait of 3 seconds is received, so the 51st message only gets sent after t=12.5 seconds.

To avoid waiting this extra time, and to avoid wasting even fractions of a second sending requests only to receive a floodwait back, when it could reasonably have been predicted based on the above experimentally-deduced numbers, I've implemented a variable to act as a counter for the number of messages a client has sent, its value being increased by 1 every time the client sends a message, until it reaches a maximum. For bot clients, this maximum is 5 messages, and for user clients it's 50, and I've implemented a separate counter for each of the two client types. When the counter reaches the maximum, the time t at which this occurs for that client is recorded. Then out of all the clients of the same type, those with no remaining floodwait are selected, as they are able to immediately start sending messages. Out of those, the client for which the longest time has passed since the counter reached the maximum for it, i.e. the client with the lowest t, is chosen to send subsequent messages. The counter is then reset for this next client to start sending messages.

If a client has reached the maximum but all other clients of the same type have floodwaits remaining, then this client remains on and is used to attempt to send the next message at which it might receive a floodwait, after which the switch to the next client is handled as described previously. There's no guarantee it does receive a floodwait though, as what I've implemented doesn't take into consideration how long ago the client sent the 1st message in this sequence of messages. So it's possible e.g. that a user client sends 25 messages, then the next 100 are sent by bot clients, after which the user sends another 25 messages and the counter hits the maximum, but by this time 10 seconds has passed so it's able to send its 51st message without receiving a floodwait.

The counter is reset every time a switch to a different client is made, including when one encounters a floodwait, and if the remaining floodwait of other clients is longer and script just waits out the floodwait of the current client and re-uses it, the counter is still reset.

# Importance of using multiple clients

Switching between clients to avoid waiting out floodwaits is the main point of using multiple clients in the script. For every extra client you use, the average rate at which messages get copied increases, until if you have enough clients, the script never has to remain idle waiting out a floodwait. From experience, the rate at this point could reach around 300 messages per minute, and this point could be reached with about 17 bot clients and just 2 user clients.

E.g. if you have one client and it's limited to sending 50 messages per minute, and it's able to send 50 messages in 10 seconds, then it receives a floodwait after 10 seconds requiring it to wait 50 seconds (i.e. until the minute is up). The average rate in this case is 50 messages per minute and the script is idle for 50 seconds per minute. If you add another client, then the first client sends 50 messages in 10 seconds and receives a floodwait of 50 seconds, then the script switches to the second client which sends 50 messages in another 10 seconds and receives a floodwait of 50 seconds, then the script only has to wait 40 seconds before the first client can start copying messages again and the cycle repeats. In this case, the average rate has increased to 100 messages per minute, and the 'idle time' has reduced from 50 seconds per minute to 40 seconds per minute. If you add a third client, the rate increases to 150 messages per minute and the idle time reduces to 30 seconds per minute. And so on until when you have 6 clients, the rate is 300 messages per minute and there is no idle time.

At this point, it may seem like adding extra clients is superfluous. This may be true for bot clients, as their limits seem to be generally stable at 20 messages per minute, which a bot can send in about 4 seconds overall split up over the minute into batches of 5 messages, so accounting for minor variations in this, I've found 17 bot clients to be sufficient from experience. There's no significant disadvantage to adding more bots though to account for unforeseen changes in the limits, besides using up more of a user's quota of 20 bots per account, but if you have multiple accounts this shouldn't be an issue.

With user clients, even if 2 could be enough, their limits are somewhat more random and less predictable, and there's the point above of spreading the job amongst more of them so it's less likely any one of them gets banned, so the more the better.

Note that if you don't have enough bot clients but all the messages to be copied are media messages that can only be copied with user clients anyway, it could still slow down the process, because even if the bot's attempt to send the message fails with a MediaEmptyError, that attempt still counts towards its limit and gets it closer to receiving a floodwait. So when the messages being copied are all media messages that require an access hash, the bots don't end up copying any messages and all their attempts fail with MediaEmptyError. If a bot attempts to copy some message, then encounters a floodwait, but all other bots still have positive remaining floodwaits, then the script waits for one of the bots to finish its floodwait before switching to it to attempt to copy the same message, upon which it fails with MediaEmptyError and switches to a user client anyway. If you have enough bot clients to avoid floodwaits from them altogether (around 17 like I said), then the bot clients can at least avoid being a clearly noticeable hindrance to the process while the user clients do all the copying.

# The caption added to messages

Not all messages accept a text component, but those that do include text messages (obviously), videos, photos, documents. The script adds a caption to whichever message can have a text component. The caption consists of the following components:

- For every message, the first line of the caption is 'chat\_ID: ' followed by the ID of the source channel from which the message has been copied
- The second line is 'message\_ID: ' followed by the ID of the message in the source channel. If the message in the source chanel has been edited since it was first sent there, this is followed by ' (a\_previous\_message\_edited)'.
- The third line is 'date: ' followed by the date and time at which the message was sent in the source channel, except if the message has been edited since it was first sent, in which case it's the date and time at which the message was last edited instead of that at which it was first sent. The format of the date in both cases is 'YYYY-MM-DD hh:mm:ss UTC' with the time being given in UTC.
- If the message is a reply to a previous message, the next line is 'in\_reply\_to\_message\_ID: ' followed by the ID of the message to which it was a reply.
- If the message in the source channel had been forwarded from somewhere else, such that it had a 'Forwarded from: ' tag, then:
  - If the message was forwarded from an anonymous group admin, the next line is 'forwarded\_from\_chat\_ID: {ID} (supergroup)' where {ID} is the ID of the group from which it was forwarded
  - If the message was forwarded from a channel, the next line is 'forwarded\_from\_chat\_ID: ' followed by the ID of that channel, and the line after that is 'forwarded\_from\_message\_ID: ' followed by the ID of the original message in that channel
  - If the message is forwarded from an individual user, even if that original message was sent in a group rather than a private chat, then:
    - If the user allowed linking to their account in messages forwarded from them, the next line is 'forwarded\_from\_user\_ID: ' followed by the ID of the user
    - Otherwise, if the user didn't allow linking to their account in messages forwarded from them, the next line is 'forwarded\_from\_user\_name: ' followed by the name of the user, as it appears in the 'Forwarded from: ' tag
	
  The next line is then 'forwarded\_from\_message\_date: ' followed by the date and time at which the original message was sent in the chat from which it was forwarded to the source channel. The format of the date is likewise 'YYYY-MM-DD hh:mm:ss UTC' with the time being given in UTC.

The issue of the attributes of a forwarded message is still somewhat vague, so if none of the message attributes exist which are used to determine which of the above cases applies, the message is copied without this part of the caption, and a message is printed to the terminal which should provide relevant details to look into it if you wish.

If the message already has text, then two line breaks are inserted at the end, followed by the above caption. If the message doesn't already have text (e.g. a document with no caption), then the caption is inserted without being preceded by two line breaks.

This applies if the text a message already contains wouldn't exceed the limit if the caption was added to it. The limit is 4096 characters for text messages and 1024 characters for the caption of media messages. If it would exceed the limit, the message is instead copied without a caption added to it, and the caption is sent in a new message in reply to the copied message immediately afterwards.

# Handling FileReferenceExpiredError and MediaEmptyError with a user client

User clients can also receive a MediaEmptyError, if they aren't subscribed to the channel from which messages are being copied, so make sure they are before you start the script.

But I have also experienced user clients receiving a MediaEmptyError whilst the script is running and after they had already copied many messages without issue. The client then continues to receive it even as it retries sending the message again and again. It's still not clear what causes this, but the only solution I've found so far is to restart the script, after which that client is able to send that message without receiving the error.

When implementing a 2-second wait for the user client, I would receive a FileReferenceExpiredError after a while, presumably because the gap between having retrieved the message and attempting to send it was so long. This would presumably affect all messages thereafter as well. The solution for this was to retrieve the messages again, which could simply be done by restarting the script.

To handle both these errors, the script updates the CLONE\_STREAMS environment variable and the RUN environment variable, and then restarts. This is the point of the RUN environment variable, to keep track of how many times the script has restarted. It starts at 1 when first running the script, and increases by 1 every time the script restarts itself. Its value is printed in every log statement so you can tell from the log statements in the terminal how many times the script has restarted. The CLONE\_STREAMS environment variable is updated to start copying in the next run from wherever the script left off in this run.

# Other notes

If you cancel the script whilst it's running (e.g. using Ctrl+C), a message is output to the terminal giving the ID of the last copied message of the stream that was being copied at the time. Depending on when exactly you cancel the script, is a possibility that another message has successfully been copied, such that the ID output to the terminal is actually the ID of the penultimate message to have been copied, so you may want to confirm this yourself before using the ID output to the terminal to e.g. update the CLONE\_STREAMS environment variable for the next time you manually run the script to pick up where it left off.
