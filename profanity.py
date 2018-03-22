
file = open('prof_list.txt', 'r')
words = list(file.read().split())

def is_bad_word(word):

    file = open('blocked_prof_list.txt','r')
    new_words = list(file.read().split())
    words.extend(new_words)
    if word.upper() in (name.upper() for name in words):
        return True
    else:
        return False

def add_bad_word(word):
    file = open('blocked_prof_list.txt','a')
    file.write(str(word)+'\n')

    file = open('prof_list.txt', 'a')
    file.write(str(word)+'\n')
