**1.Initial Setup**
"""

!pip install tensorflow transformers
!pip install tf-keras

"""**2. Importing Libraries**"""

# To finetune transformer model, we need following libraries
import tensorflow as tf
from tensorflow.keras import activations, optimizers, losses
from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification

# To save our trained model, we import pickle library
import pickle

# To pre-process, we need following libraries
import pandas as pd
import numpy as np
import seaborn as sns

# To explre and visualize data, we need following libraries
import matplotlib.pyplot as plt
import plotly.express as px

"""**3. Data Loading**"""

# To upload the data from file
from google.colab import files
uploaded= files.upload()
print(uploaded)

import pandas as pd
df = pd.read_csv('/content/amazon_alexa.tsv', sep='\t')

df.head()

"""**4. Data Exploration**"""

df['feedback'].value_counts()

"""**Visualization:**"""

# Plot count of feedback
import plotly.express as px

df_plot = df.groupby(by=['feedback']).size().reset_index(name='count')
px.bar(df_plot, x='feedback', y='count')

"""**5. Data Balancing**
(Separate and balance the dataset:)
"""

# Create a dataframe with only negative reviews
df_negative=df[df['feedback']==0]
# Create a dataframe with only positive reviews
df_positive=df[df['feedback']==1]

# Check number of rows of negative reviews
df_negative.shape[0]

# Down sample positive reviews to match number of negative reviews
df_positive_downsampled=df_positive.sample(df_negative.shape[0])
df_positive_downsampled.shape

# Create a balanced dataset of equal number of positive and negative reviews
df_balanced=pd.concat([df_positive_downsampled,df_negative],axis=0)
df_balanced.shape

# Check the review distribution
df_plot=df_balanced.groupby(by=['feedback']).size().reset_index(name='count')
px.bar(df_plot,x='feedback',y='count')

""" **[6. Text Preprocessing](https://)**(This code calculates and adds a new column review_length to measure how many words are in each review.)"""

df_balanced['review_length'] = df_balanced['verified_reviews'].apply(lambda x: len(str(x).split()) if isinstance(x, str) else 0)

df_balanced.shape

"""Visualize review lengths:"""

fig=px.histogram(df_balanced['review_length'],title='Review Length')
fig.show()

# Converting dataframe series object into list
x=df_balanced['verified_reviews'].to_list()
x[0:5]

# Converting dataframe series object into list
y=df_balanced['feedback'].to_list()
y[0:5]

"""**7. Tokenization**(Prepare the text for model input:)"""

from transformers import DistilBertTokenizer

# Initialize tokenizer
MODEL_NAME = 'distilbert-base-uncased'
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

# Ensure x is a list of strings
x = df_balanced['verified_reviews'].astype(str).tolist()

# Fixed function (corrected 'trucation' to 'truncation')
def construct_encodings(x, tokenizer, max_len, truncation=True, padding=True):
    return tokenizer(x, max_length=max_len, truncation=truncation, padding=padding)

# Generate encodings
encodings = construct_encodings(x, tokenizer, max_len=50)

"""**8. Dataset Creation**"""

import tensorflow as tf
def construct_tfdataset(encodings, y=None):
    if y:
        return tf.data.Dataset.from_tensor_slices((dict(encodings),y))
    else:
        # this case is used when making predictions on unseen samples after training
        return tf.data.Dataset.from_tensor_slices(dict(encodings))

tfdataset = construct_tfdataset(encodings, y)

"""**9. Train-Test-Validation Split**"""

# All these are hyper-parameters
TEST_SPLIT = 0.2
VAL_SPLIT=0.2
BATCH_SIZE = 32

# Initial training size
train_size = int(len(x) * (1-TEST_SPLIT))
val_size=int(len(x) * (VAL_SPLIT))

# At this step, we're only declaring the train & test size
print('Initial Train size is: ',train_size)
print('Test size is: ',int(len(x) * (TEST_SPLIT)))
print('Validation size is: ',val_size)

# Shuffling
tfdataset = tfdataset.shuffle(len(x)) # randomly shuffles dataset across dimension of x tensor vector

# Testing data: tfdataset.skip(3) --> will skip inital 3 rows from the dataset. So tfdataset.skip(train_size) will skip initial 411 rows and keep remaining 102 into tfdataset_test
tfdataset_test = tfdataset.skip(train_size)

# Remaining data: tfdataset.take(3) --> will take first 3 rows from the dataset. So tfdataset.take(train_size) will store first 411 rows into tfdataset_rest
tfdataset_rest = tfdataset.take(train_size)

# Now we will split tfdataset_rest into train and validation datasets using val_size=51
tfdataset_train=tfdataset_rest.skip(val_size)
tfdataset_val=tfdataset_rest.take(val_size)

print('Train size is: ',len(tfdataset_train))
print('Test size is: ',len(tfdataset_test))
print('Validation size is: ',len(tfdataset_val))

# tfdataset_train.batch creates batches of the data, each batch having number of samples equal to the batch size
tfdataset_train = tfdataset_train.batch(BATCH_SIZE)
tfdataset_val = tfdataset_val.batch(BATCH_SIZE)
tfdataset_test = tfdataset_test.batch(BATCH_SIZE)

print('Number of batches of Training data: ',len(tfdataset_train))
print('Number of batches of Testing data: ',len(tfdataset_test))
print('Number of batches of Validation data: ',len(tfdataset_val))

"""**10. Model Creation**"""

# Import required libraries
import tf_keras as keras  # Use tf_keras instead of tf.keras
import tensorflow as tf
from transformers import TFDistilBertForSequenceClassification

# Constants
N_EPOCHS = 10  # Number of training epochs
MODEL_NAME = 'distilbert-base-uncased'

# Load the pre-trained DistilBERT model
model = TFDistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    from_pt=False,  # Ensure loading in TensorFlow format
    num_labels=2    # Set number of labels for classification
)

# Define the optimizer and loss
optimizer = keras.optimizers.Adam(learning_rate=3e-5)
loss = keras.losses.SparseCategoricalCrossentropy(from_logits=True)

# Compile the model
model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])
model.summary()

"""**11. Model Training**"""

# Train Model
history=model.fit(tfdataset_train, batch_size=BATCH_SIZE, epochs=N_EPOCHS,validation_data=tfdataset_val,verbose=1)

"""Visualize training history:"""

import matplotlib.pyplot as plt

def plot_metric(history,metric):
    training_metrics=history.history[metric]
    validation_metrics=history.history['val_'+metric]
    epochs=range(1,len(training_metrics)+1)
    plt.plot(epochs,training_metrics)
    plt.plot(epochs,validation_metrics)
    plt.title('Training and Validation '+metric)
    plt.xlabel("Number of Epochs")
    plt.ylabel(metric)
    plt.ylim([0,1.5])
    plt.legend(["training_"+metric, 'validation_'+metric])
    plt.show()

plot_metric(history, 'loss')

"""**12. Model Evaluation**"""

# Using moedl.evaluate() we test the model performance on unseed data which is stored in tfdataset_test
benchmarks = model.evaluate(tfdataset_test, return_dict=True, batch_size=BATCH_SIZE,verbose=1)
print(benchmarks)

"""**13. Making Predictions**"""

def create_predictor(model, model_name, max_len):
  tokenizer = DistilBertTokenizer.from_pretrained(model_name)
  def predict_proba(text):
      x = [text]

      encodings = construct_encodings(x, tokenizer, max_len=max_len)
      tfdataset = construct_tfdataset(encodings)
      tfdataset = tfdataset.batch(1)

      preds = model.predict(tfdataset).logits
      #print("pred logits: ",preds)
      preds = activations.softmax(tf.convert_to_tensor(preds)).numpy()
      #print("softmax o/p: ",preds)
      return preds[0][1]

  return predict_proba

"""Example prediction:"""

# Define constants
MODEL_NAME = 'distilbert-base-uncased'
MAX_LEN = 128  # Set the maximum length of input sequences
clf = create_predictor(model, MODEL_NAME, MAX_LEN)
print(clf("Great product, I'm enjoying it!"))

"""**14. Save and Reload Model**"""

model.save_pretrained('./model/clf')
with open('./model/info.pkl', 'wb') as f:
    pickle.dump((MODEL_NAME, MAX_LEN), f)

"""**Reload and use the model:**"""

new_model = TFDistilBertForSequenceClassification.from_pretrained('./model/clf')
model_name, max_len = pickle.load(open('./model/info.pkl', 'rb'))
clf = create_predictor(new_model, model_name, max_len)
print(clf('Love my Echo!'))

clf = create_predictor(new_model, model_name, max_len)
print(clf("Alexa doesn't get connected well to my laptop's bluetooth, however it's very useful and answers correctly to my questions"))

clf = create_predictor(new_model, model_name, max_len)
print(clf("Gets disconnecetd again and again, I'll not recommend it to others"))

def predict_y_pred(predicted_probability):
  y_pred='Negative'
  if predicted_probability>= 0.75:
    y_pred='Positive'
  elif predicted_probability>0.25 and predicted_probability<0.75:
    y_pred='Neutral'
  return y_pred

new_model = TFDistilBertForSequenceClassification.from_pretrained('./model/clf')
model_name, max_len = pickle.load(open('./model/info.pkl', 'rb'))

clf = create_predictor(new_model, model_name, max_len)
print('Review: Love my Echo!')
predicted_proba=clf('Love my Echo!')
print(predict_y_pred(predicted_proba))

clf = create_predictor(new_model, model_name, max_len)
print("Review: Alexa doesn't get connected well to my laptop's bluetooth, however it's very useful and answers correctly to my questions")
predicted_proba=clf("Alexa doesn't get connected well to my laptop's bluetooth, however it's very useful and answers correctly to my questions")
print(predict_y_pred(predicted_proba))

clf = create_predictor(new_model, model_name, max_len)
print("Review: Gets disconnecetd again and again, I'll not recommend it to others")
predicted_proba=clf("Gets disconnecetd again and again, I'll not recommend it to others")
print(predict_y_pred(predicted_proba))

clf = create_predictor(new_model, model_name, max_len)
print("Review: This is not a good product")
predicted_proba=clf("This is not a good product")
print(predict_y_pred(predicted_proba))

!zip -r sentiment-analysis.zip app.py model/

from google.colab import files
files.download('sentiment-analysis.zip')

