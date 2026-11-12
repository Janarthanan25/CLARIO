import os
import json
from pathlib import Path
import fitz  # PyMuPDF
import docx
import pandas as pd
from services.ai_service import ai_service

class DocumentProcessor:
    """
    Intelligent processor for multi-format documents:
    PDF, DOCX, TXT, CSV. Extracts text, computes analytics,
    chunks content, and performs grounded Q&A.
    """

    @staticmethod
    def extract_text(file_path, file_type):
        """
        Extract clean text from supported document types.
        """
        file_path = str(file_path)
        ext = file_type.lower().replace('.', '')
        
        if ext == 'pdf':
            return DocumentProcessor._extract_pdf(file_path)
        elif ext == 'docx':
            return DocumentProcessor._extract_docx(file_path)
        elif ext == 'txt':
            return DocumentProcessor._extract_txt(file_path)
        elif ext == 'csv':
            return DocumentProcessor._extract_csv_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")

    @staticmethod
    def _extract_pdf(file_path):
        text_parts = []
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
        return "\n\n".join(text_parts).strip()

    @staticmethod
    def _extract_docx(file_path):
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                paragraphs.append(row_text)
        return "\n\n".join(paragraphs).strip()

    @staticmethod
    def _extract_txt(file_path):
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read().strip()
            except UnicodeDecodeError:
                continue
        with open(file_path, 'r', errors='ignore') as f:
            return f.read().strip()

    @staticmethod
    def _extract_csv_text(file_path):
        df = pd.read_csv(file_path)
        preview = df.head(20).to_string(index=False)
        stats = f"CSV dataset contains {len(df)} rows and {len(df.columns)} columns.\nColumns: {', '.join(df.columns)}\n\nFirst 20 rows preview:\n{preview}"
        return stats

    @staticmethod
    def process_csv(file_path):
        """
        Produce rich analytical summary and Chart.js specs for CSV files.
        """
        df = pd.read_csv(file_path)
        row_count, col_count = df.shape
        
        columns_info = []
        numerical_cols = []
        categorical_cols = []
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique())
            
            col_meta = {
                'name': col,
                'dtype': dtype,
                'missing_values': missing,
                'unique_count': unique_count
            }
            
            if pd.api.types.is_numeric_dtype(df[col]):
                numerical_cols.append(col)
                col_meta['min'] = float(df[col].min()) if not df[col].empty and not pd.isna(df[col].min()) else None
                col_meta['max'] = float(df[col].max()) if not df[col].empty and not pd.isna(df[col].max()) else None
                col_meta['mean'] = round(float(df[col].mean()), 2) if not df[col].empty and not pd.isna(df[col].mean()) else None
            else:
                categorical_cols.append(col)
                top_values = df[col].value_counts().head(5).to_dict()
                col_meta['top_values'] = {str(k): int(v) for k, v in top_values.items()}
                
            columns_info.append(col_meta)

        # Generate chart configuration specs
        chart_config = None
        if numerical_cols and categorical_cols:
            cat = categorical_cols[0]
            num = numerical_cols[0]
            grouped = df.groupby(cat)[num].mean().head(10).reset_index()
            chart_config = {
                'type': 'bar',
                'title': f'Average {num} by {cat}',
                'labels': [str(x) for x in grouped[cat].tolist()],
                'data': [round(float(y), 2) for y in grouped[num].tolist()],
                'label': f'Avg {num}'
            }
        elif len(numerical_cols) >= 2:
            num1, num2 = numerical_cols[0], numerical_cols[1]
            chart_config = {
                'type': 'line',
                'title': f'{num2} across {num1}',
                'labels': [str(x) for x in df[num1].head(15).tolist()],
                'data': [round(float(y), 2) for y in df[num2].head(15).tolist()],
                'label': num2
            }
        elif categorical_cols:
            cat = categorical_cols[0]
            counts = df[cat].value_counts().head(8).to_dict()
            chart_config = {
                'type': 'pie',
                'title': f'Distribution of {cat}',
                'labels': [str(k) for k in counts.keys()],
                'data': [int(v) for v in counts.values()],
                'label': cat
            }

        return {
            'row_count': row_count,
            'col_count': col_count,
            'columns': columns_info,
            'preview_rows': df.head(10).fillna('').to_dict(orient='records'),
            'chart_config': chart_config
        }

    @staticmethod
    def answer_question(document_text, question, doc_title=None):
        """
        Ask question against document contents with strict factual grounding.
        """
        # Chunk text or select most relevant paragraphs
        paragraphs = [p for p in document_text.split('\n\n') if len(p.strip()) > 30]
        q_words = set(question.lower().split())
        
        # Simple TF-based relevance scoring
        scored_paras = []
        for p in paragraphs:
            score = sum(1 for w in q_words if w in p.lower())
            scored_paras.append((score, p))
            
        scored_paras.sort(key=lambda x: x[0], reverse=True)
        top_context = "\n\n---\n\n".join([p for _, p in scored_paras[:6]])
        if not top_context:
            top_context = document_text[:6000]

        system_instruction = (
            "You are CLARIO Document Intelligence Assistant. Answer the user's question "
            "strictly using the facts provided in the document context. If the answer cannot "
            "be found in the text, clearly state that the document does not contain that information. "
            "Do not hallucinate or speculate."
        )
        prompt = (
            f"Document Title: {doc_title or 'Analyzed File'}\n\n"
            f"Relevant Document Passages:\n{top_context}\n\n"
            f"User Question: {question}\n\n"
            "Provide a clear, accurate, and concise answer citing specific sections where applicable."
        )

        res = ai_service.generate_response(prompt, system_instruction=system_instruction)
        return {
            'answer': res['text'],
            'source': res['source'],
            'notice': res.get('notice')
        }
