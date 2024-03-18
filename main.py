from PIL import Image
import numpy as np
import os
import sys
import re
from queue import Queue
import threading
import random
import math
import logging

#   "Global" vars
base_dir = os.path.dirname(__file__)
original_images_dir = os.path.join(base_dir, "Originals")
char_dir = os.path.join(base_dir, "Character_Lists")
char_dir_nude = os.path.join(char_dir, "Nude")
char_dir_clothed = os.path.join(char_dir, "Clothed")
output_dir = os.path.join(base_dir, "Output")
# bg_colours = []


def process_image_queue(file_list):
    """
    Handles images and prepares them for spreading out of jobs
    :param file_list: List of images. Includes the fill path to image.
    :return: List of cut images. Sequence is preserved. FIFO.
    """
    try:
        q = Queue(maxsize=0)
        numthreads = min(15, len(file_list))
        results = [{} for _ in file_list]
        for i in range(len(file_list)):
            q.put((i, file_list[i]))

        for i in range(numthreads):
            process = threading.Thread(target=process_image, args=(q, results))
            process.daemon = True
            process.start()
        q.join()
        if len(file_list) > 0:
            print("All complete! Moving on.")
        return results
    except Exception as f:
        logging.error(f"An error occurred: {f}")


def process_image(q, results):
    """
    Cutting images based on parameters.
    :param q: Queue. Used for keeping results in order.
    :param results: Where to store the results to return
    :return: Completed queue.
    """
    while not q.empty():
        y01 = 0
        y11 = 1200
        work = q.get()
        print("New task started. " + str(work[0]) + "\n")
        clothed = []
        nude = False
        filename = work[1][0]
        cycled_once = False  # First image should always be nude
        im = Image.open(os.path.join(original_images_dir, filename))
        for _ in range(int(im.width / 1200)):
            im1 = im.crop((y01, 0, y11, 1600))
            y01 = y11
            y11 += 1200
            if not background_only(im1):
                if work[1][1]:
                    if not nude:
                        nude = im1
                    else:
                        clothed.append(im1)
                else:
                    if cycled_once:
                        clothed.append(im1)
            else:
                break
            cycled_once = True

        if work[1][1]:
            nude = im.crop((0, 0, 1200, 1600))

        if not nude:
            results[work[0]] = [clothed, filename]
        else:
            results[work[0]] = [nude, clothed, filename]
        q.task_done()
        print("New task done. " + str(work[0]) + "\n")
    return True


def preprocess_files():
    unmodified_images = sorted(
        [i for i in os.listdir(original_images_dir) if ".png" in i]
    )
    known_nudes = sorted(os.listdir(char_dir_nude))
    known_clothed = sorted(os.listdir(char_dir_clothed))
    unmodified_images_int_only = []  # [char_entry_validation(i) for i in known_nudes]
    entry_exists = []
    process_list = []

    for i in unmodified_images:
        charval = char_entry_validation(i)
        checking_filename = i[:-4]

        # Fresh entry, no nudes/clothes
        if (
                (checking_filename not in known_nudes)
                and (checking_filename not in known_clothed)
                and (charval not in unmodified_images_int_only)
        ):
            unmodified_images_int_only.append(charval)
            process_list.append([i, True])

        # Char is run once already, has an entry, but may be having extra costumes.
        elif checking_filename in known_nudes and (
                charval not in unmodified_images_int_only
        ):
            unmodified_images_int_only.append(charval)

        # Char has extra costumes. Folder uses first known image, so future new costumes should never match.
        # elif (
        #     (charval in unmodified_images_int_only)
        # ):
        else:
            if i not in os.listdir(
                    os.path.join(
                        char_dir_clothed, listdir_intmatch(os.listdir(char_dir_clothed), i)
                    )
            ):
                entry_exists.append([i, False])

    set1 = process_image_queue(process_list)
    set2 = process_image_queue(entry_exists)
    return set1, set2


def background_only(image):
    # Convert the image to a NumPy array
    image_array = np.asarray(image)

    # Check if all elements of the array are the same
    is_single_color = np.all(image_array == image_array[0])

    return is_single_color


def char_entry_validation(char_entry):
    """
    Takes a string, spits out first set of integers
    :param char_entry: Type:String
    :return: Int
    """
    return int(re.search(r"\d+", char_entry).group())


def listdir_intmatch(source, target):
    result = [j for j in source if str(char_entry_validation(target)) in j][0]
    return result


def sorting_files(imageset1, imageset2):
    for i in imageset1:
        nude_charsprite = i[0]
        nude_chardir = os.path.join(char_dir_nude, i[-1])[:-4]
        if not os.path.exists(nude_chardir):
            os.mkdir(nude_chardir)
        nude_charsprite.save(os.path.join(nude_chardir, i[-1]), "PNG")

        clothed_charsprite = i[1]
        clothed_chardir = os.path.join(char_dir_clothed, i[-1])[:-4]
        if not os.path.exists(clothed_chardir):
            os.mkdir(clothed_chardir)
        clothed_charsprite[0].save(os.path.join(clothed_chardir, i[-1]), "PNG")

    for i in imageset2:
        clothed_charsprite = i[0]
        charval = char_entry_validation(i[-1])
        chardir = os.listdir(char_dir_clothed)
        charsavedir = [
            char_dir_clothed + "\\" + j
            for j in chardir
            if charval == char_entry_validation(j)
        ]
        clothed_charsprite[0].save(os.path.join(charsavedir[0], i[-1]), "PNG")

    # print("done")


def folder_setup():
    if not os.path.exists(original_images_dir):
        print(
            "Missing original images source. Please make a folder called 'Originals' in the same place as this file, "
            "and drop your image sheets within, then run the script again."
        )
        sys.exit()
    if not os.path.exists(char_dir):
        os.makedirs(char_dir)
    if not os.path.exists(char_dir_nude):
        os.makedirs(char_dir_nude)
    if not os.path.exists(char_dir_clothed):
        os.makedirs(char_dir_clothed)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def request_images():
    while True:
        try:
            char_count = int(
                input(
                    f"How many characters do you want to merge? Integers only! You currently have "
                    f"{len(os.listdir(char_dir_nude))} characters in your list. Put the same number in to run auto-nude"
                    f"!: "
                )
            )
            if char_count < 0:
                raise ValueError("Negative integers are not allowed.")
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    master_list = []
    file_mashup_name = ""
    if char_count == len(os.listdir(char_dir_nude)):
        while True:
            checkall = input(
                "Same number of total files detected! Did you want to do a full nude/clothed lineup? N/C: "
            ).lower()[:1]
            if checkall in ["n", "c"]:
                if checkall == "n":
                    for i in os.listdir(char_dir_nude):
                        char_fullpath = os.path.join(char_dir_nude, i)
                        master_list.append(
                            Image.open(
                                os.path.join(
                                    char_fullpath, os.listdir(char_fullpath)[0]
                                )
                            )
                        )
                        file_mashup_name += f"{'&' if file_mashup_name else ''}({'_'.join([i[:3], 'N'])})"
                elif checkall == "c":
                    print("not done")
                    sys.exit()
                else:
                    master_list, file_mashup_name = request_images_manual(char_count)
                break
            else:
                raise ValueError("Invalid input. Try again.")
    else:
        master_list, file_mashup_name = request_images_manual(char_count)

    return master_list, file_mashup_name


def request_images_manual(char_count):
    file_mashup_name = ""
    master_list = []
    print("Manual selection time!")
    for _ in range(char_count):
        charval = 0
        v1 = True
        while v1:
            try:
                charval = int(input("Who's next? Integers only! : "))
                if charval < 0:
                    raise ValueError("Negative integers are not allowed.")
                for i in os.listdir(char_dir_nude):
                    if charval == char_entry_validation(i):
                        print(f"Character sheet no. {charval} found!")
                        v1 = False
                        break
            except ValueError:
                print("Invalid input. Please enter an integer.")

        while True:
            clothes = input("Should they wear clothes? Y/N: ").lower()[:1]
            if clothes in ["y", "n"]:
                if clothes == "y":
                    char_content = os.path.join(
                        char_dir_clothed,
                        str(
                            listdir_intmatch(os.listdir(char_dir_clothed), str(charval))
                        ),
                    )
                    if len(os.listdir(char_content)) > 1:
                        filefound = False
                        for file1 in os.listdir(char_content):
                            correct_file = input(
                                f'Is this the right file? "{file1}"  Y/N: '
                            ).lower()[:1]
                            verify = True
                            while verify:
                                if correct_file in ["y", "n"]:
                                    if correct_file == "y":
                                        master_list.append(
                                            Image.open(
                                                os.path.join(char_content, file1)
                                            )
                                        )
                                        filefound = True
                                    else:
                                        print("Understood. Trying again.")
                                    verify = False
                                else:
                                    print("Invalid input. Please enter Y or N.")
                        if not filefound:
                            print(
                                f"Last one of {charval} found. Since none was chosen, Aborting."
                            )
                            sys.exit()
                    else:
                        master_list.append(
                            Image.open(
                                os.path.join(char_content, os.listdir(char_content)[0])
                            )
                        )
                else:
                    char_content = os.path.join(
                        char_dir_nude,
                        str(
                            [i for i in os.listdir(char_dir_nude) if str(charval) in i][
                                0
                            ]
                        ),
                    )
                    master_list.append(
                        Image.open(
                            os.path.join(char_content, os.listdir(char_content)[0])
                        )
                    )
                file_mashup_name += (
                    f"{'&' if file_mashup_name else ''}"
                    f"({'_'.join([str(charval), 'C' if clothes == 'y' else 'N'])})"
                )
                break
            else:
                print("Invalid input. Please enter Y or N.")
    return master_list, file_mashup_name


def merge_images(images, filename):
    """
    Final Step. Combines individual image segments together.
    :param images: Image list.
    :param filename: Name of file. Expects '(000_C/N)&...', but if longer than254, replace with alnum string of X len.
    :return: None
    """
    base_width = 1200  # Don't modify
    base_height = 1600  # Don't modify
    rowmax = 10  # Final image width
    merged_width = base_width * len(images)
    merged_height = base_height
    if merged_width > base_width * rowmax:
        merged_width = base_width * rowmax
        merged_height = merged_height * math.ceil(len(images) / rowmax)
    merged_image = Image.new("RGB", (merged_width, merged_height))
    width = 0
    height = 0
    for im in images:
        merged_image.paste(im, (width, height))
        width += base_width
        if width >= base_width * rowmax:
            width = 0
            height += base_height
    filename = os.path.join(output_dir, filename)
    if len(filename) > 254:
        print(
            f"File name {filename}.png is too long. Replacing with a randomly generated string of numbers."
        )
        filename = os.path.join(output_dir, str(random.randint(1, 999999)))
    merged_image.save(f"{filename}.png", "PNG")
    print(f"File name {filename}.png saved!.")


def main():
    # Initial folder prerequisite checks
    folder_setup()

    # Start checking if images are properly broken apart
    imageset1, imageset2 = preprocess_files()
    sorting_files(imageset1, imageset2)

    # Request user settings
    master_list, final_name = request_images()
    merge_images(master_list, final_name)


if __name__ == "__main__":
    main()

#   TODO:
#   Add automation to auto-run all in directory for specific type (nude/clothed) -split files, one proc, one input/pass?
#   - Partially Done, only handles nude.
