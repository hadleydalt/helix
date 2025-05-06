# How to run! 

1. Open 3 terminals. 
2. In each one, cd into sellscale_agentic_hr. 
3. In two of them, make sure the virtual environment is activated by running "source venv/bin/activate" on Mac/Linux or "venv\Scripts\activate" on Windows
4. If the requirements are not installed you can run "pip install -r requirements.txt" in one terminal. 
5. In one terminal, run "python setup_db.py"
6. In another terminal, run "python app.py"
NOTe: Every terminal you run a Python script in should have the virtual environment activated. 
7. In your last terminal, run "npm start". If something is wrong, you may need to run "npm install" first. 
8. You should now be able to navigate to the localhost provided in the terminal (probably http://localhost:3000) and view the project!
9. Let me know if you encounter any issues. 



BUGS: 
1. There is a bug where in order to edit the sequence, you have to explicitly tell it to edit the sequence (for example, "Please edit the sequence to add a final step to let them know i'm always available around the clock for questions" rather than "Add a final step"). 

How I would solve if I had more time: I would configure the "brain"/seed message so that the instructions are more clear and the LLM is able to recognize when to edit the sequence without the explicit word "edit". 

2. After generating, editing or deleting a step from a sequence, the confirmation message appears at the bottom of the sequence rather than in the chatbox. This was very frustrating. 

If given more time, I would experiment more with the exact configurations that are causng this bug. (i.e., how the message is being sent to the frontend, when it is being generated in relation to the sequence, etc)

3. Sequences are stored locally rather than in the database. 

If given more time, I would have set up the database configurations more effectively so that the database would be able to store and retrieve the sequences rather than them being stored in a local variable user_sessions. In some commented-out code, I showed the functions I wrote to attempt to approach this problem but they unfortunately did not work properly so if given more time, I would debug further. 