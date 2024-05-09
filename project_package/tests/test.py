import os.path

TEST_OFFICE_FILES_DIRECTORY_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0],'files')

class FILES:

    EXAMPLE        = 'example.docx'
    EXAMPLE_EDITED = 'example-edited.docx'

def file_path(file_name:str):

    return os.path.join(TEST_OFFICE_FILES_DIRECTORY_PATH, file_name)