from PIL import Image
import os


def find_matching_files(files, file_exist):
    for filename in files:
        if file_exist == int(filename[:3]):
            print(f"File containing the integer {file_exist} found: {filename}")
            return filename
    print(f"No file containing the integer {file_exist} found in the folder.")
    return ""


def process_image(file_list):
    result_images = []
    for file_path, not_naked in file_list:
        im = Image.open(file_path)
        crop_area = (0, 0, 1200, 1600)
        if not_naked:
            crop_area = (1200, 0, 2400, 1600)
        im1 = im.crop(crop_area)
        result_images.append(im1)
    return result_images


def merge_images(images, filename):
    merged_width = 1200 * len(images)
    merged_image = Image.new("RGB", (merged_width, 1600))
    width = 0
    for image in images:
        merged_image.paste(image, (width, 0))
        width += 1200
    merged_image.save(f"{filename}.png", "PNG")


def file_finder(files):
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
    master_list = []
    file_mashup_name = ""

    while True:
        try:
            char_count = int(
                input("How many characters do you want to merge? Integers only! : ")
            )
            if char_count < 0:
                raise ValueError("Negative integers are not allowed.")
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    for _ in range(char_count):
        file1 = file_finder(files)

        while True:
            correct_file = input(f'Is this the right file? "{file1}"  Y/N: ').lower()[
                           :1
                           ]
            if correct_file in ["y", "n"]:
                if correct_file == "y":
                    break
                else:
                    files.remove(file1)
                    file1 = file_finder(files)
            else:
                print("Invalid input. Please enter Y or N.")

        while True:
            clothes = input("Should they wear clothes? Y/N: ").lower()[:1]
            if clothes in ["y", "n"]:
                master_list.append([os.path.join(current_dir, file1), clothes == "y"])
                file_mashup_name += f"{'&' if file_mashup_name else ''}({'_'.join([file1[:3], 'C' if clothes == 'y' else 'N'])})"
                break
            else:
                print("Invalid input. Please enter Y or N.")

    return master_list, file_mashup_name


def preprocess_files(files, current_dir):
    temp_hold = []
    for i in files:
        if i[:3] not in temp_hold:
            temp_hold.append(i[:3])
            temp_hold.sort()
        else:
            files = pre_merge_and_move(i[:3], files, current_dir)
    return files


def pre_merge_and_move(char_val, files, current_dir):
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
    merge_images(result_images, os.path.join(current_dir, file_mod_name + "merged"))

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
            print("Directory may alraedy contain the same file. Skipping.")
    return hold_modified_file_list


def main():
    current_dir = os.path.join(os.path.dirname(__file__), "Characters_List")
    files = os.listdir(current_dir)
    files = [i for i in files if ".txt" not in i]
    output_dir = os.path.join(os.path.dirname(__file__), "Output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    files = preprocess_files(files, current_dir)
    master_list, result_name = request_images(current_dir, files)
    img_complete = process_image(master_list)
    merge_images(img_complete, output_dir + "\\" + result_name)


if __name__ == "__main__":
    main()

#   TODO:
#   Add automation to auto-run all in directory for specific type (nude/clothed) -split files, one proc, one input/pass?
#   Add load from merged files based on file width - Clothed or nude option needs to be expanded to support this.
#   Add auto-merge same-char files with different clothes -DONE