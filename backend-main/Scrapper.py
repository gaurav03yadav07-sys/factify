#!/usr/bin/env python
# coding: utf-8

# In[1]:


from newspaper import Article
from bs4 import BeautifulSoup
import requests


# In[2]:


def extract_article_text(url: str) -> str:
    # Try newspaper3k first
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        if text and len(text.strip()) > 100:
            return text
    except Exception:
        pass

    # Fallback: requests + BeautifulSoup (basic)
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        # try to get <article> tag content
        article_tag = soup.find("article")
        if article_tag:
            text = article_tag.get_text(separator=" ", strip=True)
        else:
            # fallback to concatenation of <p> tags
            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text(separator=" ", strip=True) for p in paragraphs])
        if text and len(text.strip()) > 100:
            return text
    except Exception:
        pass

    # If nothing extracted, return empty
    return ""

