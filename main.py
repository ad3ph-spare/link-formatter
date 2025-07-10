from glob import glob

from logger import logger
from formatters import format_link

def process_file(filepath):
    with open(filepath, "r") as file:
        lines = file.readlines()
        logger.info(f"Read {len(lines)} lines from input file.")

    ret = []
    for line in lines:
        # line format: '[object_type] link'
        f_line = line.strip().split("] ")
        if len(f_line) != 2:
            logger.debug("Wrong formatting on line, skipping")
            continue
        object_type, link = line.strip().split("] ")
        object_type = object_type[1:]  # Remove the leading '['
        link = link.strip()  # Remove any leading/trailing whitespace
        logger.debug(f"Processing object type: {object_type}, link: {link}")
        formatted_link = format_link(object_type, link)
        logger.info(f"Formatted link: {formatted_link}")
        ret.append(formatted_link)
    return ret


def main():
    # Create an output file
    with open("output.txt", "w") as file:
        file.write("\n")
        logger.info("Output file created and written successfully.")
    for txt in glob("./inputs/*.txt"):
        ret = process_file(txt)

        with open("output.txt", "a", encoding="utf-8") as file:
            task_name = txt[txt.find("\\") + 1 : txt.rfind(".")]
            file.write(f"\n{'-'*20}{task_name}{'-'*20}\n")
            for id, item in enumerate(ret):
                file.write(f"{id+1}.{item}\n")
        logger.success(f"Written formatted links to output file: {len(ret)} items.")


if __name__ == "__main__":
    logger.info("Starting the application...")
    # main()
    print(process_file("./input.txt"))
    logger.info("Application finished.")
