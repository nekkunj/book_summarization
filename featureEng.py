from libraries import *
from nlp_model import *
import os


# Get the absolute path of the directory where the script is located
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set the upload folder to be a subdirectory named 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')

def process_and_split(input_filename, model_instance):
    flag_check = 0
    flag = 0
    total_chapters = 0
    skip_contents = 0
    input_filename = input_filename[:-4]
    text_file = input_filename + '.txt'
    found_index = False

    with open(text_file, 'r', encoding='utf-8') as file1:
        lines = file1.readlines()
        for line in lines:
            content_keywords = ['CONTENTS', 'Contents']
            start_pages = ['Acknowledgements', 'Acknowledgement', 'ACKNOWLEDGEMENT', 'ACKNOWLEDGEMENTS', 'INDEX',
                           'Index', 'Notes', 'NOTES', 'Subject Index']
            ignore_keywords = ['Acknowledgements', 'Acknowledgement', 'ACKNOWLEDGEMENT', 'ACKNOWLEDGEMENTS', 'INDEX',
                               'Subject Index']
            tokens = line.split()
            check_contents = any(item in content_keywords for item in tokens)
            ignore_check = any(item in start_pages for item in tokens)

            if check_contents:
                print('Contents page found!\n')
                flag_check = 1
                skip_contents = 400
                continue
            elif flag_check == 1 and skip_contents > 0:
                if ignore_check:
                    skip_contents = 0
                    continue
                else:
                    skip_contents -= 1
                    continue

            ignore_check = any(item in ignore_keywords for item in tokens)
            acknowledgement_pattern = re.compile(r'Acknowledg(?:ment|ments)')
            acknowledgement_pattern_another = re.compile(r'ACKNOWLEDG(?:MENT|MENTS)')

            found_acknowledgement = re.search(acknowledgement_pattern, line)
            found_acknowledgement_another = re.search(acknowledgement_pattern_another, line)

            if (found_acknowledgement and total_chapters > 0) or (found_acknowledgement_another and total_chapters > 0):
                print('Found acknowledgement!\n')
                break

            pattern = re.compile(r'CHAPTER\s*\d')
            pattern_small = re.compile(r'Chapter\s*\d')

            found_chapter = re.search(pattern, line)
            found_chapter_small = re.search(pattern_small, line)

            if found_chapter or found_chapter_small:
                flag = 1
                total_chapters += 1
                counter = 0
                continue

            elif flag == 1:
                if counter == 0:
                    counter += 1
                    text_file = input_filename + 'Chapter' + str(total_chapters) + '.txt'
                    with open(text_file, 'w', encoding='utf-8') as file2:
                        file2.write(line)
                    file2.close()
                else:
                    text_file = input_filename + 'Chapter' + str(total_chapters) + '.txt'
                    with open(text_file, 'a', encoding='utf-8') as file2:
                        file2.write(line)
                    file2.close()
                continue

        if flag == 0:
            print('No chapters in the book! Writing the entire book!')
            with open(input_filename + 'ChapterAll.txt', 'w', encoding="utf-8") as file2:
                file2.writelines(lines)
            file2.close()
            print("Done writing!")
    file1.close()
    try:
        os.remove(os.path.join(input_filename + ".pdf"))
    except Exception as e:
        print(e)
        pass
    finally:
        summaries,average_rouge_1_r,average_rouge_2_r,average_rouge_l_r,average_rouge_1_p,average_rouge_2_p,average_rouge_l_p,average_rouge_1_f,average_rouge_2_f,average_rouge_l_f = generate_summary_and_scores(model_instance)
        return summaries,average_rouge_1_r,average_rouge_2_r,average_rouge_l_r,average_rouge_1_p,average_rouge_2_p,average_rouge_l_p,average_rouge_1_f,average_rouge_2_f,average_rouge_l_f


def parse_pdf(input_filename, model_instance):
    file_pointer = open(os.path.join(input_filename), 'rb')
    resource_manager = PDFResourceManager()
    result_string = io.StringIO()
    layout_params = LAParams()
    text_converter_device = TextConverter(resource_manager, result_string, laparams=layout_params)
    pdf_interpreter = PDFPageInterpreter(resource_manager, text_converter_device)

    for page in PDFPage.get_pages(file_pointer, check_extractable=False):
        pdf_interpreter.process_page(page)
        extracted_data = result_string.getvalue()

    print('Converting PDF to txt file.')
    text_file = input_filename[:-4] + '.txt'
    with open(text_file, 'w', encoding='utf-8') as file:
        file.write(extracted_data)
    file.close()
    print('Successfully converted PDF to txt.')
    return process_and_split(input_filename, model_instance)
