import requests
import re
import os
from PIL import Image
from io import BytesIO
import time

class Page:
    def __init__(self, url):
        self.url = url

    def getImage(self, url, num):
        try:
            resp = requests.get(url, stream=True)
            return resp

        except:
            raise ValueError("Could not getImage\nURL:%s\n" % self.url)

    def getImageUrls(self):
        page = requests.get(self.url).text
        pattern = r'(https\:\/\/1.+[png|jpg])\">'
        image_urls = re.findall(pattern, page)
        del page

        return(image_urls)

    def getImages(self):
        try:
            image_urls = self.getImageUrls()
            images = []

            for i in range(0, len(image_urls)):
                progress = "  working%s" % (i*".")
                print(progress+"\r", end="")
                images.append(self.getImage(image_urls[i], (i+1)))

            print("Done! Crafting pdf")
            return images

        except:
            raise ValueError("failed to get images")


class Chapter:
    def __init__(self, url, num, dir):
        self.url = url
        self.num = num
        self.dir = dir

    def getImageFiles(self):
        page = Page(self.url)
        images = page.getImages()
        img_files = []
        for image in images:
            img_files.append(Image.open(BytesIO(image.content)))

        return(img_files)

    def getChapter(self):
        print("Downloading chapter {}" .format(self.num))

        img_files = self.getImageFiles()
        save_dir = "%schapter-%s.pdf" % (self.dir, self.num)
        try:
            img_files[0].save(save_dir, "PDF", resolution=100.0,
                              save_all=True, append_images=img_files[0:])
            del img_files
            os.system('cls')

        except:
            raise ValueError(
                "Failed to save chapter {}".format(self.num))


class Downloader:
    def __init__(self, dir):
        self.dir = dir

    def getChapDir(self, num):
        chap_dir = "{}/".format(self.dir)

        if not os.path.exists(chap_dir):
            os.makedirs(chap_dir)

        return(chap_dir)

    def getChapNum(self, url):
        pat = r'chapter-(.+)\/'
        num = re.findall(pat, url)
        return(num[0])

    def downloadChapter(self, url):
        num = self.getChapNum(url)
        chap_dir = self.getChapDir(num)
        chapter = Chapter(url, num, chap_dir)
        chapter.getChapter()

    def downloadChaptersFrom(self, min, max):
        print("Downloading chapters {} to {}".format(min, max))
        chapter_urls = self.getChapterUrls()
        seen=[]
        for chap_url in chapter_urls:
            num = self.getChapNum(chap_url)
            if not chap_url in seen:
                seen.append(chap_url)
            else:
                continue

            if '-' in num:
                num = re.findall(r'\d+', num)[0]

            if (min <= int(num) and int(num) <= max):
                print("Getting %s" % chap_url)
                self.downloadChapter(chap_url)


        print("Finished!")

    def getChapterUrls(self):
        page = requests.get('https://ww3.one-punchman.com/').text
        pattern = r'(https\:\/\/ww3.+chapter-.+)\">'
        chapter_urls = re.findall(pattern, page)
        return chapter_urls[::-1]


directory = './files'
min=31
max=35
start = time.time()
downloader = Downloader(directory)
downloader.downloadChaptersFrom(min, max)
stop = time.time()
print("Downloaded {} chapters in {} seconds".format((max-min),int(stop-start)))
