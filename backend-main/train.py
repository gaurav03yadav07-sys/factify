#!/usr/bin/env python
# coding: utf-8

# In[33]:


import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from preprocess import clean_text


# In[34]:


MODEL_DIR = "model_artifacts"
os.makedirs(MODEL_DIR, exist_ok=True)


# In[35]:


def load_dataset(path="fake_news.csv"):
    df = pd.read_csv(path)
    # assume df has 'text' and 'label' columns
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str)
    return df


# In[38]:


def preprocess_and_train(path="fake_news.csv"):
    df = load_dataset(path)
    df["clean_text"] = df["text"].apply(clean_text)

    X = df["clean_text"]
    y = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1,2), min_df=3)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print("Vectorized shapes:", X_train_tfidf.shape, X_test_tfidf.shape)

    # Quick grid search for C
    param_grid = {"C":[0.1, 1, 3, 10]}
    lr = LogisticRegression(max_iter=5000, class_weight="balanced", solver="liblinear")
    grid = GridSearchCV(lr, param_grid, cv=3, scoring="f1", n_jobs=-1)
    grid.fit(X_train_tfidf, y_train)
    best = grid.best_estimator_
    print("Best params:", grid.best_params_)

    y_pred = best.predict(X_test_tfidf)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Classification report:\n", classification_report(y_test, y_pred))

    # Save artifacts
    joblib.dump(vectorizer, f"{MODEL_DIR}/vectorizer.joblib")
    joblib.dump(best, f"{MODEL_DIR}/model.joblib")
    print("Saved model and vectorizer to", MODEL_DIR)

if __name__ == "_main_":
    preprocess_and_train()


# In[ ]:




