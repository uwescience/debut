#LSTM with dropout for sequence classification in the IMDB dataset
import numpy
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
import sklearn.metrics
import load_data
# fix random seed for reproducibility
numpy.random.seed(7)
# load the dataset but only keep the top n words, zero the rest
top_words = 5000
(X_train, y_train), (X_test, y_test) = load_data.load_data(nb_words=top_words)
# truncate and pad input sequences
max_review_length = 100
X_train = sequence.pad_sequences(X_train, maxlen=max_review_length)
X_test = sequence.pad_sequences(X_test, maxlen=max_review_length)
X_train = numpy.expand_dims(X_train, axis=-1)
X_test = numpy.expand_dims(X_test, axis=-1) 
# create the model
embedding_vector_length = 32
model = Sequential()
# To use the embedding code they have, uncomment the next line and remove the batch_input_shapepart of the next line. Note that this is NOT the CCA embedding we created, although we could write code to change this so it did use those embeddings.
#model.add(Embedding(top_words, embedding_vector_length, input_length=max_review_length, dropout=0.2))
model.add(LSTM(1000, dropout_W=0.2, dropout_U=0.2, batch_input_shape=(None, max_review_length, 1)))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
print(model.summary())
model.fit(X_train, y_train, nb_epoch=1, batch_size=64)#, validation_split=0.1)
# Final evaluation of the model
scores = model.evaluate(X_test, y_test, verbose=0)
ypred_pr = model.predict_proba(X_test)
# measure quality of prediction
auc = sklearn.metrics.roc_auc_score(y_test, ypred_pr[:,-1])

print("Accuracy: %.2f%%" % (scores[1]*100))
print("Auc: ", auc)
