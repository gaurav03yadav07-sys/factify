#!/usr/bin/env python
# coding: utf-8

# In[2]:


import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# In[3]:


try:
    stopwords.words("english")
except:
    nltk.download("punkt")
    nltk.download("stopwords")
    nltk.download("wordnet")
    nltk.download("omw-1.4")

STOPWORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()


# In[4]:


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'http\S+', ' ', text)            # remove URLs
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)        # remove non-letters
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens]
    return " ".join(tokens)


# In[5]:




# In[ ]:




