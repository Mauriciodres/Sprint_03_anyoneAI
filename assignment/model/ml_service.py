import json
import os
import time

import numpy as np
import redis
import settings
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import decode_predictions, preprocess_input
from tensorflow.keras.preprocessing import image

# TODO
# Connect to Redis and assign to variable `db``
# Make use of settings.py module to get Redis settings like host, port, etc.
db = redis.Redis(
    host= settings.REDIS_IP,
    port = settings.REDIS_PORT,
    db = settings.REDIS_DB_ID
)

# TODO
# Load your ML model and assign to variable `model`
# See https://drive.google.com/file/d/1ADuBSE4z2ZVIdn66YDSwxKv-58U7WEOn/view?usp=sharing
# for more information about how to use this model.
model = ResNet50(include_top = True, weights= "imagenet")


def predict(image_name):
    print("Entro a la funcion predict")
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    img = image.load_img(os.path.join(settings.UPLOAD_FOLDER, image_name), target_size=(224, 224))
    img = image.img_to_array(img)
    img_batch = np.expand_dims(img, axis=0)
    
    img_preprocess = preprocess_input(img_batch)

    preds = model.predict(img_preprocess)

    decode = decode_predictions(preds, top=3)[0]
    decode = max(decode, key=lambda k: k[2])

    class_name = decode[1]
    pred_probability = round(float(decode[2]), 4)

    return class_name, pred_probability
    


def classify_process():
    print("Entró a la funcion Classify")
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.

    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.
    """
    while True:
        # Inside this loop you should add the code to:
        #   1. Take a new job from Redis
        #   2. Run your ML model on the given data
        #   3. Store model prediction in a dict with the following shape:
        #      {
        #         "prediction": str,
        #         "score": float,
        #      }
        #   4. Store the results on Redis using the original job ID as the key
        #      so the API can match the results it gets to the original job
        #      sent
        # Hint: You should be able to successfully implement the communication
        #       code with Redis making use of functions `brpop()` and `set()`.
        file_name =  db.brpop(settings.REDIS_QUEUE)
        file_name = json.loads(file_name[1].decode("utf-8"))
        pred, score = predict(file_name["image_name"])
        # Sleep for a bit
        time.sleep(settings.SERVER_SLEEP)
        job_id = file_name["id"]
        
        db.set(job_id, json.dumps({
                    "prediction": pred,
                    "score": np.float64(score),
                }))

if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
