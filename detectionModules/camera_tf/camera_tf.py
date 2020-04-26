import os
import cv2
from dotenv import load_dotenv, find_dotenv
from detectionModules.camera_tf.tensorflowObjectDetector import TensorflowObjectDetector

# load the .env file
load_dotenv(find_dotenv())

# './ssdlite_mobilenet_v2_coco_2018_05_09/frozen_inference_graph.pb'
model_path = os.getenv('MODEL_PATH')
object_detector = TensorflowObjectDetector(path_to_checkpoint=model_path)
threshold = float(os.getenv('THRESHOLD'))  # this is %
# input_video = "Inside Google's New Asia Pacific HQ _ CNBC.mp4"
# cap = cv2.VideoCapture(input_video)
cap = cv2.VideoCapture(0)
#  output_video = "./output.avi"
#   writer = None

#    # try to determine the total number of frames in the video file
#    try:
#         prop = cv2.CAP_PROP_FRAME_COUNT
#         total_frames = int(cap.get(prop))
#         print("[INFO] {} total frames in video".format(total_frames))

#     # an error occurred while trying to determine the total
#     # number of frames in the video file
#     except:
#         print("[INFO] could not determine # of frames in video")
#         print("[INFO] no approx. completion time can be provided")
#         total_frames = -1

while True:
    grabbed, img = cap.read()

    # if not grabbed a new frame, when we reach end of stream
    if not grabbed:
        break

    img = cv2.resize(img, (1280, 720))
    boxes, scores, classes, num = object_detector.processFrame(img)
    # print("num ------> ", num)
    # Visualization of the results of a detection.

    l = 0
    for i in range(len(boxes)):
        # Class 1 represents human
        if classes[i] == 1 and scores[i] > threshold:
            box = boxes[i]
            cv2.rectangle(img, (box[1], box[0]),
                          (box[3], box[2]), (255, 0, 0), 2)
            l += 1

    print(l)

    # check if the video writer is None
    # if writer is None:
    #     # initialize our video writer
    #     fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    #     writer = cv2.VideoWriter(output_video, fourcc, 30,
    #                              (img.shape[1], img.shape[0]), True)

    # write the output frame to disk
    # writer.write(img)

    cv2.imshow("preview", img)
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break

# release the file pointers
print("[INFO] cleaning up...")
# writer.release()
cap.release()
cv2.destroyAllWindows()
