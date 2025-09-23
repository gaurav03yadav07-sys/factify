#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sqlite3
from datetime import datetime
from typing import Optional


# In[2]:


DB_PATH = "queries.db"


# In[3]:


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        label TEXT,
        confidence REAL,
        extracted_len INTEGER,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


# In[4]:


def log_query(url: str, label: str, confidence: float, extracted_len: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO queries (url,label,confidence,extracted_len,created_at) VALUES (?, ?, ?, ?, ?)",
              (url, label, confidence, extracted_len, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


# In[ ]:




