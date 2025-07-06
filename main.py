from logger import logger
from formatters import format_link

def main():
    # Create an output file
    with open("output.txt", "w") as file:
        file.write("\n")
        logger.info("Output file created and written successfully.")
    
    with open('input.txt', 'r') as file:
        lines = file.readlines()
        logger.info(f"Read {len(lines)} lines from input file.")

    ret = []    
    for line in lines:
        # line format: '[object_type] link'
        object_type, link = line.strip().split('] ')
        object_type = object_type[1:]  # Remove the leading '['
        link = link.strip()  # Remove any leading/trailing whitespace
        logger.debug(f"Processing object type: {object_type}, link: {link}")
        formatted_link = format_link(object_type, link)
        logger.info(f"Formatted link: {formatted_link}")
        ret.append(formatted_link)
    
    with open("output.txt", "w") as file:
        for item in ret:
            file.write(f"{item}\n")
    logger.success(f"Written formatted links to output file: {len(ret)} items.")

if __name__ == "__main__":
    logger.info("Starting the application...")
    main()
    logger.info("Application finished.")