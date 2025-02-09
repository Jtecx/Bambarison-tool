#!/usr/bin/python3
import time
from PIL import Image
import cv2
import numpy as np
import os
import sys
import math
import logging
from pathlib import Path
from CoreSharedLibs import csl

# You can get this (^) by running
# pip install BTCoreSharedLibs


# "Global" vars
class GlobalVars:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.original_images_dir = self.base_dir / "Originals"
        self.char_dir = self.base_dir / "Character_Lists"
        self.char_dir_nude = self.char_dir / "Nude"
        self.char_dir_clothed = self.char_dir / "Clothed"
        self.char_dir_entry = self.char_dir / "Entry_Values"
        self.output_dir = self.base_dir / "Output"
        self.bg_colours = [
            [239, 239, 239, 255],
            [230, 230, 230, 255],
            [229, 229, 229, 255],
        ]
        # White-ish grey, darker grey, and slightly more different darker grey.


script_globals = GlobalVars()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S", level=logging.INFO
)


# Shared re-usable functions
def file_finder(char_val):  # , nude):
    """
    Finds if a file exists or not.
    :param char_val: Int, character sheet
    :return: v1 for loop breaking if found, and which file matched.
    """
    v1 = False
    entry = ""
    # if nude:
    char_dir = sorted(script_globals.char_dir_nude.glob("*"))
    # else:
    #     char_dir = script_globals.char_dir_clothed.walk()
    for i in char_dir:
        entry = i.name
        test_against = csl.char_entry_value_strip(entry)
        if char_val == test_against:
            print(f"Character sheet no. {char_val} found!")
            v1 = True
            break
    logging.info(entry)
    return v1, entry


def image_validation(clothed_check, i=-1):
    """
    Image validation for clothed results.
    :param clothed_check: List, list of dirs matching the char int requested.
    :param i: Int, character entry number.
    :return: Exact file name (str), path to file(Str/Path), and if file was found (Bool).
    """
    file_name = ""
    file_path = ""
    file_found = False
    if len(clothed_check) > 1:
        for file1 in clothed_check:
            verify = True
            while verify:
                correct_file = input(
                    f'Is this the right file? "{file1.name}"  Y/N: '
                ).lower()[:1]
                if correct_file in ["y", "n"]:
                    if correct_file == "y":
                        file_name = file1.stem
                        file_path = file1
                        file_found = True
                        break
                    else:
                        print("Understood. Trying again.")
                    verify = False
                else:
                    logging.warning("Invalid input. Please enter Y or N.")
            if file_found:
                break
        if not file_found:
            logging.warning(f"Last one of Character entry no.{i} found.")
    else:
        file_name = clothed_check[0].stem
        file_path = clothed_check[0]
        file_found = True

    return file_name, file_path, file_found


# Step 1
def folder_setup():
    """
    Sets up and checks folder structure of all needed directories.
    :return: None
    """
    directories = [
        script_globals.char_dir,
        script_globals.char_dir_nude,
        script_globals.char_dir_clothed,
        script_globals.output_dir,
        script_globals.char_dir_entry,
    ]

    if not script_globals.original_images_dir.exists():
        logging.warning(
            "Missing original images source. Please make a folder called 'Originals' in the same place as this file, "
            "and drop your image sheets within, then run the script again."
        )
        print(f"Current Directory: {script_globals.base_dir}")
        sys.exit()

    for directory in directories:
        if not directory.exists():
            os.makedirs(directory)


# Step 2
def preprocess_files():
    """
    Pre-cuts new images and sorts them into respective files based on expected type.
    :return: None
    """
    unmodified_images = sorted(
        [i for i in script_globals.original_images_dir.glob("*.png")]
    )
    known_nudes = sorted(script_globals.char_dir_nude.glob("*"))
    known_clothed = sorted(script_globals.char_dir_clothed.glob("*"))
    unmodified_images_int_only = []
    known_nudes_filenames = [path1.stem for path1 in known_nudes]
    known_clothed_filenames = [
        file_path.stem
        # for file_path2 in list(known_clothed.rglob("*"))
        for path2 in known_clothed
        for file_path in path2.glob("*")
    ]
    # Path doesn't exist on first run with multi-costume. It's okay, we can just get the expected file_dir from
    # original.
    clothed_pre_creation_check = sorted(script_globals.char_dir_clothed.glob("*"))
    if not clothed_pre_creation_check:
        clothed_pre_creation_check = sorted(
            script_globals.original_images_dir.glob("*")
        )
    entry_exists = []
    process_list = []

    for image_path in unmodified_images:
        checking_filename = image_path.stem
        char_val = csl.char_entry_value_strip(checking_filename)

        # Fresh entry, no nudes/clothes
        if (
            checking_filename not in known_nudes_filenames
            and checking_filename not in known_clothed_filenames
            and char_val not in unmodified_images_int_only
        ):
            unmodified_images_int_only.append(char_val)
            process_list.append([image_path, True])

        # Char is run once already, has an entry, but may be having extra costumes.
        elif checking_filename in known_nudes and (
            char_val not in unmodified_images_int_only
        ):
            unmodified_images_int_only.append(char_val)

        # Char has extra costumes. Folder uses first known image, so future new costumes should never match.
        else:
            # Path doesn't exist on first run with multi-costume. It's okay, we can just get the expected file_dir from
            # original.
            # clothed_pre_creation_check = list(script_globals.char_dir_clothed.iterdir())
            # if not clothed_pre_creation_check:
            #     clothed_pre_creation_check = list(
            #         script_globals.original_images_dir.iterdir()
            #     )

            # Path only doesn't exist on first run, and this else only for multi-costumes.
            path_simplified = script_globals.char_dir_clothed / csl.listdir_int_match(
                clothed_pre_creation_check, image_path.name
            )
            if (
                not path_simplified.exists()
                and not (path_simplified / image_path.name).exists()
            ):
                entry_exists.append([image_path, False])
            else:
                temp1 = sorted(path_simplified.glob("*"))
                temp2 = image_path.name[:-4]
                for i in range(len(temp1)):
                    temp3 = temp1[i].name
                    if temp2 in temp3:
                        break
                    elif i + 1 == len(temp1):
                        entry_exists.append([image_path, False])

    # logging.warning("1")
    csl.process_list_queue(process_list, process_image)  # looped
    # logging.warning("2")
    csl.process_list_queue(entry_exists, process_image)
    # logging.warning("3")


# noinspection PyUnusedLocal
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
        logging.info("New task started. %s", str(work[0]))
        clothed = []
        nude = False
        filedir = work[1][0]
        filename = filedir.stem
        cycled_once = False  # First image should always be nude
        im = Image.open(filedir)
        if (im.width % 1200 > 0) or (im.height % 1600 > 0):
            logging.warning(
                "%s is not a proper sheet. Dimensions should be H = 1600, "
                "W = 1200, or any multiple of W for character sheets. This one will be skipped.",
                filename,
            )
            q.task_done()
        for _ in range(int(im.width / 1200)):
            im1 = im.crop((y01, 0, y11, 1600))
            y01 = y11
            y11 += 1200
            # im1.show()
            if not csl.background_only(im1):
                if work[1][1]:
                    if not nude:
                        nude = im1
                    else:
                        clothed.append(im1)
                else:
                    if cycled_once:
                        clothed.append(im1)
            cycled_once = True

        # if work[1][1]:
        #     nude = im.crop((0, 0, 1200, 1600))

        if not nude:
            char_val = csl.char_entry_value_strip(filename)
            char_dir_2 = list(script_globals.char_dir_clothed.glob("*"))
            char_save_dir = [
                dir_entry
                for dir_entry in char_dir_2
                if char_val == csl.char_entry_value_strip(dir_entry.name)
            ]
            clothed[0].save(str(char_save_dir[0] / filename) + ".png", "PNG")

        else:
            run_this = [
                [nude, script_globals.char_dir_nude],
                [clothed, script_globals.char_dir_clothed],
            ]
            ran_once = False
            counter = 0
            for i in run_this:
                if isinstance(i[0], list):
                    for j in i[0]:
                        process_image_2(j,i[1],filename, filename + str(counter))
                        counter += 1
                else:
                    process_image_2(i[0], i[1], filename)
                if not ran_once:
                    char_entry_img_extract(i[0], filename)
                    ran_once = True

        q.task_done()
        logging.info("New task done. %s", str(work[0]))
    return True


# noinspection PyBroadException
def process_image_2(char_sprite, image_dir, filebasedir, altclothes = ""):
    try:
        # Construct the full path including the filename
        char_dir_exists = Path(image_dir) / filebasedir

        # Create the directory if it doesn't exist
        if not char_dir_exists.exists():
            char_dir_exists.mkdir(
                parents=True, exist_ok=True
            )  # Create parent directories if they don't exist
            # Set permissions for the directory (read, write, execute for owner, read and execute for group and others)
            char_dir_exists.chmod(0o755)  # Adjust permissions as needed

        # Save the image inside the directory
        if altclothes:
            char_sprite.save(str(char_dir_exists / altclothes) + ".png", "PNG")
        else:
            char_sprite.save(str(char_dir_exists / filebasedir) + ".png", "PNG")
        filemade = open(char_dir_exists/filebasedir, "w")
        filemade.close()
    except Exception:
        logging.exception("Error: ")


def char_entry_img_extract(img_base, filename2):
    """
    Extracts the char entry number as pixels in the top left, and saves them for separate use.
    :return: None
    """
    char_sheet_init_dim = (0, 0, 125, 100)
    target_color = np.array(script_globals.bg_colours[0])
    filename = (
        script_globals.char_dir_entry / f"{csl.char_entry_value_strip(filename2)}.png"
    )
    if not filename.exists():
        im1 = img_base.crop(char_sheet_init_dim)
        im1 = im1.convert("RGBA")
        image_array = csl.img_to_numpy(im1)
        image_array = image_array.copy()
        mask = np.all(image_array == target_color, axis=-1)
        image_array[mask, 3] = 0
        modified_image = Image.fromarray(image_array)
        modified_image.save(filename, "PNG")
        # logging.info("%s character sheet number has been extracted and saved.", filename2)


# Step 2.5
def begin_interface_opt():
    valid_entries = [i + 1 for i in range(2)]
    while True:
        try:
            chosen_val = int(
                input(
                    "What job are you running?"
                    "\n 1 for comparing a list of chars"
                    # "\n 2 for comparing a singular char against multiple"
                    "\n Input: "
                )
            )
            if chosen_val in valid_entries:
                break
            else:
                raise ValueError
        except ValueError:
            logging.warning("Input is invalid. Integers ONLY.")

    return chosen_val


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
                    f"{len(list(script_globals.char_dir_nude.glob('*')))} characters in your list. Put the same number "
                    f"in to run auto-nude!: "
                )
            )
            if char_count < 0:
                raise ValueError("Negative integers are not allowed.")
            break
        except ValueError:
            logging.warning("Invalid input. Please enter an integer.")

    char_dir_nude_list = sorted(script_globals.char_dir_nude.glob("*"))
    if char_count == len(list(char_dir_nude_list)):
        print("Same number of total files detected!")
        master_list, file_mashup_name = nude_or_clothed(char_dir_nude_list, char_count)
    else:
        # sequential = input("Is this sequential or random? Y/N: ").lower()[:1]
        # if sequential in ["y", "n"]:
        #     if sequential == "n":
        master_list, file_mashup_name = request_images_manual(char_count)
            # else:
            #     master_list, file_mashup_name = nude_or_clothed(char_dir_nude_list, char_count)

    return master_list, file_mashup_name


def nude_or_clothed(char_dir_nude_list, char_count):
    master_list = []
    file_mashup_name = ""
    while True:
        try:
            checkall = input(
                "Did you want to do a full nude/clothed lineup? N/C: "
            ).lower()[:1]
            if checkall in ["n", "c"]:
                if checkall == "n":
                    for i in char_dir_nude_list:
                        char_full_path = i
                        master_list.append(
                            Image.open(
                                char_full_path / next(char_full_path.glob("*.png"))
                            )
                        )
                        file_mashup_name += (
                            f"{'&' if file_mashup_name else ''}"
                            f"({'_'.join([str(csl.char_entry_value_strip(i.name)), 'N'])})"
                        )
                elif checkall == "c":
                    merge_images_clothed()
                # else:
                #     master_list, file_mashup_name = request_images_manual(
                #         char_count
                #     )
                break
            else:
                raise ValueError("Invalid input. Try again.")
        except ValueError:
            logging.warning("Invalid input.")

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
        while True:
            try:
                char_val = csl.validate_int_input()
                result, char_val = file_finder(char_val)
                if result:
                    break
                else:
                    raise ValueError
            except ValueError:
                logging.warning("File not found..")

        while True:
            clothes = input("Should they wear clothes? Y/N: ").lower()[:1]
            if clothes in ["y", "n"]:
                if clothes == "y":
                    char_content = script_globals.char_dir_clothed / char_val
                    char_content_data = sorted(char_content.glob("*.png"))
                    file_name, file_path, re_status = image_validation(
                        char_content_data, csl.char_entry_value_strip(char_val)
                    )
                    if re_status:
                        file_mashup_name += (
                            f"{'&' if file_mashup_name else ''}"
                            f"({'_'.join([str(file_name), 'C'])})"
                        )
                        master_list.append(Image.open(file_path))
                    else:
                        char_count += 1
                        logging.warning("File not found. Returning an entry to loop.")
                else:
                    char_content = script_globals.char_dir_nude / str(char_val)
                    master_list.append(Image.open(next(char_content.glob("*.png"))))
                    file_mashup_name += (
                        f"{'&' if file_mashup_name else ''}"
                        f"({'_'.join([str(char_val), 'N'])})"
                    )
                break
            else:
                logging.warning("Invalid input. Please enter Y or N.")
    return master_list, file_mashup_name


def request_images_automatic(spt_args):
    n_integers = []
    c_integers = []
    n_filename = ""
    c_filename = ""
    # merge_flag = False
    current_flag = None

    for item in spt_args:
        # if item == "-m":
        #     merge_flag = True
        if item == "-n":
            current_flag = "n"
        elif item == "-c":
            current_flag = "c"
        elif item == "-an":
            dir_list = sorted(script_globals.char_dir_nude.glob("*"))
            n_integers = [i.glob("*") for i in dir_list]
            break
        elif item == "-ac":
            dir_list = sorted(script_globals.char_dir_clothed.glob("*"))
            c_integers = [i.glob("*") for i in dir_list]
            break
        else:
            if current_flag == "n":
                # Learnt this is safer. Users may not put space between ints, this will prevent that from causing
                # issues recognizing proper character entries.
                n_integers.extend(map(int, item.split(",")))
                n_filename += (
                    f"{'&' if n_filename else ''}"
                    f"({'_'.join([str(item), current_flag])})"
                )
            elif current_flag == "c":
                c_integers.extend(map(int, item.split(",")))
                c_filename += (
                    f"{'&' if c_filename else ''}"
                    f"({'_'.join([str(item), current_flag])})"
                )
    n_result = request_images_automatic_extract(n_integers, True)
    c_result = request_images_automatic_extract(c_integers, False)
    if n_result:
        merge_images(n_result, n_filename, 0)
    if c_result:
        merge_images(c_result, c_filename, 1)


def request_images_automatic_extract(img_list, nude):
    result = []
    if nude:
        char_path = script_globals.char_dir_nude
    else:
        char_path = script_globals.char_dir_clothed
    for i in img_list:
        clothed_dir = char_path / csl.listdir_int_match(char_path, i)
        clothed_check = sorted(clothed_dir.glob("*"))
        file_name, file_path, re_status = image_validation(clothed_check, i)
        if re_status:
            result.append(Image.open(clothed_dir / file_path))
        else:
            logging.warning("Error. File not found. Aborting.")
            sys.exit()

    return result


def request_images_singular_char():
    loop_breaker = True
    main_char = ""
    while loop_breaker:
        print("Who do you wanna compare the others against?")
        main_char_int = csl.validate_int_input()
        loop_breaker, main_char = file_finder(main_char_int)
        # image_validation()
    return main_char, "test", 0


# Step 4
def merge_images(images, filename, nude=0):
    """
    Final Step. Combines individual image segments together.
    :param images: Image list.
    :param filename: Name of file. Expects '(000_C/N)&...', but if longer than 255, replace with alphanumeric string
    of X len.
    :param nude: Boolean. Checks if nude string required to append.
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
    output_dir = script_globals.output_dir

    while True:
        try:
            file_quality = int(input("Lossless(0) or Lossy(1)? :"))
            if file_quality not in [0, 1]:
                raise ValueError("Invalid integer inputted. Please use 0 or 1.")
            break
        except ValueError:
            logging.warning("Invalid input. Please enter an integer.")

    filename_path = Path(output_dir) / f"{filename}"
    if len(str(filename_path)) > 254:
        logging.info(
            f"File name {filename_path} is too long. Replacing with a randomly generated string of numbers."
        )
        filename_path = Path(output_dir) / str(int(time.time()))
        if nude == 0:
            filename_path = Path(str(filename_path) + "_nude")
        elif nude == 1:
            filename_path = Path(str(filename_path) + "_clothed")
        else:
            filename_path = Path(str(filename_path) + "_merged")

    ##Used for webp support
    maxsize = (16000, 16000)
    merged_image.thumbnail(maxsize, Image.Resampling.LANCZOS)

    merged_image_cv = np.array(merged_image)
    merged_image_cv = cv2.cvtColor(merged_image_cv, cv2.COLOR_RGB2BGR)


    if file_quality == 0:
        # logging.info(f"Hit Lossless @ {time.time()}")
        #
        # filename_path_lossless_pil = Path(str(filename_path) + "_pil").with_suffix(".webp")
        # timeS = time.time()
        # merged_image.save(filename_path_lossless_pil, lossless=True, quality=100, method=6)
        # timeE = time.time()
        # logging.info(f"Total time for pillow: {str(timeE - timeS)}")

        # filename_path_lossless_ocv = Path(str(filename_path) + "_ocv101").with_suffix(".webp")
        filename_path_lossless_ocv = filename_path.with_suffix(".webp")
        # timeS = time.time()
        cv2.imwrite(filename_path_lossless_ocv, merged_image_cv, [cv2.IMWRITE_WEBP_QUALITY, 101])
        # timeE = time.time()
        # logging.info(f"Total time for OpenCV: {str(timeE - timeS)}")

        print(f"File name {filename_path_lossless_ocv} saved!.")

    elif file_quality == 1:
        # logging.info(f"Hit Lossy @ {time.time()}")

        # filename_path_lossy_pil = Path(str(filename_path) + "_pil").with_suffix(".webp")
        # timeS = time.time()
        # merged_image.save(filename_path_lossy_pil, quality=100, method=6)
        # timeE = time.time()
        # logging.info(f"Total time for pillow: {str(timeE - timeS)}")

        # filename_path_lossy_ocv = Path(str(filename_path) + "_ocv95").with_suffix(".webp")
        filename_path_lossy_ocv = filename_path.with_suffix(".webp")
        # timeS = time.time()
        cv2.imwrite(filename_path_lossy_ocv, merged_image_cv, [cv2.IMWRITE_WEBP_QUALITY, 100]) # 100 is still lossy. 101 is lossless.
        # timeE = time.time()
        # logging.info(f"Total time for OpenCV95: {str(timeE - timeS)}")

    # else:
        # starttime = time.time()
        # maxsize = (16000, 16000)
        # merged_image.thumbnail(maxsize, Image.Resampling.LANCZOS)
        #
        # filename_path_lossless = filename_path.with_suffix(".webp")
        # merged_image.save(filename_path_lossless, lossless=True, quality=100, method=6)
        # print(f"File name {filename_path_lossless} saved!.")
        #
        # filename_path_lossy = filename_path.with_suffix(".webp")
        # merged_image.save(filename_path_lossy, quality=100, method=6)
        # print(f"File name {filename_path_lossy} saved!.")

        # endtime = time.time() - starttime
        # logging.info(endtime)


    print(f"File name {filename_path} saved!.")
    return filename_path


def merge_images_clothed():
    """
    Merge variant. Chars each have their own row.
    :return: None
    """
    char_dir_clothed = script_globals.char_dir_clothed
    output_dir = script_globals.output_dir

    base_height = len(list(char_dir_clothed.glob("*"))) * 1600
    base_width = 0
    for char_folder in char_dir_clothed.iterdir():
        max_width_base = len(list(char_folder.glob("*")))
        base_width = max(base_width, max_width_base)-1 # -1 cause of the padding empty-name file
    base_width *= 1200

    merged_image = Image.new("RGB", (base_width, base_height))
    x = 0  # height
    y = 0  # width
    for char_folder in char_dir_clothed.iterdir():
        for image_file in char_folder.iterdir():
            if image_file.suffix == ".png":
                merging_hold = Image.open(image_file)
                merged_image.paste(merging_hold, (y, x))
                y += 1200
        x += 1600
        y = 0
    filename = output_dir / f"{time.time()}_clothed.png"
    merged_image.save(filename)
    print(f"File name {filename} saved!.")
    sys.exit()


# Main
def main():
    try:
        args_valid = False
        args_valid_flags = ["-n", "-c", "-m", "-an", "-ac"]
        # Initial folder prerequisite checks
        folder_setup()

        # Reads and processes images. If new originals are found, or new clothing, process and break them down.
        preprocess_files()

        # Request user settings
        if len(sys.argv) > 1:
            sys_args = sys.argv
            first_arg = sys_args[0]
            if os.path.normpath(first_arg) != __file__:
                sys_args.pop(0)
                first_arg = sys_args[0]
                if first_arg in args_valid_flags:
                    if len(sys_args) >= 2 or first_arg == "-an" or first_arg == "-ac":
                        request_images_automatic(sys_args)
                        args_valid = True
                    else:
                        logging.warning("Arguments malformed. Not enough parameters.")
                        sys.exit()
                elif not sys.argv:
                    logging.warning(
                        "Arguments malformed. Start with -n or -c for nude/clothed."
                    )
                    sys.exit()

        if not args_valid:
            # menu_selection = begin_interface_opt()
            menu_selection = 1
            if menu_selection == 1:
                master_list, final_name = request_images()
                merge_images(master_list, final_name, 0)
            # elif menu_selection == 2:
            #     master_list, final_name, nude_status = request_images_singular_char()
            #     merge_images(master_list, final_name, nude_status)
            # elif menu_selection == 3:
            #     print("Printing nude walk result:\n\n")
            #     print(script_globals.char_dir_nude.walk())
            #     print("\n\nPrint complete. Printing nude glob result:\n\n")
            #     print(script_globals.char_dir_nude.glob("*"))
            #     print("\n\nPrint complete.")
            else:
                logging.error(
                    "Invalid menu selection was passed. This should not be possible. "
                    "Panic calmly and abort."
                )
            sys.exit()
    except KeyboardInterrupt:
        logging.warning("\nInterrupt caught. Exiting. Brace, brace, brace!")
        sys.exit()


if __name__ == "__main__":
    main()

# TODO:
#
# Pixel background strip colour?
# Proper name-file sanitation, for "home"/"away" cramball-esque stuff. i.e. multi sheet chars.
