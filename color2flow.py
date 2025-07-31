import pyrealsense2 as rs
import numpy as np
import cv2

def main():

    # 查询连接的设备，检查是否支持彩色相机
    context = rs.context()
    devices = context.query_devices()
    if len(devices) == 0:
        print("没有检测到 RealSense 设备，请检查连接。")
        return

    serial_numbers = []
    for i, dev in enumerate(devices):
        name = dev.get_info(rs.camera_info.name)           # 设备名称
        sn = dev.get_info(rs.camera_info.serial_number)    # 序列号
        product_line = dev.get_info(rs.camera_info.product_line)
        print(f"设备 {i}: {name}, SN: {sn}, 产品线: {product_line}")
        serial_numbers.append(sn)

    selected_index = 0  # 默认选第一个
    # 用户输入：
    selected_index = int(input("请输入要使用的设备编号: "))
    selected_sn = serial_numbers[selected_index]
    print(f"正在使用设备 (SN: {selected_sn})")

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device(selected_sn)

    # # 获取设备的产品线信息（如 D400、L500）
    # device = devices[0]  # 取第一个设备
    # product_line = str(device.get_info(rs.camera_info.product_line))

    # 启用彩色流（RGB）
    # 参数：流类型、宽度、高度、格式、帧率
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # 开始流传输
    print("开始彩色流...")
    pipeline.start(config)

    try:
        while True:
            # 等待一帧图像
            frames = pipeline.wait_for_frames()

            # 获取彩色帧
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue  # 如果没有接收到帧，跳过

            # 将图像帧转换为 NumPy 数组（OpenCV 格式）
            color_image = np.asanyarray(color_frame.get_data())

            # 使用 OpenCV 显示图像
            cv2.imshow('RealSense color flow', color_image)

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
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()