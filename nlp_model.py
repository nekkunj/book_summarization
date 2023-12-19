from libraries import *
import os

base_dir = os.path.abspath(os.path.dirname(__file__))


app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')

device = torch.device('cpu')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def cleanText(noisyText):
    cl_text = re.sub(r"@[A-Za-z0-9]+", ' ', noisyText)
    cl_text = re.sub(r"https?://[A-Za-z0-9./]+", ' ', cl_text)
    cl_text = re.sub(r"[^a-zA-z.!?'0-9]", ' ', cl_text)
    cl_text = re.sub('\t', ' ', cl_text)
    cl_text = re.sub(r" +", ' ', cl_text)
    return cl_text


def getSummary(inputtext, model,tokenizer):
    preprocess_text = inputtext.strip().replace("\n", "")
    t5_prepared_Text = "summarize: " + preprocess_text
    tokenized_text = tokenizer.encode(t5_prepared_Text, return_tensors="pt").to(device)

    mode_out = model.generate(tokenized_text,
                                 num_beams=5,
                                 no_repeat_ngram_size=3,
                                 min_length=40,
                                 max_length=146,
                                 early_stopping=True)

    output = tokenizer.decode(mode_out[0], skip_special_tokens=True)
    return output

def calculate_rouge(reference, summary):
    rouge = Rouge()
    scores = rouge.get_scores(summary, reference)
    return scores

def sentenceCorrection(text):
    corrected_text = ""
    spell = SpellChecker()
    sentences = sent_tokenize(text)
    for sentence in sentences:
        words = word_tokenize(sentence)
        corrected_words = [spell.correction(word) if spell.correction(word) is not None else word for word in words]
        corrected_sentence = ' '.join(corrected_words)
        corrected_text += corrected_sentence + ' '

    return corrected_text.strip()


def generate_summary_and_scores(transformer_model):
    try:
        all_rouge_scores=[]
        summaries = []
        model=T5ForConditionalGeneration.from_pretrained(transformer_model)
        tokenizer = T5Tokenizer.from_pretrained(transformer_model)
        txtFiles = []
        for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
            if fnmatch.fnmatch(filename, '*Chapter*.txt'):
                print(filename)
                txtFiles.append(filename)
        
        for fname in txtFiles:
            summary = ""
            print("Summarising: ", fname)
            text = ""
            with open(os.path.join(app.config['UPLOAD_FOLDER'] + '/' + fname), 'r', encoding="utf-8") as f:
                textLines = f.readlines()
                for line in textLines:
                    line = cleanText(line)
                    line = line.replace("\n", " ")
                    text += line

                textTokens = word_tokenize(text)
                totalTokens = len(textTokens)
                chunkCounter = 0
                maxTokenLen = 400
                incomingText = []
                st = 0
                lt = maxTokenLen

                if (totalTokens % maxTokenLen) == 0:
                    totalChunks = int(totalTokens / maxTokenLen)

                    for i in range(0, totalChunks):
                        tempTokens = textTokens[st:lt]
                        in_ch_text = ' '.join([str(elem) for elem in tempTokens])
                        incomingText.append(in_ch_text)
                        st = lt
                        lt += maxTokenLen
                        in_ch_text = ""

                else:
                    totalChunks = int(totalTokens / maxTokenLen) + 1

                    for i in range(0, (totalChunks - 1)):
                        tempTokens = textTokens[st:lt]
                        in_ch_text = ' '.join([str(elem) for elem in tempTokens])
                        incomingText.append(in_ch_text)
                        st = lt
                        lt += maxTokenLen
                        in_ch_text = ""

                    tempTokens = textTokens[st:totalTokens]
                    in_ch_text = ' '.join([str(elem) for elem in tempTokens])
                    incomingText.append(in_ch_text)
                    input_text=""
                for chunk in incomingText:
                    input_text=input_text+chunk
                    tempSummary = getSummary(chunk, model,tokenizer)
                    summary += tempSummary
                    # summary += chunk
                
                summary = sentenceCorrection(summary)
                rouge_scores = calculate_rouge(input_text, summary)
                print(rouge_scores)
                all_rouge_scores=all_rouge_scores + rouge_scores
                summaries.append(summary)
                print("Summarisation complete!")
                fileName = fname[:-4] + "_summary.txt"
                with open(os.path.join(app.config['UPLOAD_FOLDER'] + '/' + fileName), 'w', encoding="utf-8") as f1:
                    f1.write(summary)
                print("Summary written to file!")
                f1.close()
            f.close()
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'] + '/' + fname))
        print(all_rouge_scores)
        rouge_1_r = [file_scores['rouge-1']['r'] for file_scores in all_rouge_scores]
        rouge_2_r = [file_scores['rouge-2']['r'] for file_scores in all_rouge_scores]
        rouge_l_r = [file_scores['rouge-l']['r'] for file_scores in all_rouge_scores]

        rouge_1_p = [file_scores['rouge-1']['p'] for file_scores in all_rouge_scores]
        rouge_2_p = [file_scores['rouge-2']['p'] for file_scores in all_rouge_scores]
        rouge_l_p = [file_scores['rouge-l']['p'] for file_scores in all_rouge_scores]

        rouge_1_f = [file_scores['rouge-1']['f'] for file_scores in all_rouge_scores]
        rouge_2_f = [file_scores['rouge-2']['f'] for file_scores in all_rouge_scores]
        rouge_l_f = [file_scores['rouge-l']['f'] for file_scores in all_rouge_scores]

        # Calculate the average scores
        average_rouge_1_r = np.mean(rouge_1_r)
        average_rouge_2_r = np.mean(rouge_2_r)
        average_rouge_l_r = np.mean(rouge_l_r)

        average_rouge_1_p = np.mean(rouge_1_p)
        average_rouge_2_p = np.mean(rouge_2_p)
        average_rouge_l_p = np.mean(rouge_l_p)

        average_rouge_1_f = np.mean(rouge_1_f)
        average_rouge_2_f = np.mean(rouge_2_f)
        average_rouge_l_f = np.mean(rouge_l_f)

        makezipAndCleanUp(fname[:-4])
        return summaries,average_rouge_1_r,average_rouge_2_r,average_rouge_l_r,average_rouge_1_p,average_rouge_2_p,average_rouge_l_p,average_rouge_1_f,average_rouge_2_f,average_rouge_l_f
    except Exception as e:
        print(e)


def makezipAndCleanUp(fileName):    
    # function to compress all summary text files into single zip file
    # call mail function and send zip file
    shutil.make_archive(fileName+'summarized_chapters', 'zip', app.config['UPLOAD_FOLDER'])
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'] + '/' + file))