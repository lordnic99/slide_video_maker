import requests
import os
import string
import random
import utilities


def get_videos_url(keyword):
    vid_urls = []
    for item in get_list_videos(keyword):
        vid_urls.append(item['videoSrc'])
    return vid_urls

def get_list_videos(keyword):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    res = requests.get(f"https://www.freepik.com/api/videos?filters[aspect_ratio][]=16:9&view_aspect=16:9&format[search]=1&license[free]=1&locale=en&order=relevance&term={keyword}&type[video]=1&page=2", headers=headers)
    return res.json()['items']

def find_and_download(key_word):
    os.makedirs("freepik_videos", exist_ok=True)
    print("Đang tải video freepik")
    video_urls = get_videos_url(key_word)
    if not video_urls:
        print(f"Không tìm thấy freepik video với keyword: {key_word}")
        os._exit(1)
        
    random_video_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    url = video_urls[0]
    ext = url.rsplit('.')[-1]
    video_name = f"{random_video_name}.{ext}"
    utilities.download_file_from_internet(url, f"freepik_videos/{random_video_name}.{ext}")
    print(f"-> Tai thanh cong video: {random_video_name}.{ext}")
    return f"freepik_videos/{video_name}"