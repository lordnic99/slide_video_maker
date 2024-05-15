from tqdm import tqdm
import requests
import os

def download_file_from_internet(url, location):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc=location)
        with open(location, "wb") as f:
            for chunk in response.iter_content(block_size):
                progress_bar.update(len(chunk))
                f.write(chunk)
        progress_bar.close()
    else:
        raise Exception(f"download failed with status code: {response.status_code}")
    
def remove_all_files_in_path(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        try:
            os.remove(file_path)
        except:
            pass