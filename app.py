from dotenv import load_dotenv
import logging
import os
import ast
from telethon import TelegramClient,errors
from telethon.sessions import StringSession
from datetime import timezone
from telethon.tl.types import MessageMediaWebPage,MessageService,KeyboardButtonUrlAuth,ReplyInlineMarkup
from telethon.tl.custom.button import Button
import time
import sys
import signal
import asyncio
#from textwrap import wrap
from character_limits import split_message

load_dotenv() #loading environment variables from .env file

run = os.environ.get("RUN") #indicating the number of times the script has been restarted (see restart() below)

logging.basicConfig(format='[%(asctime)s --- run {} --- %(filename)s line %(lineno)d --- %(levelname)s] --- %(message)s'.format(run), level=logging.INFO) #for detailed logging

str1 = os.environ.get("STREAMS") #loading the environment variable "STREAMS" to a variable str1
str2 = str1.split(";") #splitting at the semi-colons ; which is used as the separator between different streams
str3 = ["[" + x + "]" for x in str2] #enclosing each of the streams in square brackets
str4 = ','.join(str3) #joining the streams together, separated by commas
str5 = "[" + str4 + "]" #enclosing the entire thing in square brackets, which is relevant for correct recognition as a list of a list when there is only one stream
cs = ast.literal_eval(str5) #converting the string into an array
#print(cs)

str1 = os.environ.get("SESSION_STRINGS") #all of which are for user clients
str2 = str1.replace("\n","") #remove any line breaks
ss = str2.split(",") #session strings are separated from each other by a comma
#print(ss)

apiid = os.environ.get("API_ID")
apihash = os.environ.get("API_HASH")

l = list(range(len(ss))) #just to give it the right size
for b in l:
    l[b] = TelegramClient(StringSession(ss[b]),apiid,apihash,connection_retries=None,flood_sleep_threshold=0) #flood_sleep_threshold=0 so it doesn't automatically sleep for any floodwait errors
    l[b].parse_mode = None

str1 = os.environ.get("BOT_TOKENS")
str2 = str1.replace("\n","")
bts = str2.split(",")

b = list(range(len(bts)))
for f in b:
    b[f] = TelegramClient(None,apiid,apihash,connection_retries=None,flood_sleep_threshold=0)
    b[f].parse_mode = None

h = [[] for y in l] #initialise the lists of messages retrieved by each user client
async def main(i,s,j,user):
    '''client 'user' retrieves the messages to be copied for stream s'''
    fro,sid,eid = [*s[0:3]] #the chat from which messages are being copied, the ID of the first message to be copied, and the ID of the last message to be copied
    v = sid
    while True: #infinite looping; this is to try again after waiting out any floodwait error encountered
        await asyncio.sleep(0) #yield control to the event loop momentarily, allowing other tasks (e.g. copying over already-retrieved messages) to be run
        y = v #the first message to be retrieved in this iteration of the while loop has ID y
        try:
            async for q in user.iter_messages(fro,min_id=y-1,max_id=eid+1,wait_time=0,reverse=True): #iterating over the messages to be retrieved
                h[j].append(q) #append each retrieved message to the list of 'user'
                y = q.id #update y to the ID of the message just retrieved
                #logging.info(y)
        except errors.FloodWaitError as e:
            if y != v: #in which case it seems some successful iterations have just run so y has been updated to the ID of the last message retrieved by the user client, as opposed to if y==v, in which case the floodwait seems to have occurred upon attempting to retrieve the first message in the loop, so y is still the ID of the first message yet to be retrieved by this user client
                v = y+1 #so the next message for this user client to retrieve has ID y+1
            logging.info('FloodWait error encountered on user client {0} while retrieving messages of stream {1}; sleeping {2} seconds'.format(j+1,i+1,e.seconds))
            await asyncio.sleep(e.seconds)
            continue
        break #in which case the 'try' statement has completed execution without error, so break out of the while loop
    logging.info('user client {0} has retrieved all the messages of stream {1} ({2} in total)'.format(j+1,i+1,len(h[j])))
    h[j].append('finished') #to indicate there are no more messages to be retrieved for stream s by 'user'

def err_msgs(k,lid):
    """called when the messages at position k in the lists of messages don't all have the same ID (or aren't all 'finished')"""
    logging.info('It seems some of the messages to be copied of stream {0} might have been deleted whilst the user clients were retrieving them. Update the STREAMS environment variable and re-run the script if you still want to continue.'.format(i+1))
    logging.info('ID of last copied message of stream {0} = {1}'.format(i+1,lid[0]))
    for j,v in enumerate(h):
        if v[k] == 'finished':
            p = k-1
        else:
            p = k
        logging.info('The ID of the previous message of stream {0} retrieved by user client {1} was {2}'.format(i+1,j+1,v[p-1].id))
        logging.info('The ID of the this message (after which this error has appeared) of stream {0} retrieved by user client {1} was {2}'.format(i+1,j+1,v[p].id))
    sys.exit(0)

async def move(x,w,ct,t=None,f3=False):
    """To move to the next client, which is the client with the lowest remaining floodwait, or if 'f3=True' then the client with no remaining floodwait that maxxed out its counter longest ago
    """
    pl = [q[0] - (time.time() - q[1]) for q in w] #the remaining floodwaits of each client, negative values indicate there is no remaining floodwait for that client
    #the floodwaits of the clients in pl are in the same order as the order of the clients themselves in cl, so the index of a client in cl is equal to the index of its floodwait in cl (i.e. pl[idx]=cl[idx] for an index 'idx')
    #print(pl)
    kt = False #initialising it as False, possibly to be changed below
    pli = sorted(range(len(pl)), key=lambda i1: pl[i1]) #a list of the indices of the sorted elements of pl, from the index of the lowest element of pl to the index of the highest element of pl
    if f3: #if it must switch to a different client
        pli1 = [q for q,q2 in enumerate(pl) if q2 <= 0] #the indices of the clients with no remaining floodwait
        t1 = [t[q] for q in pli1] #for those clients with no remaining floodwait, the times when their counters last reached the maximum
        x[0] = pli1[t1.index(min(t1))] #the index of the client (with no remaining floodwait) whose counter last reached the maximum longest ago
    elif pli[0] == x[0]: #otherwise, if it need not switch to a different client, it can stay on the same client if it has the least remaining floodwait
        kt = True #to keep track of this being the case (that it's remaining on the same client)
    else:
        x[0] = pli[0] #switch to the client with the lowest remaining floodwait
    p = pl[x[0]] #the remaining floodwait
    if p > 0: #i.e. if the time passed since receiving the floodwait error is less than the time it was required to wait
        if kt: #if it's the same client as before, so no change in client has occurred
            logging.info('It has the least remaining floodwait of all the {0} clients; waiting {1} seconds to finish its floodwait then continuing with it'.format(ct[0],p))
        else: #if it's a different client to before
            logging.info('Waiting {0} seconds before switiching to {1} client {2}, to finish its floodwait'.format(p,ct[0],x[0]+1))
        await asyncio.sleep(p) #sleep the remaining amount of time before moving onto the next bot
    elif not f3: #if its floodwait has finished and it need not wait any longer
        logging.info('Switching to {0} client {1}'.format(ct[0],x[0]+1))

async def movec(c,m,t,x,w,ct):
    """to either increase the counter by 1 or move to the next client and reset the counter"""
    if c[0] == m: #if the counter has reached the maximum
        t[x[0]] = time.time() #the time when the counter has reached its maximum
        await move(x,w,ct,t,f3=True)
        c[0] = 1 #reset the counter for the next client
    else: #if it hasn't reached the maximum yet
        c[0] += 1

xu = [0] #x is the index of the current client to be used to copy messages in the list of clients (be it the list of user clients or the list of bot clients), set to 0 to start the process with the first client in the list
xb = [0]
#w is a list, each of its elements a 2-element list for each client, its 1st element being the required wait time for that client resulting from the most recent floodwait error it encountered, and its 2nd element being the time the client encountered that floodwait error
wu = [[0,0] for i in l] #initialising w as such to suitably handle the first round of floodwaits, when the next client in line hasn't had any floodwaits
wb = [[0,0] for i in b]
cu = [1] #c is used as a counter to keep track of how many messages the current client has set
cb = [1]
#t is a list containing, for each client, the most recent time when the counter of the number of messages the client has sent reached the maximum
tu = [0 for i in l]
tb = [0 for i in b]
#x and c above are intialised as single-element lists so that updates to x and c (see below) are reflected in them too
ct = ['bot']

sl = float(os.environ.get('SLEEP')) #the minimum amount of time the user client should wait between sending messages

cid = [0] #initialising the ID of the current message being copied
lid = [0] #initialising the ID of the last message to be successfuly copied

async def process_message(process,*args,**kwargs):
    #first try sending the message with the current bot client:
    ct[0] = 'bot'
    x = xb
    cl = b
    w = wb
    c = cb
    t = tb
    m = 5 #the maximum number of messages a bot client should send before moving onto a different bot client
    while True: #infinite looping; this is to try again for this message after handling any exceptions
        try:
            if process == 'send':
                #if 'reply_to' in kwargs:
                #    extra = 'caption of '
                #else:
                #    extra = ''
                #logging.info('attempting to copy {0}message {1} with {2} client {3}'.format(extra,cid[0],ct[0],x[0]+1))
                a = await cl[x[0]].send_message(*args,**kwargs)
                #logging.info('copied {0}message {1} with {2} client {3}'.format(extra,cid[0],ct[0],x[0]+1))
            elif process == 'edit':
                a = await cl[x[0]].edit_message(*args,**kwargs)
        except errors.FloodWaitError as e:
            te = time.time() #the current time at which the floodwait has occurred
            wait = e.seconds #the required wait time
            w[x[0]] = [wait,te]
            logging.info('FloodWait error of {0} seconds encountered on {1} client {2}'.format(w[x[0]][0],ct[0],x[0]+1))
            #logging.info('FloodWait error of {0} seconds encountered on {1} client {2} when trying to copy {3}message {4}'.format(w[x[0]][0],ct[0],x[0]+1,extra,cid[0]))
            await move(x,w,ct) #move to the next client
            c[0] = 1 #reset the counter to 1 for the next client
            continue #continue to the next iteration of the while loop
        except errors.rpcerrorlist.MediaEmptyError:
            if ct[0] == 'user': #if the client that's encountered the MediaEmptyError is a user
                logging.info('A MediaEmptyError was encountered with user client {0} when trying to send message {1}. Check that it has access to the source chat and/or check the media object.'.format(x[0]+1,cid[0]))
                logging.info('ID of last copied message of stream {0} = {1}'.format(i+1,lid[0]))
                restart(i,cid) #restart the script
            #logging.info('moving to user client to copy {0}message {1}'.format(extra,cid[0]))
            await movec(c,m,t,x,w,ct) #increment the counter for bot clients or move to the next bot client if it's reached the maximum
            #switch to user client
            ct[0] = 'user'
            x = xu
            cl = l
            w = wu
            c = cu
            t = tu
            m = 50
            await asyncio.sleep(sl)
            continue #to the next iteration of the while loop to try sending the message with a user client this time
        break
    await movec(c,m,t,x,w,ct) #increment the counter or move to the next client if it's reached the maximum
    return a

async def copy_message(message,to): #defining a function which is used repeatedly later in the code
    """copy the given message to the destination with the appropriate added text/caption"""
        
    if type(message.reply_markup) == ReplyInlineMarkup: #checking if the message has reply_markup and if so, then is it inline keyboard buttons
        #print(print(message.reply_markup.__dict__))
        for i in range(len(message.reply_markup.rows)): #iterating through each row of buttons
            #print(row.__dict__)
            for j in range(len(message.reply_markup.rows[i].buttons)): #iterating through the button in each row
                if type(message.reply_markup.rows[i].buttons[j]) == KeyboardButtonUrlAuth: #change any login urls to regular urls
                    #print(message.reply_markup.rows[i].buttons[j].__dict__)
                    #print(message.buttons[i][j].button.__dict__)
                    message.reply_markup.rows[i].buttons[j] = Button.url(text = message.reply_markup.rows[i].buttons[j].text, url = message.reply_markup.rows[i].buttons[j].url)
                    message.buttons[i][j].button = message.reply_markup.rows[i].buttons[j]
                    #print(message.reply_markup.rows[i].buttons[j].__dict__)
                    #print(message.buttons[i][j].button.__dict__)
        
    string = '\n\nchat_ID: ' + str(message.chat_id) + '\nmessage_ID: ' + str(message.id) #initialising the string to be added to the text/caption of the copied message
    if message.edit_date: #if the message is a previous message edited, then edit_date is the date of the most recent edit, which is what I want to output
        date = message.edit_date.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') #converts the date from UNIX time to a more readable format
        string += ' (a_previous_message_edited)' + '\ndate: ' + date
    else: #i.e. if the message is brand new
        date = message.date.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        string += '\ndate: ' + date
    if message.is_group: #if the message was sent in a group (including megagroups and gigagroups)
        if message.sender: #in which case the sender seems to be either a user/bot or a channel that's linked to the group
            string += '\nsender_ID: ' + str(message.sender_id)
        else: #in which case the sender seems to be an anonymous group admin
            string += '\nsender_ID: ' + str(message.chat_id) #i.e. just the ID of the group in which it's been sent
    if message.reply_to:
        string += '\nin_reply_to_message_ID: ' + str(message.reply_to.reply_to_msg_id)
    if message.fwd_from: #if this property exists, it indicates the message is forwarded
        fdate = message.fwd_from.date.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')   
        if message.forward._sender_id: #in which case I think the 'Forwarded from:' tag contains a user's or bot's name (even if their original message was sent in a group rather than a private chat) and if it's a user then they have allowed linking to their account when forwarding their messages
            string += '\nforwarded_from_user_ID: ' + str(message.forward._sender_id) + '\nforwarded_from_message_date: ' + fdate
        elif message.fwd_from.from_name: #in which case I think the 'Forwarded from:' tag contains a user's name (even if their original message was sent in a group rather than a private chat) and in this case the user didn't allow linking to their account when forwarding their messages
            string += '\nforwarded_from_user_name: ' + str(message.fwd_from.from_name) + '\nforwarded_from_message_date: ' + fdate
        elif message.forward._chat.megagroup or (hasattr(message.forward._chat,'gigagroup') and message.forward._chat.gigagroup): #Using hasattr for gigagroup because when dealing with an inaccessible channel (ChannelForbidden object) I got an AttributeError when using just 'if message.forward._chat.gigagroup' as the object didn't have the 'gigagroup' attribute
            string += '\nforwarded_from_chat_ID: ' + '-100' + str(message.fwd_from.from_id.channel_id) + ' (supergroup)\nforwarded_from_message_date: ' + fdate #it seems the message is forwarded from an anonymous group admin
        elif message.fwd_from.from_id.channel_id: #in which case, with neither ._chat.megagroup nor ._chat.megagroup being 'true, I think it's forwarded from a channel, in which case the ID of the original message is also accessible
            string += '\nforwarded_from_chat_ID: ' + '-100' + str(message.fwd_from.from_id.channel_id) + '\nforwarded_from_message_ID: ' + str(message.forward.channel_post) + '\nforwarded_from_message_date: ' + fdate
        else:
            logging.info("This message has the `.fwd_from attribute` but none of `.forward._sender_id`, `.fwd_from.from_name`, `.forward._chat.megagroup`, `.forward._chat.gigagroup` or `.fwd_from.from_id.channel_id` attributes. I'm not adding the 'Forwarded from:' part of the caption to it; look into it. Here it is printed out:")
            print(message)
            logging.info('and here is message.forward:')
            print(vars(message.forward))    
    
    
    '''
    n = False #maximum no. characters of the text part of the message (either 4096 or 1024), only relevant for those over the limit
    if message.media:
        if type(message.media) == MessageMediaWebPage: #a media type, but not subject to the 1024 character restriction
            if len(message.message + string) <= 4096: #to ensure it doesn't go above the limit for text messages, which I think is 4096 characters
                message.message += string #adding the above string to the text of the message
                a = await process_message('send',to,message) #copy the message (not forward) to the destination chat
            else: #if the combined string would be over the limit for text messages, send the message without the added string and send the string as a reply to it
                a = await process_message('send',to,message)
                n = 4096
                #await process_message('send',to,string[2:],reply_to=a) #remove the line breaks at the beginning of the above string, as it's not being added to previously existing text so nothing to separate it from
        elif message.message: #media that already has a caption
            if len(message.message + string) <= 1024: #to ensure it doesn't go above the limit for captions on media messages, which I think is 1024 characters
                message.message += string #adding the above string to the caption of the message
                a = await process_message('send',to,message)
            else:
                a = await process_message('send',to,message)
                n = 1024
                #await process_message('send',to,string[2:],reply_to=a)
        else: #if it doesn't already have a caption, make the above string its caption
            message.message = string[2:]
            a = await process_message('send',to,message)
    else:
        if len(message.message + string) <= 4096:
            message.message += string
            a = await process_message('send',to,message) 
        else:
            a = await process_message('send',to,message)
            n = 4096
            #await process_message('send',to,string[2:],reply_to=a)
    '''    
    
    #first, determine the max no. characters of the text part of the message, depending on message type. Premium users may have higher character limits than free-tier users, so the limits below assume a free-tier and allow copying a message with Premium character length
    media_limit = 1024
    text_limit = 4096
    if message.media:
        if type(message.media) == MessageMediaWebPage: #a media type, but with a text limit equal to that of regular text messages
            n = text_limit
        else: #for all other media types, their caption limit:
            n = media_limit
    else: #just a regular text message
        n = text_limit
    #print(message)
    if message.message: #a text message, or media message that already has a caption
        if len(message.message) > n: #if the length of the text part of the messages exceeds the limit for free users ...
            logging.info('splitting message {0} of chat {1}'.format(message.id,message.chat_id))
            #t1 = time.time()
            lmsgs = split_message(message.message,message.entities,n) #split the text part of the message into parts less than n characters in length, avoiding splitting apart words or formatting entities where possible; the result is a list of strings with the formatting entities applicable to them
            #t2 = time.time()
            #print('time elapsed:',t2-t1)
        else: #just for consistency in the code, setting this
            lmsgs = [[message.message,message.entities]]
        if len(lmsgs[-1][0] + string) <= text_limit: #add the above string to the last element of lstrings if within the limit
            lmsgs[-1][0] += string
        else: #send the above string separately
            lmsgs.append([string[2:],None])
    else: #a media message with no caption
        lmsgs = [[string[2:],message.entities]]
    message.message,message.entities = lmsgs[0][0],lmsgs[0][1] #make the first element of lmsgs part of the message object, the rest to be sent separately; this may be the only (and hence also last) element of lmsgs if everything was within the limit
    a = await process_message('send',to,message) #copy the message (not forward) to the destination chat
    if message.buttons and ct[0] == 'user': #if the message was copied by a user, then it was copied without its buttons ...
        await process_message('edit',a,buttons=message.buttons) #... so add them on using a bot client
    for text in lmsgs[1:]: #copy the rest of the strings as text messages in reply to the previous one, formatted with their entities; loop has zero iterations if lmsgs had only one element
        a = await process_message('send',to,text[0],reply_to=a,formatting_entities=text[1])

    #The below works just fine when ignoring formatting entities, not otherwise:
    """
    if message.message: #a text message, or media message that already has a caption
        lstrings = wrap(message.message,n,break_on_hyphens=False,expand_tabs=False,replace_whitespace=False) #split the text part of the message into parts below n characters, without splitting single words apart
        if len(lstrings[-1] + string) <= n: #add the above string to the last element of lstrings if within the limit
            lstrings[-1] += string
        else: #send the above string separately
            lstrings.append(string[2:])
    else: #a media message with no caption
        lstrings = [string[2:]] #make the above string its caption; removing the initial line breaks but may not be necessary as Telegram strips the text server-side anyway
    #print(len(lstrings))
    #print(lstrings)
    message.message = lstrings[0] #make the first element of lstrings the text of the message, the rest to be sent separately; this may be the only (and hence also last) element of lstrings if everything was within the limit
    a = await process_message('send',to,message) #copy the message (not forward) to the destination chat
    if message.buttons and ct[0] == 'user': #if the message was copied by a user, then it was copied without its buttons ...
        await process_message('edit',a,buttons=message.buttons) #... so add them on using a bot client
    for sstring in lstrings[1:]: #copy the rest of the strings as text messages in reply to the previous one; loop has zero iterations if lstrings had only one element
        a = await process_message('send',to,sstring,reply_to=a,formatting_entities=None)
    """
    
    '''
    if n:
        lstrings = wrap(message.message,n,break_on_hyphens=False)
        if len(lstrings[-1] + string) <= n:
            lstrings[-1] += string
        else:
            lstrings.append(string[2:])
        for sstring in lstrings:
            a = await process_message('send',to,sstring,reply_to=a)
    '''


def restart(i,ID):
    """to restart the script"""
    cs[i][1] = ID #update the ID of the first message to be copied in this stream when the script restarts
    cs1 = [[str(u) for u in x] for x in cs[i:]]
    cs2 = [','.join(x) for x in cs1]
    str1 = ';'.join(cs2)
    os.environ["STREAMS"] = str1 #update the STREAMS environment variable, removing all streams which have been copied over in this run of the script
    os.environ["RUN"] = str(int(run) + 1) #increment the run of the script by 1
    os.execv(sys.executable, ['python3'] + sys.argv) #restart the script

async def main1(i,s):
    #await b[0].send_message(-1001506400182,'--------')
    #sys.exit(0)
    for j,user in enumerate(l):
        asyncio.create_task(main(i,s,j,user)) #all user client concurrently start retrieving the messages to be copied
    lid[0] = 0 #the ID of the last copied message; initialised as 0 to indicate no message has been copied yet
    #to handle cases where the script is cancelled before finishing with all messages:
    def cancel(sig,frame):
        logging.info('ID of last copied message of stream {0} = {1}'.format(i+1,lid[0]))
        sys.exit(0)
    signal.signal(signal.SIGINT, cancel)
    k = 0 #the index of the next item to be considered in the lists of messages
    while True: #infinite looping; to continue checking whether the 'if' statement below is satisfied as the lists of messages continue to get updated with newly retrieved messages
        await asyncio.sleep(0) #yield control to the event loop momentarily, allowing other tasks (e.g. retrieving the rest of the messages) to be run
        #print(k)
        if k < min([len(v) for v in h]): #only proceed if each user client has retrieved enough messages for its list to be long enough to have an item with index k
            lif1 = [v[k] for v in h] #the item with index k in the list of each user client, for all user clients
            if 'finished' in lif1: #indicating that at least one of the user clients has finished retrieving all messages
                if len(set(lif1)) == 1: #the items with index k should be 'finished' in all the lists
                    logging.info('All messages of stream {0} have been copied.'.format(i+1)) #in which case the previous value of k was the final message to be copied, which has been done
                    break #so break out of the while loop here
                #next line is only executed when the 'if' statement isn't true because of 'break', so no need for 'else'
                #if the items aren't all 'finished', then the final message(s) to be retrieved may have been retrieved by some of the user clients and then deleted before the other user clients could retrieve it, so the lists of the latter clients 'finished' at an earlier position than the lists of the former clients, so...
                err_msgs(k,lid) #...terminate the script
            #otherwise, if none of the items are the string 'finished' then they are all Message objects...
            lif = [v[k].id for v in h] #...so this is a list of their IDs...
            if len(set(lif)) != 1: #...which should all be the same, otherwise the item may be a message that was retrieved by some user clients and then deleted before the other user clients could retrieve it, so...
                err_msgs(k,lid) #...terminate the script
            #if all the items with index k are Message objects with the same ID, then proceed to copy that message
            to = s[3] #the destination chat
            msg = h[xu[0]][k] #the message is retrieved from list of the current user client to copy messages
            cid[0] = msg.id #thd ID of the current message to be copied
            if not type(msg) == MessageService: #as it seems services messages (like a message being pinned, a channel name or photo being changed, etc) can't be copied
                try:
                    await copy_message(msg,to) #copying the message to the destination chat
                    lid[0] = msg.id #if the message was copied without error, this line runs to update the ID of the last copied message
                except errors.rpcerrorlist.FileReferenceExpiredError:
                    logging.info('FileReferenceExpiredError encountered on message {}'.format(msg.id))
                    restart(i,msg.id) #restart the script
                    #await asyncio.sleep(2)
                    continue
                #logging.info('successfully copied message {0} with {1} client {2}'.format(msg.id,ct[0],x[0]+1))
                if p2f:
                    print('',file=file) #a blank line to separate messages
                    print(msg,file=file) #print the message to the file
                #asyncio.sleep(1)
            k += 1

li = []
async def start_clients():
    for user in l: #starting all user clients concurrently
        a = asyncio.create_task(user.start())
        li.append(a)
    for i,bot in enumerate(b): #starting all bot clients concurrently
        a = asyncio.create_task(bot.start(bot_token=bts[i]))
        li.append(a)
    for task in li: #wait until all the clients have finished starting
        await task
    #alternatively (I think it should work):
    #await asyncio.gather(*[*[user.start() for user in l],*[bot.start(bot_token=bts[i]) for i,bot in enumerate(b)]])
l[0].loop.run_until_complete(start_clients())

if os.environ.get("PRINT_TO_FILE") == '1':
    p2f = True
    with open('msgs.txt','a+',encoding='utf-8') as file:
        for i,s in enumerate(cs): #copying the streams successively, one after the other, in the order given in the environment variable
            b[0].loop.run_until_complete(main1(i,s))
            h = [[] for y in l] #re-initialising the array h to be populated by the messages of the next stream
else:
    p2f = False
    for i,s in enumerate(cs): #copying the streams successively, one after the other, in the order given in the environment variable
        b[0].loop.run_until_complete(main1(i,s))
        h = [[] for y in l] #re-initialising the array h to be populated by the messages of the next stream
