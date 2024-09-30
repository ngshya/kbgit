PROMPT_KBB_REWRITE = '''

- I have a lengthy text that I would like you to rewrite in a structured format. 
- Please ensure that all information is retained while organizing the content into clear sections or headings. 
- The rewritten text should be concise and easy to understand.
- Do not invent anything. Use only the information contained in the text.
- If there are any contradictions in the text, prioritize the information that appears later in the text.
- The output should be simple, structured, and have brief but informative sentences. 
- Please enclose the rewritten text within <OUTPUT> </OUTPUT> tags. For example, it should be formatted as follows: <OUTPUT>Rewritten text.</OUTPUT>
- Reason step by step. 

Example 1. 
**Text:**
I am hungry. 
The pen is red.
The output is: <OUTPUT>I am hungry. The pen is red.</OUTPUT>

Example 2. 
**Text:**
Intesa Sanpaolo is an Italian bank.
Turin is a beautiful city located in France.
Intesa Sanpaolo (ISP) has its headquarter in Turin.
Turin is a city located in Italy.
The output is: <OUTPUT>Intesa Sanpaolo (ISP) is an Italian bank. It has its headquarter in Turin, which is a beautiful Italian city.</OUTPUT>

Your turn to complete. 
**Text:**
%s
The output is: 

'''


PROMPT_KBB_SUB = '''

- I have two blocks of text. 
- I need you to remove any information from the first block (Block 1) that is also contained in the second block (Block 2).
- Please provide the revised version of the first block (Block 1) after removing the overlapping information.
- Do not invent anything. Use only the information contained in the text.
- The output should be simple, structured, and have brief but informative sentences. 
- Please enclose the rewritten text within <OUTPUT> </OUTPUT> tags. For example, it should be formatted as follows: <OUTPUT>Rewritten text.</OUTPUT>
- Reason step by step. 

Example 1. 
**Block 1:**
I am hungry and the pen is red.
**Block 2:**
I am hungry. 
The output is: <OUTPUT>The pen is red.</OUTPUT> 

Example 2. 
**Block 1:**
Intesa Sanpaolo is an Italian bank. It has its headquarter in Turin. 
**Block 2:**
Turin is a city on the north of Italy and it is where the headquerter of Intesa Sanpaolo is located. 
The output is: <OUTPUT>Intesa Sanpaolo is an Italian bank.</OUTPUT>

Example 3. 
**Block 1:**
The laptop is running hot.
**Block 2:**
Today it is sunny and the laptop is getting very hot.
The output is an empty string <OUTPUT></OUTPUT> since the unique information to keep (laptop running hot) is also contained in the second block.

Your turn to complete. 
**Block 1:**
%s
**Block 2:**
%s
The output is:

'''


PROMPT_KBB_CONFLICTS = '''

- I have a block of text, and I need you to identify evident conflictual information or strong contradictory statements within it. 
- Please highlight the specific conflicting statements and provide a brief explanation of why they are considered contradictory. 
- Ensure that the identified conflicts are based on clear evidence from the given text and not on assumptions or hypotheses or your previous knowledge.
- Do not use any your previous knowledge. Use only the contents of the given text. 
- Please enclose the rewritten text within <OUTPUT> </OUTPUT> tags. For example, it should be formatted as follows: <OUTPUT>Text</OUTPUT>.
- If no evident conflictual information or contradictory statements are detected, or if you are unsure, then return <OUTPUT>OK</OUTPUT>.
- Reason step by step. 

Example 1. 
**Text:**
I am hungry right now and the pen is red. 
I am full and won't eat again today.
Reasoning: In the first sentence I am hungry but in the second sentence I say that I won't eat again because I am full. They are contradictory statements.
The output is: <OUTPUT>In the first sentence I am hungry but in the second sentence I say that I won't eat again because I am full. They are contradictory statements.</OUTPUT> 

Example 2. 
**Text:**
Intesa Sanpaolo is an Italian bank. It has its headquarter in Turin. 
Turin is a city on the north of Italy and it is where the headquarter of Intesa Sanpaolo is located.
Reasoning: no contradictory statements here.
The output is:  <OUTPUT>OK</OUTPUT>

Example 3. 
**Text:**
The laptop is running hot.
Today it is sunny and the laptop is getting very hot due to the running job. 
Reasoning: no contradictory statements here.
The output is: <OUTPUT>OK</OUTPUT>. 

Example 4. 
**Text:**
The library operates under the following schedule:
Opening Time: 9:00 AM
Closing Time: 6:00 PM (18:00)
To access the reading room within the library, please ensure you have a valid student card. 
You can access the library at any time, provided you have a valid student card.
Reasoning: at the beginning the opening and the closing times are given, but then the text states that you can access the library at any time.
The output is: <OUTPUT>There is contradiction because at the beginning the opening and the closing times are given, but then the text states that you can access the library at any time.</OUTPUT>.

Your turn to complete.
**Text:**
%s
Reasoning: ...
The output is:

'''


PROMPT_KBB_CORRECT = '''

- I have two blocks of text. 
- I need you to revise the first block (Block 1) with the observation contained in the second block (Block 2).
- If there are any contradictions in the text, prioritize the information that appears later in the text of the Block 1.
- Remove conflictual information in the first block.
- Do not invent anything. Use only the information contained in the text.
- The output should be simple, structured, and have brief but informative sentences. 
- Please enclose the rewritten text within <OUTPUT> </OUTPUT> tags. For example, it should be formatted as follows: <OUTPUT>Revised text.</OUTPUT>
- Reason step by step. 

Example 1. 
**Block 1:**
I am hungry and the pen is red. I am full.
**Block 2:**
Reasoning: 
It seems that there is a contradiction. You cannot be hungry and full in the same time. I'm going to keep the information that appear later in the text (I am full).
The output is: <OUTPUT>I am full and the pen is red.</OUTPUT> 

Example 2. 
**Block 1:**
Intesa Sanpaolo is an American tech company. Its headquarter is in Turin. Intesa Sanpaolo is a Italian bank. 
**Block 2:**
Reasoning: 
In the first part of the text it states that Intesa Sanpaolo is an American tech company but in the second part it becomes an Italian bank. You need to keep the infromation that appears later: Intesa Sanpaolo is a Italian bank.
The output is: <OUTPUT>Intesa Sanpaolo is an Italian bank and its headquarter is in Turin.</OUTPUT>

Example 3. 
**Block 1:**
The hat and the pen are on the table. The laptop is updating. The pen is in the bag. 
**Block 2:**
Reasoning: 
There is conflictual information: from the first sentence we can learn that the pen is on the table but in the third sentence it is in the bag. The pen cannot be in two differente places at the same time. The information that appears later overwrites the previous one. The pen is in the bag and not on the table.  
The output is <OUTPUT>The hat is on the table, the pen is on the bag and the laptop is updating.</OUTPUT>

Your turn to complete. 
**Block 1:**
%s
**Block 2:**
%s
Reasoning: 
...
The output is:

'''