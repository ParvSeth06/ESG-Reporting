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
Raw Data Element Encountered,AI Action (Mapping Logic),Strict Guardrail Compliance
"A Table containing structured data (e.g., metric tons CO2​e, number of employees)","1. Identify the Metric: Analyze column/row headers to identify which metric this table relates to (e.g., GHG Emissions, Injuries, Water Withdrawal). 2. Check the Template Field: Use the metric name to find the corresponding GRI field (e.g., 11.1.5 Gross Direct GHG) in the template. 3. Populate/Append: If the field is [EMPTY], fill it with the extracted data. If the field is [FILLED], append the new data under a timestamp or sub-heading to preserve both pieces of information (""Append if already filled"" rule). 4. Flag as Mapped: Mark the specific data extracted from the table as ""Processed/Mapped.""","Strictly: Data extracted must be an exact value from the table. If a table contains irrelevant data (e.g., non-GRI metrics), ignore that data point but proceed with the table. No generation or inference."
"A Paragraph containing qualitative data (e.g., policies, rationale, management approach)","1. Search for Target Keywords: Analyze the paragraph content against a set of unfilled or partially filled narrative fields in the GRI 11 template (e.g., searching for ""anti-corruption policies,"" or ""flaring and venting effectiveness""). 2. Contextual Match: If the paragraph directly and completely addresses a specific GRI field, extract the relevant sentence(s). 3. Populate/Append: Add the text to the corresponding template field. If the field is already filled, append the new narrative (e.g., adding a specific policy detail found later). 4. Flag as Mapped: Mark the extracted section of the paragraph as ""Processed/Mapped.""","Strictly: If a paragraph contains redundant information already perfectly captured, it can be skipped/not appended. If the paragraph contains unstructured data not relevant to any template field, mark the paragraph as [IRRELEVANT] and continue. No data is invented."
</pre>
</html>