import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from utils import clean_text

df = pd.read_csv("ml/data/resume_dataset.csv")

df['cleaned'] = df['resume_text'].apply(clean_text)

X = df['cleaned']
y = df['category']

tfidf = TfidfVectorizer(max_features=3000)
X_vec = tfidf.fit_transform(X)

model = LogisticRegression()
model.fit(X_vec, y)

pickle.dump(model, open("ml/model/model.pkl", "wb"))
pickle.dump(tfidf, open("ml/model/tfidf.pkl", "wb"))

print("Model trained and saved!")