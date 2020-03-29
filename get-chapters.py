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

            print("Got images from %s!"%self.url)
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
            img_files.append(Image.open(BytesIO(image.content)).convert('RGB'))

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

    def getCombinedDir(self):
        comb_dir = "{}/".format(self.dir)
        if not os.path.exists(comb_dir):
            os.makedirs(comb_dir)

        return(comb_dir)

    def getChapNum(self, url):
        pat = r'chapter-(.+)\/'
        num = re.findall(pat, url)[0]
        return(num)

    def downloadChapter(self, url):
        num = self.getChapNum(url)
        chap_dir = self.getChapDir(num)
        chapter = Chapter(url, num, chap_dir)
        chapter.getChapter()

    def getChaptersBetween(self, min, max):
        chapter_urls = self.getChapterUrls()
        seen = []
        wanted_urls = []

        for chap_url in chapter_urls:
            num = self.getChapNum(chap_url)
            if not chap_url in seen:
                seen.append(chap_url)
            else:
                continue

            if '-' in num:
                num = re.findall(r'\d+', num)[0]

            if (min <= int(num) and int(num) <= max):
                wanted_urls.append(chap_url)

        return sorted(wanted_urls)


    def getPdfBetween(self, min, max):
        img_files = []
        urls = self.getChaptersBetween(min, max)
        print("Combining %d chapters"%len(urls))
        for url in urls:
            num = self.getChapNum(url)
            dir = self.getChapDir(num)
            chapter = Chapter(url, num, dir)
            img_files = img_files + chapter.getImageFiles()
        
        save_dir = "%sopm-%sto%s.pdf" % (self.getCombinedDir(), min, max)

        try:
            img_files[0].save(save_dir, "PDF", resolution=100.0,
                                save_all=True, append_images=img_files[0:])
            del img_files
            os.system('cls')
            print("Finished! Combined %d chapters"%len(urls))
            return len(urls)
        except:
            raise ValueError("Failed to download mass PDF")

    def downloadChaptersBetween(self, min, max):
        print("Downloading chapters {} to {}".format(min, max))
        chapter_urls = self.getChaptersBetween(min, max)
        for url in chapter_urls:
            print("Getting %s" % url)
            self.downloadChapter(url)

        return len(chapter_urls)

    def getChapterUrl(self, num):
        url = 'https://ww3.one-punchman.com/manga/one-punch-man-chapter-%d/' % (
            num)
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
            url_num = self.getInputAsNum(
                'What chapter number would you like to download?\n')
            url = downloader.getChapterUrl(url_num)
            start = time.time()
            downloader.downloadChapter(url)
            stop = time.time() - start
            print("Downloaded 1 chapter in {} seconds".format(round((stop), 2)))

        elif(resp == 2):
            print(
                "This option lets you download all the chapters between a minimum and maximum value")
            min = self.getInputAsNum(
                "What's the lowest chapter number you'd like to download?\n")
            max = self.getInputAsNum(
                "What's the highest chapter number you'd like to download?\n")
            start = time.time()
            count = downloader.downloadChaptersBetween(min, max)
            stop = time.time() - start
            if stop > 120:
                print("Downloaded {} chapters in {} minutes".format(
                    count, round((stop/60), 2)))
            else:
                print("Downloaded {} chapters in {} seconds".format(
                    count, round((stop), 2)))
        elif(resp == 3):
            print("This option lets you download all chapters between a minimum and maximum value\nand puts the chapters into a single PDF")
            min = self.getInputAsNum(
                "What's the lowest chapter number you'd like to download?\n")
            max = self.getInputAsNum(
                "What's the highest chapter number you'd like to download?\n")
            start = time.time()
            count = downloader.getPdfBetween(min, max)
            stop = time.time() - start
            if stop > 120:
                print("Downloaded {} chapters in {} minutes".format(
                    count, round((stop/60), 2)))
            else:
                print("Downloaded {} chapters in {} seconds".format(
                    count, round((stop), 2)))
        elif(resp == 4):
            print("Bye!")
        else:
            print("That won't work. Please make a valid choice")

    def writeMenu(self):
        while(True):
            print("Welcome to One-Punch-Py\n1: Download a single chapter\n2: Download many chapters\n3: Download many chapters into a single PDF\n4: Quit")
            resp = self.getInputAsNum("Please make a choice: ")
            self.doUserAction(resp)
            if(resp == 4):
                break


directory = './all-chapters'
DownloadManager(directory).writeMenu()
