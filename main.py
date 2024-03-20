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

# "Global" vars
base_dir = os.path.dirname(__file__)
original_images_dir = os.path.join(base_dir, "Originals")
char_dir = os.path.join(base_dir, "Character_Lists")
char_dir_nude = os.path.join(char_dir, "Nude")
char_dir_clothed = os.path.join(char_dir, "Clothed")
char_dir_entry = os.path.join(char_dir, "Entry_Values")
output_dir = os.path.join(base_dir, "Output")
bg_colours = [[239, 239, 239, 255], [230, 230, 230, 255], [229, 229, 229, 255]]
# White-ish grey, darker grey, and slightly more different darker grey.


# Helper functions
def char_entry_validation(char_entry):
    """
    Takes a string, spits out first set of integers
    :param char_entry: Type:String
    :return: Int
    """
    return int(re.search(r"\d+", char_entry).group())


def listdir_int_match(source, target):
    """
    Function to return first matching int file/folder name from list.
    :param source: List of directory contents.
    :param target: String to match against.
    :return: String of int value.
    """
    try:
        result = [j for j in source if str(char_entry_validation(target)) in j][0]
    except IndexError:
        print(f"{source} | {target}")
        result = "0"
    return result


def img_to_numpy(image):
    """
    Converts Image to numpy, and skips over the annoying IDE warnings about unexpected type.
    :param image: Image type
    :return: Numpy array
    """
    return np.asarray(image)


def background_only(image):
    """
    Checks for if the image is entirely background, no char sprites.
    :param image: Image type. Takes in image to check.
    :return: Boolean
    """
    # Convert the image to a NumPy array
    image_array = img_to_numpy(image)

    # Check if all elements of the array are the same
    is_single_color = np.all(image_array == image_array[0])

    return is_single_color


def process_list_queue(file_list, func_proc):
    """
    Handles images and prepares them for spreading out of jobs
    :param file_list: List of images. Includes the fill path to image.
    :param func_proc: Function to multi-thread.
    :return: List of cut images. Sequence is preserved. FIFO.
    """
    try:
        q = Queue(maxsize=0)
        numthreads = min(15, len(file_list))
        results = [{} for _ in file_list]
        for i in range(len(file_list)):
            q.put((i, file_list[i]))

        for i in range(numthreads):
            process = threading.Thread(target=func_proc, args=(q, results))
            process.daemon = True
            process.start()
        q.join()
        if len(file_list) > 0:
            print("All complete! Moving on.")
        return results
    except Exception as f:
        logging.error(f"An error occurred: {f}")


# Step 1
def folder_setup():
    """
    Sets up and checks folder structure of all needed  directories.
    :return: None
    """
    if not os.path.exists(original_images_dir):
        print(
            "Missing original images source. Please make a folder called 'Originals' in the same place as this file, "
            "and drop your image sheets within, then run the script again."
        )
        print(f"{base_dir}")
        sys.exit()
    if len(os.listdir(original_images_dir)) == 0:
        print("No images detected. Script ending.")
        sys.exit()
    if not os.path.exists(char_dir):
        os.makedirs(char_dir)
    if not os.path.exists(char_dir_nude):
        os.makedirs(char_dir_nude)
    if not os.path.exists(char_dir_clothed):
        os.makedirs(char_dir_clothed)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(char_dir_entry):
        os.makedirs(char_dir_entry)


# Step 2
def preprocess_files():
    """
    Pre-cuts new images and sorts them into respective files based on expected type.
    :return: None
    """
    unmodified_images = sorted(
        [i for i in os.listdir(original_images_dir) if ".png" in i]
    )
    known_nudes = sorted(os.listdir(char_dir_nude))
    known_clothed = sorted(os.listdir(char_dir_clothed))
    unmodified_images_int_only = []
    entry_exists = []
    process_list = []

    for i in unmodified_images:
        char_val = char_entry_validation(i)
        checking_filename = i[:-4]

        # Fresh entry, no nudes/clothes
        if (
            (checking_filename not in known_nudes)
            and (checking_filename not in known_clothed)
            and (char_val not in unmodified_images_int_only)
        ):
            unmodified_images_int_only.append(char_val)
            process_list.append([i, True])

        # Char is run once already, has an entry, but may be having extra costumes.
        elif checking_filename in known_nudes and (
            char_val not in unmodified_images_int_only
        ):
            unmodified_images_int_only.append(char_val)

        # Char has extra costumes. Folder uses first known image, so future new costumes should never match.
        else:
            # Path doesn't exist on first run with multi-costume. It's okay, we can just get the expected file_dir from
            # original.
            clothed_pre_creation_check = os.listdir(char_dir_clothed)
            if not clothed_pre_creation_check:
                clothed_pre_creation_check = sorted(os.listdir(original_images_dir))

            # Path only doesn't exist on first run, and this else only for multi-costumes.
            path_simplified = os.path.join(
                char_dir_clothed, listdir_int_match(clothed_pre_creation_check, i)
            )
            if not os.path.exists(path_simplified) and not os.path.exists(
                path_simplified + i
            ):
                entry_exists.append([i, False])
            else:
                if i not in os.listdir(path_simplified):
                    entry_exists.append([i, False])

    process_list_queue(process_list, process_image)
    process_list_queue(entry_exists, process_image)


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
            char_val = char_entry_validation(filename)
            char_dir_2 = os.listdir(char_dir_clothed)
            char_save_dir = [
                os.path.join(char_dir_clothed, j)
                for j in char_dir_2
                if char_val == char_entry_validation(j)
            ]
            clothed[0].save(os.path.join(char_save_dir[0], filename), "PNG")

        else:
            run_this = [[nude, char_dir_nude], [clothed[0], char_dir_clothed]]
            ran_once = False
            for i in run_this:
                process_image_2(i[0], i[1], filename)
                if not ran_once:
                    char_entry_img_extract(i[0], filename)

        q.task_done()
        print("New task done. " + str(work[0]) + "\n")
    return True


def process_image_2(char_sprite, image_dir, filename):
    char_dir_exists = os.path.join(image_dir, filename)[:-4]
    if not os.path.exists(char_dir_exists):
        os.mkdir(char_dir_exists)
    char_sprite.save(os.path.join(char_dir_exists, filename), "PNG")


def char_entry_img_extract(img_base, filename2):
    """
    Extracts the char entry number as pixels in the top left, and saves them for separate use.
    :return: None
    """
    char_sheet_init_dim = (0, 0, 125, 100)
    target_color = np.array(bg_colours[0])
    filename = os.path.join(
        char_dir_entry, str(char_entry_validation(filename2)) + ".png"
    )
    if not os.path.exists(filename):
        im1 = img_base.crop(char_sheet_init_dim)
        im1 = im1.convert("RGBA")
        image_array = img_to_numpy(im1)
        image_array = image_array.copy()
        mask = np.all(image_array == target_color, axis=-1)
        image_array[mask, 3] = 0
        modified_image = Image.fromarray(image_array)
        modified_image.save(f"{filename}", "PNG")
        # print(f"{i} character sheet number has been extracted and saved.")


# Step 3
def request_images():
    """
    User inputs.
    :return: master_list: List of images to grab,
    file_mashup_name: Name of file to save merged as.
    """
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
            try:
                checkall = input(
                    "Same number of total files detected! Did you want to do a full nude/clothed lineup? N/C: "
                ).lower()[:1]
                if checkall in ["n", "c"]:
                    if checkall == "n":
                        for i in os.listdir(char_dir_nude):
                            char_full_path = os.path.join(char_dir_nude, i)
                            master_list.append(
                                Image.open(
                                    os.path.join(
                                        char_full_path, os.listdir(char_full_path)[0]
                                    )
                                )
                            )
                            file_mashup_name += (
                                f"{'&' if file_mashup_name else ''}"
                                f"({'_'.join([str(char_entry_validation(i)), 'N'])})"
                            )
                    elif checkall == "c":
                        merge_images_clothed()
                    else:
                        master_list, file_mashup_name = request_images_manual(
                            char_count
                        )
                    break
                else:
                    raise ValueError("Invalid input. Try again.")
            except ValueError:
                print("Invalid input.")
    else:
        master_list, file_mashup_name = request_images_manual(char_count)

    return master_list, file_mashup_name


def request_images_manual(char_count):
    """
    Manual selection of images to merge together.
    :param char_count: Number of chars to merge together.
    :return: master_list: List of images to grab,
    file_mashup_name: Name of file to save merged as.
    """
    file_mashup_name = ""
    master_list = []
    print("Manual selection time!")
    while char_count != 0:
        print(f"You have {char_count} left.")
        char_count -= 1
        char_val = 0
        v1 = True
        while v1:
            try:
                char_val = int(input("Who's next? Integers only! : "))
                if char_val < 0:
                    raise ValueError("Negative integers are not allowed.")
                for i in os.listdir(char_dir_nude):
                    if char_val == char_entry_validation(i):
                        print(f"Character sheet no. {char_val} found!")
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
                            listdir_int_match(
                                os.listdir(char_dir_clothed), str(char_val)
                            )
                        ),
                    )
                    if len(os.listdir(char_content)) > 1:
                        file_found = False
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
                                        file_mashup_name += (
                                            f"{'&' if file_mashup_name else ''}"
                                            f"({'_'.join([str(char_val), 'C'])})"
                                        )
                                        file_found = True
                                        break
                                    else:
                                        print("Understood. Trying again.")
                                    verify = False
                                else:
                                    print("Invalid input. Please enter Y or N.")
                            if file_found:
                                break
                        if not file_found:
                            print(
                                f"Last one of Character entry no.{char_val} found. Since none was chosen, looping."
                            )
                            char_count += 1
                    else:
                        master_list.append(
                            Image.open(
                                os.path.join(char_content, os.listdir(char_content)[0])
                            )
                        )
                        file_mashup_name += (
                            f"{'&' if file_mashup_name else ''}"
                            f"({'_'.join([str(char_val), 'C'])})"
                        )
                else:
                    char_content = os.path.join(
                        char_dir_nude,
                        str(
                            [
                                i
                                for i in os.listdir(char_dir_nude)
                                if str(char_val) in i
                            ][0]
                        ),
                    )
                    master_list.append(
                        Image.open(
                            os.path.join(char_content, os.listdir(char_content)[0])
                        )
                    )
                    file_mashup_name += (
                        f"{'&' if file_mashup_name else ''}"
                        f"({'_'.join([str(char_val),'N'])})"
                    )
                break
            else:
                print("Invalid input. Please enter Y or N.")
    return master_list, file_mashup_name


# Step 4
def merge_images(images, filename):
    """
    Final Step. Combines individual image segments together.
    :param images: Image list.
    :param filename: Name of file. Expects '(000_C/N)&...', but if longer than254, replace with alpha-numeric string
    of X len.
    :return: None
    """
    base_width = 1200  # Don't modify
    base_height = 1600  # Don't modify
    row_max = 10  # Final image width
    merged_width = base_width * len(images)
    merged_height = base_height
    if merged_width > base_width * row_max:
        merged_width = base_width * row_max
        merged_height = merged_height * math.ceil(len(images) / row_max)
    merged_image = Image.new("RGB", (merged_width, merged_height))
    width = 0
    height = 0
    for im in images:
        merged_image.paste(im, (width, height))
        width += base_width
        if width >= base_width * row_max:
            width = 0
            height += base_height
    filename = os.path.join(output_dir, filename)
    if len(filename) > 254:
        print(
            f"File name {filename}.png is too long. Replacing with a randomly generated string of numbers."
        )
        filename = os.path.join(output_dir, str(random.randint(1, 999999))) + "_nude"
    merged_image.save(f"{filename}.png", "PNG")
    print(f"File name {filename}.png saved!.")


def merge_images_clothed():
    """
    Merge variant. Chars each have their own row.
    :return: None
    """
    base_height = len(os.listdir(char_dir_clothed)) * 1600
    base_width = 0
    for i in os.listdir(char_dir_clothed):
        max_width_base = len(os.listdir(os.path.join(char_dir_clothed, i)))
        base_width = max(base_width, max_width_base)
    base_width = base_width * 1200
    merged_image = Image.new("RGB", (base_width, base_height))
    x = 0  # width
    y = 0  # height
    for i in os.listdir(char_dir_clothed):
        for j in os.listdir(os.path.join(char_dir_clothed, i)):
            merging_hold = Image.open(os.path.join(char_dir_clothed, i, j))
            merged_image.paste(merging_hold, (y, x))
            y += 1200
        x += 1600
        y = 0

    filename = os.path.join(output_dir, str(random.randint(1, 999999))) + "_clothed"
    merged_image.save(f"{filename}.png", "PNG")
    print("Done.")
    sys.exit()


# Main
def main():
    # Initial folder prerequisite checks
    folder_setup()

    # Reads and processes images. If new originals are found, or new clothing, process and break them down.
    preprocess_files()

    # Request user settings
    master_list, final_name = request_images()
    merge_images(master_list, final_name)


if __name__ == "__main__":
    main()

# TODO:
#
# Pixel background strip colour?
