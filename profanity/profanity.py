
file = open('profanity/prof_list.txt', 'r')
words = list(file.read().split())

def is_bad_word(word):


   for name in words:
      for w in word.split():
         if name.upper() == w.upper():
            return True
   """
   ##################   Substring level checking ##########################
   count=0
   for name in words:
      count +=1
      if name.upper() in word.upper():
         print("Matched at count :",count,name.upper(),word.upper())
         return True

	###########################################
   """


   return False

def add_bad_word(word):
    file = open('profanity/blocked_prof_list.txt','a')
    file.write(str(word)+'\n')
    words.extend(word.split())
    file = open('profanity/prof_list.txt', 'a')
    file.write(str(word)+'\n')

def all_blocked_word():
    words = list(file.read().split())
    return words
