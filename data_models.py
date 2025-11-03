# data_models.py
"""
Defines the data structures for the GRI Reporting Agent, primarily the 
DisclosureEntry class that represents a single required disclosure.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DisclosureEntry:
    """
    Represents a single entry in the GRI Master Template.
    """
    ref_no: str
    topic: str
    disclosure_source: str
    data_field: str
    data_type: str # 'Metric' or 'Narrative'
    data: str = "" # Stores extracted data, can be appended to
    source_chunks: List[str] = field(default_factory=list)
    status: str = "[Data Missing/Omission]"

    def add_data(self, new_data: str, source_chunk_id: str):
        """
        Adds or appends data to the entry and logs the source.
        Adheres to the "append if already filled" rule.
        """
        if self.data: # If data already exists, append
            self.data += f"\n--- Appended Source ({source_chunk_id}) ---\n{new_data}"
        else: # Otherwise, set the initial data
            self.data = new_data
        
        if source_chunk_id not in self.source_chunks:
            self.source_chunks.append(source_chunk_id)
        
        self.status = "FOUND (POPULATED)"