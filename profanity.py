
file = open('prof_list.txt', 'r')
words = list(file.read().split())

def is_bad_word(word):
    """
    for second in (name.upper() for name in words):

        print("Word :",word,"Second :",second)
        if  (second == word.upper()) or (word.upper() in second) or (second in word.upper()):
            print("returning True")
            return True
    """
    count=0
    for name in words:
        count +=1
        if name.upper() in word.upper():
            print("Matched at count :",count,name.upper(),word.upper())
            return True
    return False

def add_bad_word(word):
    file = open('blocked_prof_list.txt','a')
    file.write(str(word)+'\n')
    words.extend(word.split())
    file = open('prof_list.txt', 'a')
    file.write(str(word)+'\n')

def all_blocked_word():
    words = list(file.read().split())
    return words
