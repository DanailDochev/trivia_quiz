import openai
import gradio as gr
import re
import os

openai_api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

topics = ["Science", "History", "Sports", "Technology", "Movies"]
difficulty_levels = ["Easy", "Medium", "Hard"]


def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def generate_question(topic, difficulty):
    prompt = (
        f"Generate a {difficulty.lower()} difficulty trivia question "
        f"about {topic.lower()} with its correct answer in this format:\n"
        f"Question: <question>\nAnswer: <answer>"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a trivia master."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=120
    )
    output = response.choices[0].message.content.strip()
    if "Question:" in output and "Answer:" in output:
        question = output.split("Question:")[1].split("Answer:")[0].strip()
        answer = output.split("Answer:")[1].strip()
        return question, answer
    return "Failed to generate a question. Click Next Question again.", ""


def generate_image(question, answer):
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"A realistic image from the event described in this trivia question: '{question}'. The correct answer is {answer}.",
        size="1024x1024",
    )
    return image_response.data[0].url


current_question = {"question": "", "answer": ""}


def get_question(topic, difficulty):
    global current_question
    question, answer = generate_question(topic, difficulty)
    current_question = {"question": question, "answer": answer}
    return question, "", "", None


def check_answer(user_answer):
    correct_answer_raw = current_question["answer"]
    correct_answer = clean_text(correct_answer_raw)
    user_answer_normalized = clean_text(user_answer)
    correct = (
        user_answer_normalized in correct_answer
        or correct_answer in user_answer_normalized
    )
    image_url = generate_image(current_question["question"], correct_answer_raw)
    return (
        f"Your Answer: {user_answer}\n"
        f"Correct Answer: {current_question['answer']}\n"
        f"Result: {'✅ Correct!' if correct else '❌ Wrong!'}",
        image_url
    )


with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown("<h1 style='text-align: center; color: #333;'>🔥 AI Trivia Quiz 🔥</h1>")
    topic_dropdown = gr.Dropdown(choices=topics, label="Select Topic", value="Science")
    difficulty_dropdown = gr.Dropdown(choices=difficulty_levels, label="Select Difficulty", value="Medium")
    question_box = gr.Textbox(label="Question", interactive=False)
    answer_input = gr.Textbox(label="Your Answer", placeholder="Type your answer here...")
    submit_button = gr.Button("Submit Answer", variant="primary")
    result_box = gr.Textbox(label="Result", interactive=False)
    image_display = gr.Image(label="Related Image")
    next_question_button = gr.Button("🎲 Next Question", variant="secondary")

    submit_button.click(fn=check_answer, inputs=answer_input, outputs=[result_box, image_display])
    next_question_button.click(fn=get_question, inputs=[topic_dropdown, difficulty_dropdown],
                               outputs=[question_box, answer_input, result_box, image_display])
    topic_dropdown.change(fn=get_question, inputs=[topic_dropdown, difficulty_dropdown],
                          outputs=[question_box, answer_input, result_box, image_display])
    difficulty_dropdown.change(fn=get_question, inputs=[topic_dropdown, difficulty_dropdown],
                               outputs=[question_box, answer_input, result_box, image_display])

iface.launch()
