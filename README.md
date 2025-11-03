<html>
<h2>this is the repo for AI Agent for ESG report generation</h2>
<p>
<br>
step1 : raw ingestion
</br>
<br> 
    data parsing and data validation
</br><br>
step2 : Knowledge base including the LLM logic
</br><br> 
step3 : reasoning and decision making
</br><br>
step4 : actuator and action : production of report plus feedback
</br><br>
step5 : learning and adaption : knowledge update loop
</br>
</p>
<pre>
ask the company whch sector does it belong (for example : oil and gas sector)
analyse the company data that is the qualitative and quantitative data
in accordance with the gri standards , ie , from the knowledge base , we extract the required data and make report
</pre>
<br></br>
<pre>
data ingestion and mapping :
    data acquisition and structuring
        breaking down into chunks
        structured data (tables) and unstructured data

    Data Extraction and Mapping
        Strategy for Quantitative Metrics (High Precision Mapping): 
            Metric Identification (Keyword/Context Matching)
            Unit and Boundary Validation
            Data Placement
        Strategy for Qualitative Narratives (Contextual Mapping)
            Prompt-Based Search 
            Sentence/Paragraph Extraction
            Synthesis and Placement
        Strict Data Guardrail (Critical Instruction)
            The AI must NOT generate or infer data to fill empty fields
    Validation and Gap Analysis
</pre>
<br></br>
<pre>else use : single pass strategy : 
    we have the template for report
    Single-Pass Ingestion and Mapping (The Core Logic)
        https://docs.google.com/spreadsheets/d/1iFIzk3zb4QT9EZnPAn60PZmTQN0LLNOkh-gFJ6qhPHc/edit?gid=1817010029#gid=1817010029
    
</pre>
</html>