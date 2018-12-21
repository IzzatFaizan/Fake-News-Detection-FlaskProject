import pandas as pd
import logging
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import model_selection, preprocessing, metrics
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# database connection
conn = mysql.connector.connect(host='127.0.0.1', user='root', password='', database='news')
cursor = conn.cursor()
cursor.execute("SELECT * from news")
content = cursor.fetchall()

# load the dataset
labels, texts = [], []

for row in content:
    texts.append(row[2])
    texts.append(row[3])

for i in range(239):
    labels.append('Fake')
    labels.append('Real')

# create a dataframe using data and label
trainDF = pd.DataFrame()
trainDF['text'] = texts
trainDF['label'] = labels

# split the dataset into training and validation datasets
train_x, valid_x, train_y, valid_y = model_selection.train_test_split(trainDF['text'], trainDF['label'], shuffle=False,
                                                                      test_size=0.25)

# label encode the target variable
encoder = preprocessing.LabelEncoder()
train_y = encoder.fit_transform(train_y)
valid_y = encoder.fit_transform(valid_y)

# characters level tf-idf
tfidf_vect_ngram_chars = TfidfVectorizer(analyzer='char', token_pattern=r'\w{1,}', ngram_range=(2, 3),
                                         max_features=5000)
tfidf_vect_ngram_chars.fit(trainDF['text'])
xtrain_tfidf_ngram_chars = tfidf_vect_ngram_chars.transform(train_x)
xvalid_tfidf_ngram_chars = tfidf_vect_ngram_chars.transform(valid_x)

# SVM on Character Level TF IDF Vectors
# svm_model = svm.SVC(kernel='linear', C=1.0, gamma='auto')
text_clf = Pipeline(memory=None,
                    steps=[('clf', LinearSVC(C=1.0, class_weight=None, dual=True, fit_intercept=True,
                                             intercept_scaling=1, loss='squared_hinge', max_iter=1000,
                                             multi_class='ovr', penalty='l2', random_state=None, tol=0.0001,
                                             verbose=0))])


def train_model(classifier, feature_vector_train, label, feature_vector_valid):
    # fit the training dataset on the classifier
    req = classifier.fit(feature_vector_train, label)
    print("Train Accuracy : ", req.score(feature_vector_train, label))
    parameters = {'vect__ngram_range': [(1, 1), (1, 2)],
                  'tfidf__use_idf': (True, False),
                  'clf__alpha': (1e-2, 1e-3)}

    gs_clf = GridSearchCV(text_clf, parameters, n_jobs=-1, cv=5)
    gs_clf = gs_clf.fit(feature_vector_train, label)

    print(gs_clf.best_score_)
    print(gs_clf.best_params)

    # predict the labels on validation dataset
    predictions = classifier.predict(feature_vector_valid)
    print(confusion_matrix(valid_y, predictions))
    print(classification_report(valid_y, predictions))

    return metrics.accuracy_score(predictions, valid_y)


# Print Accuracy
accuracy = train_model(text_clf, xtrain_tfidf_ngram_chars, train_y, xvalid_tfidf_ngram_chars)
print("Test Accuracy : ", accuracy)