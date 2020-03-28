import requests
import re
import os
from PIL import Image
from io import BytesIO
import time

class Page:
    def __init__(self, url):
        self.url = url

    def getImage(self, url):
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
                images.append(self.getImage(image_urls[i]))

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
        save_dir = "%sopm-%s.pdf" % (self.dir, self.num)
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

    def downloadChaptersBetween(self, min, max):
        print("Downloading chapters {} to {}".format(min, max))
        chapter_urls = self.getChapterUrls()
        seen=[]
        count=0
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
                count+=1

        return count

    def getChapterUrl(self, num):
        url = 'https://ww3.one-punchman.com/manga/one-punch-man-chapter-%d/'%(num)
        return url

    def getChapterUrls(self):
        page = requests.get('https://ww3.one-punchman.com/').text
        pattern = r'(https\:\/\/ww3.+chapter-.+)\">'
        chapter_urls = re.findall(pattern, page)
        return chapter_urls[::-1]

class DownloadManager:
    def __init__(self, dir):
        self.dir = dir

    def getInputAsNum(self, query):
        while(1):
            try:
                resp = int(input(query))
                return(resp)
            except:
                print("Only numbers will work...")

    def doUserAction(self, resp):
        downloader = Downloader(self.dir)
        if(resp == 1):
            url_num = self.getInputAsNum('What chapter number would you like to download?\n')
            url = downloader.getChapterUrl(url_num)
            start = time.time()
            downloader.downloadChapter(url)
            stop = time.time() - start
            print("Downloaded 1 chapter in {} seconds".format(round((stop), 2)))

        elif(resp == 2):
            print("This option lets you download all the chapters between a minimum and maximum value")
            min = self.getInputAsNum("What's the lowest chapter number you'd like to download?\n")
            max = self.getInputAsNum("What's the highest chapter number you'd like to download?\n")
            start = time.time()
            count = downloader.downloadChaptersBetween(min, max)
            stop = time.time() - start
            print("Downloaded {} chapters in {} seconds".format(count, round((stop), 2)))
        elif(resp == 3):
            print("Bye!")
        else: 
            print("That won't work. Please make a valid choice")


    def writeMenu(self):
        while(True):
            print("Welcome to One-Punch-Py\n1: Download a single chapter\n2: Download many chapters\n3: Quit")
            resp = self.getInputAsNum("Please make a choice: ")
            self.doUserAction(resp)
            if(resp == 3):
                break


directory = './files'
DownloadManager(directory).writeMenu()
