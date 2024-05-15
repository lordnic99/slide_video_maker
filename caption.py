import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def textsize(text, font):
    im = Image.new(mode="P", size=(0, 0))
    draw = ImageDraw.Draw(im)
    _, _, width, height = draw.textbbox((0, 0), text=text, font=font)
    return width, height

def process_text_for_clip(text, width, font_size):
    char_width = font_size * 0.7
    current_line = ""
    processed_text = ""
    for word in text[::-1]:
        if len(current_line) * char_width + len(word) * char_width <= width:
            current_line += " " + word
        else:
            processed_text += current_line + "\n"
            current_line = word
            
    processed_text += current_line
    return processed_text[::-1] + '\n'


def add_text_to_video(video_path, text, font_path, font_size, output_path):
    video = cv2.VideoCapture(video_path)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    
    text_processed = process_text_for_clip(text=text, width=width, font_size=30)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while True:
        ret, frame = video.read()
        if not ret:
            break
        frame = add_text_to_frame(frame, text_processed, font_path, font_size)
        out.write(frame)
    video.release()
    out.release()

def add_text_to_frame(frame, text, font_path, font_size):
    pil_image = Image.fromarray(frame)

    draw = ImageDraw.Draw(pil_image, "RGBA")

    font = ImageFont.truetype(font_path, font_size)

    text_width, text_height = textsize(text, font=font)

    text_x = (pil_image.width - text_width) // 2
    text_y = pil_image.height - text_height - 50 

    opacity = int(.25*255)
    
    draw.rectangle(
        [(text_x - 5, text_y - 5), (text_x + text_width + 5, text_y + text_height + 5)],
        fill=(0, 0, 0, opacity),
    )
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 0), align='center')

    frame = np.array(pil_image)

    return frame

add_text_to_video(
    video_path="final_result_1.mp4",
    text="試合はオラクル・パークで行われ、試合開始10分前にドジャースの先発ラインナップが発表されると、ジャイアンツの本拠地は大きなブーイングで満たされました。",
    font_path="font.ttc",
    font_size=30,
    output_path="text.mp4",
)