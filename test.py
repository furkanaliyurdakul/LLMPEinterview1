import os
import glob

def extract_python_files_to_txt(directory='.', output_filename='combined_code.txt'):
    """
    Extracts all .py files from the given directory and writes them to a single text file.
    Each file's content is preceded by a header that indicates the file name.
    
    :param directory: The directory to search for Python files. Defaults to current directory.
    :param output_filename: The name of the output text file.
    """
    # Get a list of all Python files in the directory
    python_files = glob.glob(os.path.join(directory, '*.py'))
    
    # Open the output file in write mode
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for file_path in python_files:
            file_name = os.path.basename(file_path)
            header = f"\n==== {file_name} ====\n\n"
            outfile.write(header)
            with open(file_path, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
            # Optionally, add some separation after each file
            outfile.write("\n" + "=" * 40 + "\n")

if __name__ == "__main__":
    # You can change the directory and output file name as needed.
    extract_python_files_to_txt(directory='.', output_filename='combined_code.txt')
