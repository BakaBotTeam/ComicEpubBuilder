import imghdr
import io
import json
import os
import sys
import traceback

from PIL import Image
from ebooklib import epub

PICA_COMIC_DOWNLOAD_DIR = os.getenv('APPDATA') + "/com.kokoiro.xyz/pica_comic/download"


def ehhiConvert(comic: str, comic_name: str, comic_authors: list):
    # EHentai / Hitomi / NHentai / Ht support
    print(f"Found (EHentai / Hitomi / NHentai / Wnacg) comic: {comic_name} by {', '.join(comic_authors)}")
    cover_image = os.path.join(comic, "cover.jpg")
    image_list = os.listdir(comic)
    for image in image_list:
        if image.startswith("cover") or image.endswith(".json"):
            image_list.remove(image)
    image_path_list = [os.path.join(comic, f"{i}.{image_list[0].split('.')[-1]}") for i in range(len(image_list) - 1)]

    print("Building epub book...")

    book = epub.EpubBook()
    book.set_identifier(os.path.split(comic)[-1])
    book.set_title(comic_name)
    book.set_language("en")

    for i in comic_authors:
        book.add_author(i)

    print("Adding cover to the book...")
    image_file = open(cover_image, 'rb').read()
    book.set_cover("cover.jpg", image_file, create_page=False)
    webp_warn = False

    content = [u'<html> <head></head> <body>']
    print("Adding images to the book...")
    for i in image_path_list:
        image_file = open(i, 'rb').read()
        image_type = imghdr.what(i)
        if image_type == "webp":
            if not webp_warn:
                webp_warn = True
                print("Adding webp to the book, that may take a while...")
            im = Image.open(i).convert("RGB")
            img_byte_arr = io.BytesIO()
            im.save(img_byte_arr, format='JPEG')
            image_file = img_byte_arr.getvalue()
        if image_type == "gif":
            print("GIF is not supported")
            return
        image = epub.EpubImage()
        image.file_name = "images/" + os.path.split(i)[-1]
        image.content = image_file
        book.add_item(image)
        content.append('<img src="images/{}"/>'.format(os.path.split(i)[-1]))
    content.append('</body> </html>')
    c1 = epub.EpubHtml(title=comic_name, file_name="chap_01.xhtml", lang="en")
    c1.content = ''.join(content)
    book.add_item(c1)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # basic spine
    book.spine = ["nav", c1]
    print("Writing to file...")
    epub.write_epub(f"{os.path.split(comic)[-1]}.epub", book)


def picacgConverter(comic: dict, comic_dir: str):
    comic_name = comic['comicItem']['title']
    comic_author = comic['comicItem']['author']
    print(f"Found Picacg comic: {comic_name} by {comic_author}")
    all_part = comic['chapters']
    all_part.reverse()
    downloaded_part = [i - 1 for i in comic['downloadedChapters']]
    cover_image = os.path.join(comic_dir, "cover.jpg")
    print("Building epub book...")

    book = epub.EpubBook()
    book.set_identifier(os.path.split(comic_dir)[-1])
    book.set_title(comic_name)
    book.set_language("en")
    book.add_author(comic_author)

    print("Adding cover to the book...")
    image_file = open(cover_image, 'rb').read()
    book.set_cover("cover.jpg", image_file, create_page=False)
    webp_warn = False
    book.spine = ["nav"]

    for i in downloaded_part:
        print(f"Found downloaded chapter {all_part[i]}")
        image_list = os.listdir(os.path.join(comic_dir, str(i + 2)))
        for image in image_list:
            if image.startswith("cover") or image.endswith(".json"):
                image_list.remove(image)
        image_path_list = [os.path.join(comic_dir, str(i + 2), f"{i2}.{image_list[0].split('.')[-1]}") for i2 in
                           range(len(image_list) - 1)]
        content = [u'<html> <head></head> <body>']
        print("Adding images to the book...")
        for i2 in image_path_list:
            image_file = open(i2, 'rb').read()
            image_type = imghdr.what(i2)
            if image_type == "webp":
                if not webp_warn:
                    webp_warn = True
                    print("Adding webp to the book, that may take a while...")
                im = Image.open(i2).convert("RGB")
                img_byte_arr = io.BytesIO()
                im.save(img_byte_arr, format='JPEG')
                image_file = img_byte_arr.getvalue()
            if image_type == "gif":
                print("GIF is not supported")
                return
            image = epub.EpubImage()
            image.file_name = f"images/{i + 2}/{os.path.split(i2)[-1]}"
            image.content = image_file
            book.add_item(image)
            content.append(f'<img src="images/{i + 2}/{os.path.split(i2)[-1]}"/>')
        content.append('</body> </html>')
        c1 = epub.EpubHtml(title=all_part[i], file_name=f"chap_{i}.xhtml", lang="en")
        c1.content = ''.join(content)
        book.add_item(c1)
        book.spine.append(c1)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.toc = [epub.Link(f"chap_{i}.xhtml", all_part[i], f"chap_{i}") for i in downloaded_part]

    # basic spine
    print("Writing to file...")
    epub.write_epub(f"{os.path.split(comic_dir)[-1]}.epub", book)


def jmConverter(comic: dict, comic_dir: str):
    comic_name = comic['comic']['name']
    comic_authors = comic['comic']['author']
    print(f"Found JMComic comic: {comic_name} by {', '.join(comic_authors)}")
    all_part = comic['comic']['epNames']
    downloaded_part = [i for i in comic['downloadedChapters']]
    cover_image = os.path.join(comic_dir, "cover.jpg")
    print("Building epub book...")

    book = epub.EpubBook()
    book.set_identifier(os.path.split(comic_dir)[-1])
    book.set_title(comic_name)
    book.set_language("en")

    for i in comic_authors:
        book.add_author(i)

    print("Adding cover to the book...")
    image_file = open(cover_image, 'rb').read()
    book.set_cover("cover.jpg", image_file, create_page=False)
    webp_warn = False
    book.spine = ["nav"]

    for i in downloaded_part:
        print(f"Found downloaded chapter {all_part[i]}")
        image_list = os.listdir(os.path.join(comic_dir, str(i + 1)))
        for image in image_list:
            if image.startswith("cover") or image.endswith(".json"):
                image_list.remove(image)
        image_path_list = [os.path.join(comic_dir, str(i + 1), f"{i2}.{image_list[0].split('.')[-1]}") for i2 in
                           range(len(image_list) - 1)]
        content = [u'<html> <head></head> <body>']
        print("Adding images to the book...")
        for i2 in image_path_list:
            image_file = open(i2, 'rb').read()
            image_type = imghdr.what(i2)
            if image_type == "webp":
                if not webp_warn:
                    webp_warn = True
                    print("Adding webp to the book, that may take a while...")
                im = Image.open(i2).convert("RGB")
                img_byte_arr = io.BytesIO()
                im.save(img_byte_arr, format='JPEG')
                image_file = img_byte_arr.getvalue()
            if image_type == "gif":
                print("GIF is not supported")
                return
            image = epub.EpubImage()
            image.file_name = f"images/{i + 1}/{os.path.split(i2)[-1]}"
            image.content = image_file
            book.add_item(image)
            content.append(f'<img src="images/{i + 1}/{os.path.split(i2)[-1]}"/>')
        content.append('</body> </html>')
        c1 = epub.EpubHtml(title=all_part[i], file_name=f"chap_{i}.xhtml", lang="en")
        c1.content = ''.join(content)
        book.add_item(c1)
        book.spine.append(c1)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.toc = [epub.Link(f"chap_{i}.xhtml", all_part[i], f"chap_{i}") for i in downloaded_part]

    # basic spine
    print("Writing to file...")
    epub.write_epub(f"{os.path.split(comic_dir)[-1]}.epub", book)


def main():
    # list all dir in Pica Comic Download Dir
    dirs = os.listdir(PICA_COMIC_DOWNLOAD_DIR)
    all_comic = []
    for dir in dirs:
        if os.path.isdir(os.path.join(PICA_COMIC_DOWNLOAD_DIR, dir)):
            all_comic.append(os.path.join(PICA_COMIC_DOWNLOAD_DIR, dir))

    if len(all_comic) == 0:
        print("No comic found, program will exit.")
        sys.exit(0)

    for comic in all_comic:
        try:
            comic_info = json.loads(open(os.path.join(comic, "info.json"), "rb").read())
            if "comic" in comic_info and "downloadedChapters" not in comic_info and "uploader" not in comic_info[
                "comic"]:
                comic_name = comic_info["comic"]["name"]
                comic_authors = comic_info["comic"]["artists"]
                ehhiConvert(comic, comic_name, comic_authors)
            elif "gallery" in comic_info:
                comic_name = comic_info["gallery"]["title"]
                comic_authors = comic_info["gallery"]["tags"]["artist"]
                ehhiConvert(comic, comic_name, comic_authors)
            elif "comicID" in comic_info and comic_info["comicID"].startswith("nhentai"):
                comic_name = comic_info["title"]
                comic_authors = ["N/A"]
                ehhiConvert(comic, comic_name, comic_authors)
            elif "comic" in comic_info and "uploader" in comic_info["comic"]:
                comic_name = comic_info["comic"]["name"]
                comic_authors = ["N/A"]
                ehhiConvert(comic, comic_name, comic_authors)
            elif "comicItem" in comic_info:
                picacgConverter(comic_info, comic)
                pass
            elif "comic" in comic_info and "downloadedChapters" in comic_info:
                jmConverter(comic_info, comic)
                pass
            else:
                print("Unsupported comic: " + os.path.split(comic)[-1])
                continue
        except:
            print("Unexpected error")
            print(sys.exc_info())
            traceback.print_exc()


if __name__ == '__main__':
    main()
