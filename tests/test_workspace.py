import io
from modules.workspace.processor import DocumentProcessor

def test_document_processor_txt():
    content = "CLARIO Enterprise Report.\nTotal revenue was $1,200,000 on October 15, 2026."
    ans = DocumentProcessor.answer_question(content, "What was the total revenue?", "Test Doc")
    assert "1,200,000" in ans['answer'] or "revenue" in ans['answer'].lower()

def test_document_processor_csv(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("department,budget\nEngineering,50000\nMarketing,25000\nSales,35000")
    res = DocumentProcessor.process_csv(str(csv_file))
    assert res['row_count'] == 3
    assert res['col_count'] == 2
    assert res['chart_config'] is not None

def test_document_upload_and_chat(logged_in_client):
    data = {
        'file': (io.BytesIO(b"Quarterly corporate statement. Filing deadline is November 30, 2026."), 'report.txt')
    }
    upload_res = logged_in_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert upload_res.status_code == 200
    doc_data = upload_res.get_json()
    assert doc_data['success'] is True
    doc_id = doc_data['document']['id']

    # Chat against the document
    chat_res = logged_in_client.post('/api/documents/chat', json={
        'document_id': doc_id,
        'question': 'What is the filing deadline?'
    })
    assert chat_res.status_code == 200
    chat_json = chat_res.get_json()
    assert chat_json['success'] is True
    assert len(chat_json['answer']) > 0

    # Verify persistent conversation history
    msg_res = logged_in_client.get(f'/api/documents/{doc_id}/messages')
    assert msg_res.status_code == 200
    msg_data = msg_res.get_json()
    assert msg_data['success'] is True
    assert len(msg_data['messages']) >= 2

    # Delete document
    del_res = logged_in_client.delete(f'/api/documents/{doc_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True
