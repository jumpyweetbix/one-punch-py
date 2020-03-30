import requests
import re
import os
from PIL import Image
from io import BytesIO
import time
from scipy.spatial import distance as dist

class Page:
    def __init__(self, url):
        self.url = url

    #   Find all image urls on the page using a regex pattern
    #   Returns a list of all urls found
    def getImageUrls(self):
        page = requests.get(self.url).text
        # pattern = r'(https\:\/\/1\S+[png|jpg])\">'
        pattern = r'(https?\:\/\/[1|2]\S+[png|jpg|=s0])\" '
        image_urls = re.findall(pattern, page)
        del page

        return(image_urls)

    #   Returns a response object for an image given a url
    def getImage(self, url):
        try:
            resp = requests.get(url, stream=True)
            return resp

        except:
            raise ValueError("Could not getImage\nURL:%s\n" % self.url)

    #   Find all image urls on a page, then loop through and create a list of response objects
    def getImages(self):
        try:
            image_urls = self.getImageUrls()
            images = []
            seen = []
            for i in range(0, len(image_urls)):
                if (image_urls[i] not in seen):
                    progress = "  working%s" % (i*".")
                    print(progress+"\r", end="")

                    images.append(self.getImage(image_urls[i]))
                    seen.append(image_urls[i])

            print("Got %d images from %s" % (len(images), self.url))
            return images

        except:
            raise ValueError("failed to get images")



class Chapter:
    def __init__(self, url, num, dir):
        self.url = url
        self.num = num
        self.dir = dir



    #   Use a comparison algorithm to find the distance between two histograms 
    def compareImages(self, hist1, hist2):
        d = dist.cityblock(hist1, hist2)
        
        #   Arbitrary value, that seems to be best for identifying duplicate images
        #   Much lower and you will start to notice false positives (images that aren't duplicates will be discarded)
        return(d < 90000)
        
    #   Creates a page object and gets a list of response objects
    #   Converts each object into a PIL Image object, then discards duplicates if they are next to each other
    #   Returns a list of Image objects
    def getImageFiles(self):
        page = Page(self.url)
        images = page.getImages()
        img_files = []
        first = True
        for image in images:
            img = Image.open(BytesIO(image.content)).convert('RGB')
            img_hist = img.histogram()

            if first:
                seen = img_hist
                first = False
                img_files.append(img)
                continue

            result = self.compareImages(img_hist, seen)
            if(not result):
                img_files.append(img)
                seen = img_hist
            else:
                print("found likely duplicate image - skipping")
                
        return(img_files)

    #   Gets a list of Image objects and saves them into a pdf
    def getChapter(self):
        print("Downloading chapter {}" .format(self.num))
        img_files = self.getImageFiles()
        save_dir = "%schapter-%s.pdf" % (self.dir, self.num)

        try:
            img_files[0].save(save_dir, "PDF", resolution=100.0,
                              save_all=True, append_images=img_files[1:])
            del img_files
            os.system('cls')

        except:
            raise ValueError(
                "Failed to save chapter {}".format(self.num))



class Downloader:
    def __init__(self, dir, comic_name):
        self.dir = dir
        self.comic_name = comic_name

    #   Ensures chapter directory is created and formatted correctly
    def getChapDir(self,):
        chap_dir = "{}/{}/".format(self.dir, self.comic_name)

        if not os.path.exists(chap_dir):
            os.makedirs(chap_dir)

        return(chap_dir)

    #   Returns chapter number, found using regex on a url
    def getChapNum(self, url):
        # pat = r'[chapter|issue]-(\d+)'
        pat = r'[chapter|issue]-(\d+)'
        num = re.findall(pat, url)[0]
        return(num)

    #   Downloads a single chapter given a url
    def downloadChapter(self, url):
        num = self.getChapNum(url)
        chap_dir = self.getChapDir()
        chapter = Chapter(url, num, chap_dir)
        chapter.getChapter()

    #   Returns a list of chapter urls that are between a given minimum and maximum value
    def getChapterUrlsBetween(self, min, max):

        if self.comic_name == 'one-punch-man':
            chapter_urls = self.getOnePunchChapterUrls()
        else:
            chapter_urls = self.getComicChapterUrls()
        
        seen = []
        wanted_urls = []

        for chap_url in chapter_urls:
            try:
                num = self.getChapNum(chap_url)
            except:
                print("couldn't get {}\ncouldn't find chapter number".format(chap_url))
                continue
            if not chap_url in seen:
                seen.append(chap_url)
            else:
                continue

            if '-' in num:
                num = re.findall(r'\d+', num)[0]


            if (min <= int(num) and int(num) <= max):
                    wanted_urls.append(chap_url)


        return sorted(wanted_urls)

    #   Gets images from many chapters between a minimum and maximum value
    #   Combines these images into a single pdf
    def downloadPdfBetween(self, min, max):
        img_files = []
        urls = self.getChapterUrlsBetween(min, max)
        print("Combining %d chapters"%len(urls))
        for url in urls:
            num = self.getChapNum(url)
            dir = self.getChapDir()
            chapter = Chapter(url, num, dir)
            img_files = img_files + chapter.getImageFiles()
        
        save_dir = "%schapters-%sto%s.pdf" % (self.getChapDir(), min, max)

        try:
            img_files[0].save(save_dir, "PDF", resolution=100.0,
                                save_all=True, append_images=img_files[0:])
            del img_files
            os.system('cls')
            print("Finished! Combined %d chapters"%len(urls))
            return len(urls)
        except:
            raise ValueError("Failed to download mass PDF")

    #   Downloads chapters between a minimum and maximum value
    def downloadChaptersBetween(self, min, max):
        print("Downloading chapters {} to {}".format(min, max))
        chapter_urls = self.getChapterUrlsBetween(min, max)
        for url in chapter_urls:
            print("Getting %s" % url)
            self.downloadChapter(url)

        return len(chapter_urls)

    #   Returns a chapter url given the chapter number
    def getOnePunchChapterUrl(self, num):
        url = 'https://ww3.one-punchman.com/manga/one-punch-man-chapter-%d/' % (
            num)
        return url

    #   Returns a list of all chapter urls.
    def getOnePunchChapterUrls(self):
        page = requests.get('https://ww3.one-punchman.com/').text
        # pattern = r'(https\:\/\/ww3.+chapter-\S+)\">'
        pattern = r'href=\"(https\:\/\/ww3\S+chapter-\S+)/'
        chapter_urls = re.findall(pattern, page)
        del page
        return chapter_urls

    def getComicChapterUrls(self):
        page = requests.get('https://viewcomics.me/comic/{}'.format(self.comic_name)).text
        pattern = r'(https\S+{}\S+)\"'.format(self.comic_name)
        chapter_urls = re.findall(pattern, page)
        for idx in range(0,len(chapter_urls)):
            chapter_urls[idx] = '{}/full'.format(chapter_urls[idx])

        del page
        return chapter_urls

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
        downloader = Downloader(self.dir, 'one-punch-man')
        if(resp == 1):
            url_num = self.getInputAsNum(
                'What chapter number would you like to download?\n')
            url = downloader.getOnePunchChapterUrl(url_num)
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
            count = downloader.downloadPdfBetween(min, max)
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
test = Downloader(directory, 'extraordinary-x-men')
test.downloadChaptersBetween(1, 5)
# for url in url_list:
#     test.downloadChapter(url)
# DownloadManager(directory).writeMenu()
