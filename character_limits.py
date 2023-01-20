import string

def split_message(s,original_entities,limit,text_limit):
    
    #s = ' a b c\nd e f'
    
    def func(n,start): #calculate the break point for a given character limit n minding word breaks
        if n==len(s): #the maximum break point is the end of the string, so if that's where the limit is then just return that
            return len(s)
        if s[n].isspace(): #if the nth character is immediately followed by a whitespace
            return n
        if start==0:
            ss = s[n-1::-1]
        else:
            ss = s[n-1:start-1:-1] #go to the limiting character of the string, then working backwards from it ...
        ps = [ss.find(x) for x in string.whitespace] #... find the positions of the nearest whitespaces (of different types)
        #print(ps)
        psp = [num for num in ps if num>=0] #removing the -1s for those types of whitespace that aren't present in the string
        if not psp: #if there are no whitespaces present
            return start
        val = min(num for num in ps if num>=0) #the index nearest type of whitespace
        #print(val)
        return n-val + start
    
    #limit=offset+length
    """
    original_entities = [{'offset':900,'length':1010-900},
                {'offset':1000,'length':1100-1000},
                {'offset':1700,'length':2100-1700},
                {'offset':2000,'length':2170-2000},
                {'offset':2500,'length':2600-2500}]
    """
    
    if not original_entities: #just in case there are no entities such that original_entities is just None
        original_entities = [] #turn it into an empty iterable for the code below to work
    
    results = []
    b = 0 #this is the index position of the character just before which to break the string
    while b < len(s):
        start = b #start at break point of previous iteration (start initially at zero, hence why b was initialised as such)
        entities = [x for x in original_entities if x.offset >= start] #exclude the entities that can't lie within the boundaries of this iteration's resulting substring
        if results: #the messages after the first would all be text messages without media parts, so subject to the character limit of text messages not media messages, so if the first message has already been generated, switch the limit to that of text messages if it isn't already
            lim = text_limit
        else:
            lim = limit
        n0 = min(lim + start, len(s)) #the index position at which the substring would be at maximal length if broken there, or the end of the string if we hit that
        n = n0 #the index position at which the substring is of maximal length without cutting entities apart (if possible, which we haven't calculated yet, so intially just same as n0)
        b = func(n,start) #the index position at which the substring is of maximal length without cutting entities of words apart (if possible)
        ents = [] #to contain the formatting entities that apply to the resulting substring of this iteration
        #leftovers = []
        j = 0 #start inspecting from first entity
        while j < len(entities):
            if entities[j].offset < b: #in which case it either lies within b ...
                ents.append(entities[j]) #... so it's formatting that applies to some of the text within the substring, so add it to ents ...
                if entities[j].offset+entities[j].length > b: #... or b cuts through it, in which case start again after ...
                    n = entities[j].offset #... adjusting the limit to just before this entity begins so it's no longer a problem ...
                    b = func(n,start) #... and calcuating the corresponding b
                    entities = ents + entities[j+1:] #exclude the entities that we know aren't relevant by including those we found to lie within old b and those that weren't inspected, as the rest are known to start beyond old b so they will certainly start beyond the new b
                    ents = []
                    j = 0
                    continue
            j += 1
        if b==start: #the entire region from start to n0 is covered in formatting entities at least some of have a limit beyond n0
            ents = []
            b = func(n0,start) #so give up sticking to only boundaries of formatting regions and just make the boundary at the nearest whitespace to the character limit instead, cutting through the formatting regions
            if b==start: #the entire region from start to n0 doesn't have any whitespaces
                b = n0 #so also give up sticking to only word boundaries and just make the boundary at th elimit itself instead, breaking apart these strings of consecutive non-whitespace characters
            for entity in original_entities: #entity is mutable so original_entities gets modified when entity gets modified (not when it gets re-assigned)
                if entity.offset < b: #in which case this formatting applies to at least some of the text
                    if entities[j].offset+entity.length > b: #in which case it's an entity to be broken apart
                        ent = entity.copy()
                        entity.offset = b #modify original_entities for the next iteration, as the second half of the split entity goes to the next substring
                        ent.length = b-entities[j].offset #the first half of the split entity
                        entity = ent
                        #ent = entity.copy()
                        #leftovers.append(ent)
                        #entity['limit'] = b
                    ents.append(entity)
        #print(b,ents)
        results.append([start,b,ents]) #from where to start the string slice, where to break it, and the entities associated with it to be sent along with it in a message
        #print(original_entities)
        #for ent in leftovers:
        #    ent['offset'] = start
        #    entities.append(ent)
    
    string_results = [] #evaluating the new split strings
    for result in results:
        sub = s[result[0]:result[1]] #the string for this result
        #setting 'start' as the zero-point of the offset of each entity:
        nents = []
        for ent in result[2]:
            ent.offset -= result[0]
            nents.append(ent)
        string_results.append([sub,nents])
    
    return string_results

    #old outline of rough alternative for the first break point:
    """
    entities = original_entities
    ents = []
    entities0 = ents
    n0 = 1024
    n = n0
    while True:
        originaln = n
        b = func(n)
        if b==0: #then formatting region exceeds originaln0 so just split the formatting entities
            b = func(n0)
            ents = entities0
            for i in range(entities):
                if ents[i]['limit'] > b:
                    ents[i]['limit'] = b #this is the splitting of the entity
            break
        for entity in entities:
            if entity['offset'] < b:
                ents.append(entity)
                if entity['limit'] > b:
                    n = entity['offset']
    
        if n == originaln:
            break
        entities = ents
        ents = []
        #print(n,entities)
    print(b,ents)
    """
