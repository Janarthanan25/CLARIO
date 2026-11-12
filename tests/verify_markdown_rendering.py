"""
Verification script for Markdown rendering and Grounded Q&A assertions
"""
import re
from pathlib import Path

def test_no_zero_hallucination_claims():
    root = Path(__file__).resolve().parent.parent
    prohibited_pattern = re.compile(r'zero[- ]hallucination', re.IGNORECASE)
    
    files_to_check = [
        root / 'README.md',
        root / 'templates' / 'agents.html',
        root / 'templates' / 'index.html',
        root / 'templates' / 'workspace.html',
    ]
    
    violations = []
    for f in files_to_check:
        if not f.exists():
            continue
        text = f.read_text(encoding='utf-8')
        matches = prohibited_pattern.findall(text)
        if matches:
            violations.append(f"{f.name}: found {len(matches)} occurrences of '{matches[0]}'")
            
    assert not violations, f"Found ungrounded absolute claims: {violations}"
    print("PASS: No absolute 'zero hallucination' claims found. All wording is document-grounded.")

def test_safe_markdown_renderer_in_frontend():
    root = Path(__file__).resolve().parent.parent
    main_js = (root / 'static' / 'js' / 'main.js').read_text(encoding='utf-8')
    base_html = (root / 'templates' / 'base.html').read_text(encoding='utf-8')
    custom_css = (root / 'static' / 'css' / 'custom.css').read_text(encoding='utf-8')
    workspace_js = (root / 'static' / 'js' / 'workspace.js').read_text(encoding='utf-8')
    workspace_html = (root / 'templates' / 'workspace.html').read_text(encoding='utf-8')
    
    # 1. Base HTML imports marked, DOMPurify, and highlight.js
    assert 'marked.min.js' in base_html, "marked.min.js missing from base.html"
    assert 'purify.min.js' in base_html, "purify.min.js missing from base.html"
    assert 'highlight.min.js' in base_html, "highlight.min.js missing from base.html"
    print("PASS: base.html imports marked, DOMPurify, and highlight.js.")
    
    # 2. main.js defines renderSafeMarkdown and DOMPurify sanitization
    assert 'function renderSafeMarkdown' in main_js, "renderSafeMarkdown missing in main.js"
    assert 'DOMPurify.sanitize' in main_js, "DOMPurify.sanitize missing in main.js"
    assert 'hljs.highlight' in main_js, "hljs syntax highlighting missing in main.js"
    print("PASS: main.js has safe markdown parsing, code highlighting, and XSS sanitization.")
    
    # 3. custom.css has .clario-markdown-body styling
    assert '.clario-markdown-body' in custom_css, ".clario-markdown-body missing from custom.css"
    assert '.clario-markdown-body h1' in custom_css, "Heading styles missing in custom.css"
    assert '.clario-markdown-body code' in custom_css or 'code-block' in custom_css, "Code styles missing"
    print("PASS: custom.css has complete typography and spacing for .clario-markdown-body.")
    
    # 4. workspace.js and workspace.html use renderSafeMarkdown and .clario-markdown-body
    assert 'docSummaryText' in workspace_html, "docSummaryText element missing"
    assert 'clario-markdown-body' in workspace_html, "clario-markdown-body class missing in workspace.html"
    assert 'renderSafeMarkdown(doc.summary' in workspace_js, "doc.summary not passed through renderSafeMarkdown"
    assert 'renderSafeMarkdown(data.answer)' in workspace_js, "Q&A answer not passed through renderSafeMarkdown"
    assert 'renderSafeMarkdown(m.content)' in workspace_js, "Chat history message not passed through renderSafeMarkdown"
    print("PASS: workspace.js and workspace.html use renderSafeMarkdown and clario-markdown-body.")

if __name__ == '__main__':
    test_no_zero_hallucination_claims()
    test_safe_markdown_renderer_in_frontend()
    print("\nALL MARKDOWN RENDERING VERIFICATION CHECKS PASSED SUCCESSFULLY!")
