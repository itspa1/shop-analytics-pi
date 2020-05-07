import os
import cv2
import tensorflow as tf

import numpy as np
import time
from dotenv import load_dotenv, find_dotenv
# from detectionModules.camera.tf.tensorflowObjectDetector import TensorflowObjectDetector
from multiprocessing import Process

# load the .env file
# load_dotenv(find_dotenv())


class TF(Process):
    def __init__(self, configs):
        Process.__init__(self)

        # './ssdlite_mobilenet_v2_coco_2018_05_09/frozen_inference_graph.pb'
        self.model_path = configs['MODEL_PATH']
        # self.object_detector = TensorflowObjectDetector(
        #     path_to_checkpoint=self.model_path)
        self.threshold = configs['THRESHOLD']  # this is %
        self.path_to_checkpoint = self.model_path
        self.detection_graph = tf.Graph()

        with self.detection_graph.as_default():
            object_detection_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.path_to_checkpoint, 'rb') as fid:
                serialized_graph = fid.read()
                object_detection_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(object_detection_graph_def, name='')

        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.compat.v1.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name(
            'image_tensor:0')

        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name(
            'detection_boxes:0')

        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name(
            'detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name(
            'detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name(
            'num_detections:0')
        print("LOADED")

    def run(self):
        self.start()
        print("Stopping")

    def processFrame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)

        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores,
                self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()
        print(end_time)
        elapsed_time = end_time - start_time
        print("Elapsed Time For Frame:", elapsed_time)

        im_height, im_width, _ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0, i, 0] * im_height),
                             int(boxes[0, i, 1]*im_width),
                             int(boxes[0, i, 2] * im_height),
                             int(boxes[0, i, 3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def show_frame(self, frame):
        cv2.imshow("preview", frame)

    def start(self):
        input_video = "Inside Google's New Asia Pacific HQ _ CNBC.mp4"
        cap = cv2.VideoCapture(input_video)
        # cap = cv2.VideoCapture(0)
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
            # while self._run:
            grabbed, img = cap.read()
            print("ININININ")
            # if not grabbed a new frame, when we reach end of stream
            if not grabbed:
                break

            frame = cv2.resize(img, (1280, 720))
            boxes, scores, classes, num = self.processFrame(
                frame)
            print("num ------> ", num)
            # Visualization of the results of a detection.

            l = 0
            for i in range(len(boxes)):
                # Class 1 represents human
                if classes[i] == 1 and scores[i] > self.threshold:
                    box = boxes[i]
                    cv2.rectangle(frame, (box[1], box[0]),
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

            cv2.imshow("preview", frame)
            # self.show_frame(frame)

            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break

        # release the file pointers
        print("[INFO] cleaning up...")
        # writer.release()
        cap.release()
        cv2.destroyAllWindows()
