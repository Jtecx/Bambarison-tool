from PIL import Image
import os


def filecheck(files, fileexist):
    for filename in files:
        if fileexist == int(filename[:3]):
            print(f"File containing the integer {fileexist} found: {filename}")
            return filename
    print(f"No file containing the integer {fileexist} found in the folder.")
    return ""


def nameprocessor(file_name, not_naked, filemashupname):
    return f"{'&' if filemashupname else ''}({'_'.join([file_name[:3], 'C' if not_naked else 'N'])})"


def imgparse(file_list):
    result_images = []
    for file, not_naked in file_list:
        im = Image.open(file)
        left = 0
        top = 0
        right = 1200
        bottom = 1600
        im1 = (
            im.crop((left + right, top, right + right, bottom))
            if not_naked
            else im.crop((left, top, right, bottom))
        )
        result_images.append(im1)
    return result_images


def imgmerge(images, filename):
    merged_image = Image.new("RGB", (1200 * len(images), 1600))
    width = 0
    for image in images:
        merged_image.paste(image, (width, 0))
        width += 1200
    merged_image.save(f"{filename}.png", "PNG")


def filefinder(files):
    while True:
        try:
            fileexist = int(input("Who's next? Integers only! : "))
            file1 = filecheck(files, fileexist)
            if file1:
                break
        except ValueError:
            print("Invalid input. Please enter an integer.")
    return file1


def imgrequest():
    current_dir = os.path.join(os.path.dirname(__file__), "Characters_List")
    files = os.listdir(current_dir)
    masterlist = []
    filemashupname = ""
    charcount = 0

    while True:
        try:
            charcount += int(
                input("How many chars do you want to merge? Integers only! : ")
            )
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    for _ in range(charcount):

        file1 = filefinder(files)

        while True:
            correctfile = input("Is this the right file? \"" + file1 + " \"  Y/N: ").lower()[:1]
            if correctfile in ["y", "n"]:
                if correctfile == "y":
                    break
                else:
                    files.remove(file1)
                    file1 = filefinder(files)
            else:
                print("Invalid input. Please enter Y or N.")

        while True:
            clothes = input("Should they wear clothes? Y/N: ").lower()[:1]
            if clothes in ["y", "n"]:
                masterlist.append([os.path.join(current_dir, file1), clothes == "y"])
                filemashupname += nameprocessor(file1, clothes == "y", filemashupname)
                break
            else:
                print("Invalid input. Please enter Y or N.")

    return masterlist, filemashupname


def main():
    masterlist, resultname = imgrequest()
    imgcomplete = imgparse(masterlist)
    imgmerge(imgcomplete, resultname)


if __name__ == "__main__":
    main()
