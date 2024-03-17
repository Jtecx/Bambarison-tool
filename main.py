from PIL import Image
import os
from queue import Queue
import threading
import random
import string
import math
import logging


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
        print("All complete! Moving on.")
        return results
    except Exception as f:
        logging.error(f"An error occurred: {f}")


def find_matching_files(files, file_exist):
    """
    Checks if file exists.
    :param files: List of image names. String.
    :param file_exist: Character entry number, top left of character sheet. Integer.
    :return: File name that matches. If none, returns empty string.
    """
    for filename in files:
        if file_exist == int(filename[:3]):
            print(f"File containing the integer {file_exist} found: {filename}")
            return filename
    print(f"No file containing the integer {file_exist} found in the folder.")
    return ""


def process_image(q, results):
    """
    Cutting images based on parameters.
    :param q: Queue. Used for keeping results in order.
    :param results: Where to store the results to return
    :return: Completed queue.
    """
    while not q.empty():
        work = q.get()
        print("New task started. " + str(work[0]) + "\n")
        im = Image.open(work[1][0])
        crop_area = (0, 0, 1200, 1600)
        if work[1][1]:
            crop_area = (1200, 0, 2400, 1600)
        results[work[0]] = im.crop(crop_area)
        q.task_done()
        print("New task done. " + str(work[0]) + "\n")
    return True


def merge_images(images, filename, output_path):
    """
    Final Step. Combines individual image segments together.
    :param images: Image list.
    :param filename: Name of file. Expects '(000_C/N)&...', but if longer than254, replace with alnum string of X len.
    :param output_path: Directory path of output file location.
    :return: None
    """
    base_width = 1200  # Don't modify
    base_height = 1600  # Don't modify
    rowmax = 10  # Final image width
    filename_length = 10  # Filename length if longer than OS limit
    merged_width = base_width * len(images)
    merged_height = base_height
    if merged_width > base_width * rowmax:
        merged_width = base_width * rowmax
        merged_height = merged_height * math.ceil(len(images) / rowmax)
    merged_image = Image.new("RGB", (merged_width, merged_height))
    width = 0
    height = 0
    for image in images:
        merged_image.paste(image, (width, height))
        width += base_width
        if width >= base_width * rowmax:
            width = 0
            height += base_height
    filename = output_path + "\\" + filename
    if len(filename) > 254:
        print(
            f"File name {filename}.png is too long. Replacing with a randomly generated string of numbers."
        )
        filename = (
            output_path
            + "\\"
            + "".join(
                random.choices(string.ascii_letters + string.digits, k=filename_length)
            )
        )
    merged_image.save(f"{filename}.png", "PNG")
    print(f"File name {filename}.png saved!.")


def file_finder(files):
    """
    File input handler. Loop for manual input.
    :param files: List of image names.
    :return: File name.
    """
    while True:
        try:
            file_exist = int(input("Who's next? Integers only! : "))
            if file_exist < 0:
                raise ValueError("Negative integers are not allowed.")
            file1 = find_matching_files(files, file_exist)
            if file1:
                break
        except ValueError:
            print("Invalid input. Please enter an integer.")
    return file1


def request_images(current_dir, files):
    """
    File image handler. Main interface.
    :param current_dir: Directory path for Character sheets.
    :param files: List of image names.
    :return: master_list: list of all images to process, file_mashup_name: expected file output name.
    """
    master_list = []
    file_mashup_name = ""

    while True:
        try:
            char_count = int(
                input(
                    f"How many characters do you want to merge? Integers only! You currently have {len(files)} "
                    f"characters in your list. Put the same number in to run auto-nude!: "
                )
            )
            if char_count < 0:
                raise ValueError("Negative integers are not allowed.")
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    if char_count == len(files):
        checkall = input(
            "Same number of total files detected! Did you want to do a full nude lineup? Y/N: "
        ).lower()[:1]
        if checkall in ["y", "n"]:
            if checkall == "y":
                for i in files:
                    master_list.append([os.path.join(current_dir, i), False])
                    file_mashup_name += (
                        f"{'&' if file_mashup_name else ''}({'_'.join([i[:3], 'N'])})"
                    )
    else:
        print("Understood. Manual selection time!")
        for _ in range(char_count):
            file1 = file_finder(files)

            # while True:
            #     correct_file = input(f'Is this the right file? "{file1}"  Y/N: ').lower()[
            #         :1
            #     ]
            #     if correct_file in ["y", "n"]:
            #         if correct_file == "y":
            #             break
            #         else:
            #             files.remove(file1)
            #             file1 = file_finder(files)
            #     else:
            #         print("Invalid input. Please enter Y or N.")

            while True:
                clothes = input("Should they wear clothes? Y/N: ").lower()[:1]
                if clothes in ["y", "n"]:
                    master_list.append(
                        [os.path.join(current_dir, file1), clothes == "y"]
                    )
                    file_mashup_name += (
                        f"{'&' if file_mashup_name else ''}"
                        f"({'_'.join([file1[:3], 'C' if clothes == 'y' else 'N'])})"
                    )
                    break
                else:
                    print("Invalid input. Please enter Y or N.")

    return master_list, file_mashup_name


def preprocess_files(files, current_dir):
    """
    Checks for duplicate char sheet ints. Example: 009.
    :param files: List of image names.
    :param current_dir: Directory of Character sheets.
    :return: cleaned list of image names.
    """
    temp_hold = []
    for i in files:
        if i[:3] not in temp_hold:  # Could break, if Moxy gets to 999+ chars.
            temp_hold.append(i[:3])
            temp_hold.sort()
        else:
            files = pre_merge_and_move(i[:3], files, current_dir)
    return files


def pre_merge_and_move(char_val, files, current_dir):
    """
    Merges charsheets if multiple costumes are found, and moves the original file to other folder for backup.
    :param char_val: Character value, top left.
    :param files: file list to clean
    :param current_dir: Directory of Character sheets.
    :return: cleaned list of image names.
    """
    merge_total = [os.path.join(current_dir, i) for i in files if char_val in i]
    merge_total = sorted(merge_total, key=lambda x: "merged" in x, reverse=True)
    result_images = []

    for i in merge_total:
        im = Image.open(i)
        y0 = 0
        y1 = 1200
        if not result_images:
            y01 = y0
            y11 = y1
            if "merged" in i:  # merged images that need new clothes added on
                for _ in range(int(im.width / 1200)):
                    result_images.append(im.crop((y01, 0, y11, 1600)))
                    y01 = y11
                    y11 += 1200
            else:  # new set of images to merge together
                result_images.append(im.crop((0, 0, 1200, 1600)))
                result_images.append(im.crop((1200, 0, 2400, 1600)))
        else:  # looping through, cutting out the second image.
            # THIS WILL BREAK IF STANDALONE CLOTHES SPRITES ARE RELEASED.
            result_images.append(im.crop((1200, 0, 2400, 1600)))

    file_mod_name = [f for f in files if char_val in f][0][:-4]
    merge_images(result_images, file_mod_name + "merged", current_dir)

    hold_modified_file_list = [i for i in files if char_val not in i]
    hold_modified_file_list.append(file_mod_name + "merged.png")
    hold_move1 = [os.path.join(current_dir, i) for i in files if char_val in i]
    hold_move2 = [
        s.replace("Characters_List", "Characters_List_Unmerged") for s in hold_move1
    ]
    temp1 = os.path.split(hold_move2[1])[0]
    if not os.path.exists(temp1):
        os.makedirs(temp1)
    for i in range(len(hold_move1)):
        try:
            os.rename(hold_move1[i], hold_move2[i])
        except OSError:
            print("Directory may already contain the same file. Skipping.")
    return hold_modified_file_list


def main():
    # time1 = time.time()
    current_dir = os.path.join(os.path.dirname(__file__), "Characters_List")
    files = os.listdir(current_dir)
    files = [i for i in files if ".txt" not in i]
    output_dir = os.path.join(os.path.dirname(__file__), "Output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    files = preprocess_files(files, current_dir)
    # time1 = time.time() - time1
    master_list, result_name = request_images(current_dir, files)
    # time2 = time.time()
    img_complete = process_image_queue(master_list)
    merge_images(img_complete, result_name, output_dir)
    # time2 = time.time() - time2
    # totaltime = round(time1 + time2, 3)
    # print(f"Total time used: {totaltime}")
    print("Process complete!")


if __name__ == "__main__":
    main()

#   TODO:
#   Add automation to auto-run all in directory for specific type (nude/clothed) -split files, one proc, one input/pass?
#   -Done, only handles nude.
#   Add load from merged files based on file width - Clothed or nude option needs to be expanded to support this.
#   Add auto-merge same-char files with different clothes -DONE
#   Image matrices for image building using numpy?
