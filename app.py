from openai import OpenAI
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()

# Get OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
CORS(app)

# Store user sessions (can be persistent in a production app)
user_sessions = {}
user_id = ""

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True, nullable=False)

class Sequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('user.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def generate_sequence(role: str = "", background: str = "", tone: str = ""):
    prompt = f"""Write a professional candidate outreach sequence for the following:
    - Role: {role}
    - Background: {background}
    - Tone: {tone}

    Assume you're drafting a full outreach unless told otherwise. That means there should be an initial message and three follow-ups. Each message MUST be separated by '---'. Follow-up messages should feel natural, persistent but respectful, and consistent with the overall strategy. Your output is ready-to-send messaging that recruiters can quickly review and edit. Your job is to generate personalized and effective candidate outreach sequences, including initial contact and follow-up messages. These sequences are used across channels like email, LinkedIn, or text, and aim to engage high-quality candidates in a clear, human, and compelling way."""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    sequence = response.choices[0].message.content
    return {"sequence": sequence, "response": "Generated sequence for a " + role + " role for candidate(s) with the following background: " + background + ", using a " + tone + " tone."}

def edit_sequence(sequence: str = "", instruction: str = "", user_id: str = ""):
    # Use the last generated sequence
    if sequence == "[LAST]":
        sequence = user_sessions[user_id]["last_sequence"]
        #DB OPTION:
        #last_sequence = Sequence.query.filter_by(user_id=user_id).order_by(Sequence.created_at.desc()).first()
        if not sequence:
            return {"sequence": "", "response": "No previous sequence found to edit."}

    prompt = f"""Edit the following outreach sequence according to this instruction: {instruction}

    Current sequence:
    {sequence}

    Please maintain the same format and structure, but make the requested changes. Each message should be separated by '---'."""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    edited_sequence = response.choices[0].message.content
    return {"sequence": edited_sequence, "response": f"Sequence has been edited according to your instruction: {instruction}"}

def delete_step(sequence: str = "", instruction: str = "", user_id: str = ""):
    # Use the last generated sequence
    #DB OPTION:
    #last_sequence = Sequence.query.filter_by(user_id=user_id).order_by(Sequence.created_at.desc()).first()
    if sequence == "[LAST]":
        sequence = user_sessions[user_id]["last_sequence"]
        if not sequence:
            return {"sequence": "", "response": "No previous sequence found to edit."}

    prompt = f"""Please delete ONLY the specified step from the sequence: {instruction}

    For example:
    - If asked to delete "the first step", keep all steps after the first '---'
    - If asked to delete "the second step", keep the first step and all steps after the second '---'
    - If asked to delete "the third step", keep the first two steps and all steps after the third '---'
    - If asked to delete "the last step", keep all steps except the final one

    Current sequence:
    {sequence}

    Please return the sequence with ONLY the specified step removed, keeping all other steps intact."""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    revised_sequence = response.choices[0].message.content
    return {"sequence": revised_sequence, "response": f"A step has been deleted from the sequence according to your instruction: {instruction}"}

functions = [
    {
        "name": "generate_sequence",
        "description": "Generates a candidate outreach sequence for recruiting.",
        "parameters": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "The title of the role being hired for"
                },
                "background": {
                    "type": "string",
                    "description": "Ideal background or candidate profile"
                },
                "tone": {
                    "type": "string",
                    "description": "Preferred tone of the outreach, e.g. 'casual', 'formal', etc."
                }
            },
            "required": ["role", "background", "tone"]
        }
    },
    {
        "name": "edit_sequence",
        "description": "Edits an existing outreach sequence.",
        "parameters": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "The sequence to edit. Use '[LAST]' to edit the most recently generated sequence."
                },
                "instruction": {
                    "type": "string",
                    "description": "The instruction for how to edit the sequence, e.g. 'add a final step', 'make it more casual', etc."
                }
            },
            "required": ["sequence", "instruction"]
        }
    },
    {
        "name": "delete_step",
        "description": "Deletes a step from an existing outreach sequence.",
        "parameters": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "The sequence to delete a step from. Use '[LAST]' to delete the most recently generated sequence."
                },
                "instruction": {
                    "type": "string",
                    "description": "The instruction for how to delete the step, e.g. 'delete the first step', 'delete the second step', etc."
                }
            },
            "required": ["sequence", "instruction"]
        }
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data['user_id']
    user_message = data['message']

    # If no session exists for this user, create it with a seed message
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "messages": [
                {"role": "system", "content": f"""You are Helix, a highly efficient and articulate recruiter working at Sellscale, a fast-growing organization. Your job is to generate personalized and effective candidate outreach sequences, including initial contact and follow-up messages. These sequences are used across channels like email, LinkedIn, or text, and aim to engage high-quality candidates in a clear, human, and compelling way.

IMPORTANT: You MUST ALWAYS ask clarifying questions before generating a sequence. Never proceed with sequence generation without having ALL of the following information:
1. Role: What position are we hiring for?
2. Background: What is the ideal candidate background or profile?
3. Tone: What tone should the outreach use (e.g., casual, formal, friendly, professional)?

If the user says anything vague like "generate a sequence" or "create a sequence", you MUST respond with:
"I'll help you create a sequence. To get started, I need some information:
1. What role are you hiring for?
2. What background are you looking for in candidates?
3. What tone would you like to use in the outreach?"

Only after receiving ALL three pieces of information should you call the `generate_sequence` function. If any information is missing, ask for it specifically.

When you have all required information, call the `generate_sequence` function with the appropriate parameters. If the user wants to edit an existing sequence, use words like 'edit', 'revise', 'update', 'add', 'simplify', etc., call the `edit_sequence` function with 'sequence': '[LAST]' and the specific changes requested. If the user wants to delete a step, call the `delete_step` function with the appropriate parameters."""}
            ],
            "last_sequence": None
        }

    # Add user's message to session history
    user_sessions[user_id]["messages"].append({"role": "user", "content": user_message})

    def generate():
        # Disable streaming to handle function calls properly
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=user_sessions[user_id]["messages"],
            functions=functions,
            function_call="auto"
        )

        message = response.choices[0].message

        if message.function_call:
            func_name = message.function_call.name
            arguments = json.loads(message.function_call.arguments)

            if func_name == "generate_sequence":
                print("Generating sequence...")
                # Send a special message to indicate sequence generation
                yield f"data: [GENERATING_SEQUENCE]\n\n"
                result = generate_sequence(**arguments)
                # Send the sequence data
                yield f"data: [SEQUENCE_DATA]{result['sequence']}\n\n"
                # Send the response message (NOTE: There is a bug which is that the response message is somehow sent with the sequence)
                assistant_reply = result["response"]
                # Store the sequence (NON-DB WAY)
                user_sessions[user_id]["last_sequence"] = result['sequence']

                # Store the sequence (DB WAY)
                '''new_sequence = Sequence(user_id=user_id, content=result['sequence'])
                db.session.add(new_sequence)
                db.session.commit()'''
            elif func_name == "edit_sequence":
                print("Editing sequence...")
                yield f"data: [EDITING_SEQUENCE]\n\n"
                # Add user_id to the arguments
                arguments["user_id"] = user_id
                result = edit_sequence(**arguments)
                yield f"data: [SEQUENCE_DATA]{result['sequence']}\n\n"
                assistant_reply = result['response']
                # Store the sequence (NON-DB WAY)
                user_sessions[user_id]["last_sequence"] = result['sequence']

                # Store the sequence (DB WAY)
                '''new_sequence = Sequence(user_id=user_id, content=result['sequence'])
                db.session.add(new_sequence)
                db.session.commit()'''
            elif func_name == "delete_step":
                print("Deleting step...")
                yield f"data: [DELETING_STEP]\n\n"
                # Add user_id to the arguments
                arguments["user_id"] = user_id
                result = delete_step(**arguments)
                yield f"data: [SEQUENCE_DATA]{result['sequence']}\n\n"
                assistant_reply = result['response']
                # Store the sequence (NON-DB WAY)
                user_sessions[user_id]["last_sequence"] = result['sequence']

                # Store the sequence (DB WAY)
                '''new_sequence = Sequence(user_id=user_id, content=result['sequence'])
                db.session.add(new_sequence)
                db.session.commit()'''
            else:
                assistant_reply = f"(Unknown function `{func_name}` was called.)"
        else:
            assistant_reply = message.content

        # Add the response to session history
        user_sessions[user_id]["messages"].append({"role": "assistant", "content": assistant_reply})

        yield f"data: {assistant_reply}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/reset', methods=['POST'])
def reset_chat():
    data = request.get_json()
    user_id = data['user_id']
    if user_id in user_sessions:
        del user_sessions[user_id]  # Remove previous session
    return jsonify({"message": "Chat reset"})

if __name__ == '__main__':
    app.run(debug=True)