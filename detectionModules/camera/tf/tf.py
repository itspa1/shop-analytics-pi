import os
import cv2
import time
from detectionModules.camera.tf.tensorflowObjectDetector import TensorflowObjectDetector


class TF():
    def __init__(self, configs):
        # './ssdlite_mobilenet_v2_coco_2018_05_09/frozen_inference_graph.pb'
        self.model_path = configs['MODEL_PATH']
        self.object_detector = TensorflowObjectDetector(
            path_to_checkpoint=self.model_path)
        self.threshold = configs['THRESHOLD']  # this is %
        # set the video_source (0,-1,or some path to video)
        self.video_source = configs["VIDEO_SOURCE"]  # 0
        self.detections = list()

    def start(self, start_send_frame):
        start_send_frame(self)
        # while self._running:
        self._start_tf()
        print("Stopping")

    def _show_frame(self, frame):
        cv2.imshow("preview", frame)

    def _start_tf(self):
        # input_video = "Inside Google's New Asia Pacific HQ _ CNBC.mp4"
        # vs = cv2.VideoCapture(input_video)
        # VideoStream
        vs = cv2.VideoCapture(self.video_source)

        # initialize variables to capture start time and frame count to actually calculate approximate FPS
        frame_id = 0
        starting_time = time.time()
        while True:

            grabbed, img = vs.read()
            frame_id += 1

            # if not grabbed a new frame, when we reach end of stream
            if not grabbed:
                break

            frame = cv2.resize(img, (1280, 720))
            boxes, scores, classes, num = self.object_detector.processFrame(
                frame)
            # print("num ------> ", num)
            # Visualization of the results of a detection.

            detections = 0
            for i in range(len(boxes)):
                # Class 1 represents human
                if classes[i] == 1 and scores[i] > self.threshold:
                    # box = boxes[i]
                    # cv2.rectangle(frame, (box[1], box[0]),
                    #               (box[3], box[2]), (255, 0, 0), 2)
                    # text = "confidence: {:.4f}".format(
                    #     scores[i])
                    # cv2.putText(frame, text, (box[1], box[1] + 1),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    detections += 1

            self.detections.append(detections)
            # print(l)
            elapsed_time = time.time() - starting_time
            fps = frame_id/elapsed_time
            # cv2.putText(frame, "FPS:"+str(round(fps, 2)),
            #             (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 1)

            # self._show_frame(frame)

            # key = cv2.waitKey(1)
            # if key & 0xFF == ord('q'):
            #     break

        # release the file pointers
        print("[INFO] cleaning up...")
        # writer.release()
        vs.release()
        cv2.destroyAllWindows()


# OLD CODE TO WRITE TO OUTPUT VIDEO FILE

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

        # check if the video writer is None
        # if writer is None:
        #     # initialize our video writer
        #     fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        #     writer = cv2.VideoWriter(output_video, fourcc, 30,
        #                              (img.shape[1], img.shape[0]), True)

        # write the output frame to disk
        # writer.write(img)

        # cv2.imshow("preview", img)
