from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List

class ChunkingModel:
    def __init__(self, chunk_size : int, chunk_overlap : int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunker = RecursiveCharacterTextSplitter(length_function = len,
                                           chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
    
    def combine_chunks(self, docs : List[Document], chunk_size: int) -> list:
        """
        Combines chunks of text documents to ensure no chunk is smaller than the specified chunk_size.

        Args:
        - docs (list of Document): List of documents with `page_content` as text.
        - chunk_size (int): Desired minimum size of each chunk.
        - length_function (function): A function to calculate the length of each chunk.

        Returns:
        - combined_docs (list of Document): List of combined documents with each chunk having at least `chunk_size` length units.
        """
        # Handle case where the number of documents is <= 1
        if len(docs) <= 1:
            return docs

        combined_docs = []
        temp_content = docs[0]

        for doc in docs[1:]:
            temp_content += doc
            if len(temp_content) >= chunk_size:
                combined_docs.append(temp_content)
                temp_content = ""

        # Add any remaining content in `temp_content` to `combined_docs`
        if temp_content:
            combined_docs.append(temp_content)

        return combined_docs
    
    def split_text(self, text : str):
        docs = self.chunker.split_text(text)
        return self.combine_chunks(docs=docs, chunk_size=self.chunk_size)