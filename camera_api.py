import pyrealsense2 as rs
import numpy as np
import cv2
from threading import Thread
import time
import queue
import os
from flask import Flask, render_template, Response

def find_camera_devices():
    """
    查找本机所连接的所有realsense设备
    请记录相机序列号作为区分不同相机的标识
    """
    context = rs.context()
    devices = context.query_devices()
    if len(devices) == 0:
        print("没有检测到 RealSense 设备，请检查连接")
        return
    
    for i, dev in enumerate(devices):
        name = dev.get_info(rs.camera_info.name)           # 设备名称
        sn = dev.get_info(rs.camera_info.serial_number)    # 序列号
        product_line = dev.get_info(rs.camera_info.product_line)
        print(f"设备 {i}: {name}, SN: {sn}, 产品线: {product_line}")



class Camera_D435i():

    def __init__(self, sn: str):
        # attribute
        self.sn = sn
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        self.frame_queue = queue.Queue(maxsize=10)
        self.color_flow_thread = Thread(target=self.capture_thread)

        self.set_default_recording()


    def start_flow(self):
        # start the camera
        self.config.enable_device(self.sn)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(self.config)

    def capture_thread(self):
        """RealSense 捕获线程：不断获取帧并放入队列"""
        frame_queue = self.frame_queue
        try:
            while True:
                # 等待一帧图像
                frames = self.pipeline.wait_for_frames()

                # 获取彩色帧
                color_frame = frames.get_color_frame()
                if not color_frame:
                    continue  # 如果没有接收到帧，跳过

                # 将图像帧转换为 NumPy 数组（OpenCV 格式）
                color_image = np.asanyarray(color_frame.get_data())
                ret, buffer = cv2.imencode('.jpg', color_image)
                frame = buffer.tobytes()
                frame = (b'--frame\r\n'
                         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                
                if not frame_queue.full():
                    # todo: 这里可以按需更改流的格式
                    frame_queue.put(frame)
                else:
                    frame_queue.get()
                    frame_queue.put(frame)
                # print(f"the length of frame_queue is {frame_queue.qsize()}")
                time.sleep(0.001)

                # 使用 OpenCV 显示图像[可选]
                cv2.imshow('RealSense color flow', color_image)
                if self.outVedio_RGB is not None:
                    if self.record_flag is True:
                        print("视频正在录制中···")
                        self.outVedio_RGB.write(color_image)
                    else:
                        print("视频停止录制")
                        self.outVedio_RGB.release()

                # 按下 'q' 或 ESC 键退出
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q') or key == 27:
                    print("用户请求退出。")
                    break

        except Exception as e:
            print(f"发生错误: {e}")

        finally:
            # 清理资源
            print("停止流并关闭管道...")
            if self.record_flag is True:
                self.record_flag = False
                print("视频停止录制")
                self.outVedio_RGB.release()
            self.pipeline.stop()
            cv2.destroyAllWindows()

    def set_default_recording(self):
        self.record_flag = False
        # self.fourcc = cv2.VideoWriter_fourcc('F', 'L', 'V', '1')
        self.fourcc = 0x00000002
        self.outVedio_RGB = None


    def start_record(self):
        fps = 30
        width = 640
        height = 480
        os.makedirs('./videoStreams', exist_ok=True)
        self.outVedio_RGB = cv2.VideoWriter(f'./videoStreams/RGB{time.time()}.flv', self.fourcc, fps, (width, height))
        self.record_flag = True

    def stop_record(self):
        self.record_flag = False

if __name__ == '__main__':
    

    app = Flask(__name__)
    @app.route('/')
    def index():
        return render_template('index.html')


    find_camera_devices()
    cam1 = Camera_D435i(sn='243222074447')
    cam1.start_flow()
    cam1.color_flow_thread.start()
    # cam1.start_record()
    # time.sleep(10)
    # cam1.stop_record()
    def gen_frames():  # generate frame by frame from camera
        while True:
            # Capture frame-by-frame
            frame = cam1.frame_queue.get()  # read the camera frame
            yield frame

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    app.run(debug=False)