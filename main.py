import cv2
import numpy as np
import os
import random
from moviepy.editor import *
import os
import re
import requests
import freepik
import subprocess
import bing.crawler as crawler
import bing.helperdownload as helperdownload
import string
import utilities
import caption


def generate_audio(text, speed="1.0", device="cpu"):
    print(f"Đang chuyển đổi text sang audio: {text}")
    url = "http://113.160.163.14:5000/generate_audio_api"
    data = {"text": text, "speed": speed, "device": device}

    response = requests.post(url, json=data)

    if response.status_code == 201:
        filename = response.json()["url"]
        full_url = f"http://113.160.163.14:5000/static/{filename}"
        utilities.download_file_from_internet(full_url, filename)
        return filename
    else:
        raise Exception(f"failed with status code: {response.status_code}")


def split_sentences(text):
    sentences = re.split(r"[?.!。]", text)
    return list(filter(lambda item: item and item.strip(), sentences))

def pick_random_image(image_name, downloaded_images_folder="download_images"):
    print("\n----------------------")
    print("Đang chọn ra ảnh ngẫu nhiên từ list ảnh")
    if not os.path.isdir(downloaded_images_folder):
        raise ValueError(
            f"Invalid downloaded_images_folder: {downloaded_images_folder}"
        )

    images_path = []

    for filename in os.listdir(downloaded_images_folder):
        if filename.startswith(image_name):
            image_path = os.path.join(downloaded_images_folder, filename)
            images_path.append(image_path)

    return random.choice(images_path)


def bing_image_handler(keyword, engine, number):
    random_img_name = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(6)
    )

    crawled_urls = crawler.crawl_image_urls(
        keywords=keyword,
        engine=engine,
        max_number=number,
        face_only=False,
        safe_mode=False,
        proxy_type=None,
        proxy=None,
        browser="firefox_headless",
        image_type=None,
        color=None,
    )

    helperdownload.download_images(
        image_urls=crawled_urls,
        dst_dir="./download_images",
        file_prefix=random_img_name,
    )

    return random_img_name


def apply_chroma_key(frame, green_screen_color):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array(green_screen_color[0], dtype=np.uint8)
    upper_green = np.array(green_screen_color[1], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask_inv = cv2.bitwise_not(mask)
    fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    return fg


def create_video(
    effect_video,
    effect_width,
    effect_height,
    image,
    audio_clip,
    output_video,
    fps,
    reverse_foreground,
):
    frame_count = int(fps * audio_clip.duration)
    background = cv2.resize(image, (int(effect_width * 1.5), effect_height))
    background = np.hstack([background, background])

    foreground = cv2.resize(image, (int(effect_width * 0.6), int(effect_height * 0.6)))
    alpha = 1
    foreground = cv2.addWeighted(
        foreground, alpha, np.zeros_like(foreground), 1 - alpha, 0
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(output_video, fourcc, fps, (effect_width, effect_height))

    for i in range(frame_count):
        ret, frame = effect_video.read()
        if not ret:
            effect_video.release()
            effect_video = cv2.VideoCapture(effect_path)
            ret, frame = effect_video.read()

        effect_index = i % int(effect_video.get(cv2.CAP_PROP_FRAME_COUNT))
        effect_video.set(cv2.CAP_PROP_POS_FRAMES, effect_index)

        green_screen_color = ([25, 80, 80], [125, 255, 255])
        effect_frame = apply_chroma_key(frame, green_screen_color)

        bg_x = 0
        fg_x = (
            int(effect_width * 0.6 * (i / frame_count))
            if not reverse_foreground
            else int(effect_width * 0.6 * (1 - i / frame_count))
        )

        composite_frame = np.zeros_like(image)
        composite_frame[:, :] = background[:, bg_x : bg_x + effect_width]

        fg_y = (effect_height - int(effect_height * 0.6)) // 2
        fg_end_x = min(fg_x + int(effect_width * 0.6), effect_width)
        composite_frame[
            fg_y : fg_y + int(effect_height * 0.6), fg_x:fg_end_x
        ] = foreground[:, : fg_end_x - fg_x]

        if effect_frame.shape == composite_frame.shape:
            composite_frame = cv2.addWeighted(composite_frame, 1, effect_frame, 1, 0)

        video.write(composite_frame)

    video.release()
    return output_video


def create_effect_video(input_jpg, input_audio):
    effect_video = None

    try:
        effect_dir = "effect/"
        effect_files = [f for f in os.listdir(effect_dir) if f.endswith(".mp4")]
        selected_effect = random.choice(effect_files)
        effect_path = os.path.join(effect_dir, selected_effect)

        effect_video = cv2.VideoCapture(effect_path)
        ret, temp_frame = effect_video.read()
        if not ret:
            raise Exception("Không thể đọc video hiệu ứng")

        effect_height, effect_width = temp_frame.shape[:2]

        audio_path = input_audio
        audio_clip = AudioFileClip(audio_path)

        image_path = input_jpg
        image = cv2.imread(image_path)
        image = cv2.resize(image, (effect_width, effect_height))

        fps = 25
        output_video = "output.mp4"

        reverse_foreground = random.choice([True, False])

        create_video(
            effect_video,
            effect_width,
            effect_height,
            image,
            audio_clip,
            output_video,
            fps,
            reverse_foreground,
        )

    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")

    finally:
        if effect_video is not None and effect_video.isOpened():
            effect_video.release()


def create_freepik_video(freepik_vid_input, audio_input, output_video):
    audio_clip = AudioFileClip(audio_input)
    video_clip = VideoFileClip(freepik_vid_input)
    video_clip = video_clip.subclip(0, audio_clip.duration)
    video_clip = video_clip.set_audio(audio_clip)
        
    video_clip.write_videofile(
        output_video, codec="libx264", audio_codec="aac"
    )




def merge_all_senetences_video(
    directory=os.getcwd(), output_filename="final_result.mp4"
):
    video_files = sorted(
        os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".mp4")
    )

    with open("list.txt", "w") as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")

    result = subprocess.run(
        [
            "./bin/ffmpeg.exe",
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            "list.txt",
            "-c:v",
            "libx264",  # Use libx264 encoder for H.264 MP4
            "-c:a",
            "aac",     # Use AAC encoder for audio
            "-movflags",
            "faststart",  # For faster playback on web
            output_filename,
        ],
        check=True,
    )

    if result.returncode == 0:
        print("Videos merged successfully!")
    else:
        print("Error: ffmpeg failed to merge videos.")

    os.remove("list.txt")


if __name__ == "__main__":
    text = input("Nhập đoạn văn bản: ")
    sentences = split_sentences(text)
    id = lambda i: f"{i+1:03d}"
    
    for i, sentence in enumerate(sentences):
        
        if i % 2 == 0:  # tao video freepik
            video_no_text   = f"cau_{id(i)}_freepik_no_text.mp4"
            video_no_sound  = f"cau_{id(i)}_freepik_no_sound.mp4"
            final_video     = f"cau_{id(i)}_freepik.mp4"
            
            print(f"\n**Câu {i+1}:** {sentence}")
            
            audio_file = generate_audio(sentence)
            video_file = freepik.find_and_download(sentence)
            
            create_freepik_video(
                video_file, audio_file, video_no_text
            )
            
            print("Tiến hành ghép text vào video")
            caption.add_text_to_video(
                video_path=video_no_text,
                text=sentence,
                font_path="font.ttc",
                font_size=35,
                output_path=video_no_sound
            )
            
            create_freepik_video(
                video_no_sound, audio_file, final_video
            )
            
            print("------------------------------")
            
            os.remove(video_no_text)
            os.remove(video_no_sound)
            os.remove(audio_file)
        else:  # tao video img
            print(f"\n**Câu {i+1}:** {sentence}")
            
            video_no_sound  = f"cau_{id(i)}_img_no_sound.mp4"
            final_video     = f"cau_{id(i)}_img.mp4"
            
            jpg_downloaded_name = pick_random_image(
                bing_image_handler(sentence, "Bing", 10)
            )
            audio_file = generate_audio(sentence)
            
            create_effect_video(
                jpg_downloaded_name, audio_file
            )
            
            print("Tiến hành ghép text vào video")
            caption.add_text_to_video(
                video_path="output.mp4",
                text=sentence,
                font_path="font.ttc",
                font_size=35,
                output_path=video_no_sound
            )
            audio_clip = AudioFileClip(audio_file)
            video_clip = VideoFileClip(video_no_sound)
            video_clip = video_clip.set_audio(audio_clip)
            video_clip.write_videofile(
                final_video, codec="libx264", audio_codec="aac"
            )
            os.remove("output.mp4")
            os.remove(video_no_sound)
            os.remove(audio_file)

    merge_all_senetences_video()
    utilities.remove_all_files_in_path("download_images")
    utilities.remove_all_files_in_path("freepik_videos")
