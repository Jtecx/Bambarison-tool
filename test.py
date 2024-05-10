import sys


def script_test(clothed_dir, clothed_check):
    i = 69
    file_confirm = ""
    if len(clothed_check) > 1:
        file_found = False
        for file1 in clothed_check:
            correct_file = input(
                f'Is this the right file? "{file1.name}"  Y/N: '
            ).lower()[:1]
            verify = True
            while verify:
                if correct_file in ["y", "n"]:
                    if correct_file == "y":
                        file_confirm = file1.name
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
                f"Last one of Character entry no.{i} found. Since none was chosen, exiting."
            )
            sys.exit()
    elif not clothed_check:
        print(f"Character entry no.{i} found. Exiting.")
        sys.exit()
    else:
        file_confirm = clothed_check[0].name

    return file_confirm


def main():
    script_test("test", "test")


if __name__ == "__main__":
    main()
