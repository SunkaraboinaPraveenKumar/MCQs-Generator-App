from flask import Flask, request, render_template,make_response
from PyPDF2 import PdfReader, PdfWriter
import spacy
from collections import Counter
import random

nlp = spacy.load("en_core_web_sm")

#creating app
app = Flask(__name__)


def generate_mcqs(text, num_questions=5):
    if text is None:
        return []
    doc = nlp(text)

    sentences = [sent.text for sent in doc.sents]

    selected_sentences = random.sample(sentences, min(num_questions, len(sentences)))
    mcqs = []
    # Generate MCQs for each selective sentences
    for sentence in selected_sentences:
        # process with spacy
        sent_doc = nlp(sentence)
        # Extract entities(nouns)
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        if len(nouns) < 2:
            continue
        noun_counts = Counter(nouns)

        if noun_counts:
            subject = noun_counts.most_common(1)[0][0]
            answer_choices = [subject]
            question_stem = sentence.replace(subject, "________")
            distractors = list(set(nouns) - {subject})

            while len(distractors) < 3:
                distractors.append("[Distractor]")
            random.shuffle(distractors)
            for distractor in distractors[:3]:
                answer_choices.append(distractor)

            random.shuffle(answer_choices)
            correct_answer = chr(64 + answer_choices.index(subject) + 1)
            mcqs.append((question_stem, answer_choices, correct_answer))
    return mcqs


def process_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page_num in range(len(pdf_reader.pages)):
        page_text = pdf_reader.pages[page_num].extract_text()
        text += page_text

    return text


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        text = ""
        #check if files were uploaded
        if 'files[]' in request.files:
            files = request.files.getlist("files[]")
            for file in files:
                if file.filename.endswith('.pdf'):
                    text += process_pdf(file)
                else:
                    text += file.read().decode('utf-8')

        num_questions = int(request.form['num_questions'])

        mcqs = generate_mcqs(text, num_questions=num_questions)
        mcqs_with_index = [(i + 1, mcq) for i, mcq in enumerate(mcqs)]
        return render_template("mcqs.html", mcqs=mcqs_with_index)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
