import pytest
import httpx
import os
import tempfile
import json

BASE_URL = "http://localhost:8000"

@pytest.fixture
def sample_csv():
    data = """id,name,amount,category
1,Item A,100,Office
2,Item B,200,Electronics
3,Item C,150,Office
4,Item D,50,Furniture"""
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    f.write(data)
    f.close()
    yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)

@pytest.mark.asyncio
async def test_report_generation_pdf(sample_csv):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Upload CSV
        with open(sample_csv, 'rb') as f:
            resp = await client.post("/api/v1/data/upload", files={"file": f})
            assert resp.status_code == 200
            file_path = resp.json()["file_path"]

        # 2. Build Workflow with Report Node
        nodes = [
            {
                "id": "input_1",
                "type": "input",
                "data": {"label": "Source CSV", "config": {"file_path": file_path}}
            },
            {
                "id": "report_1",
                "type": "output",
                "data": {
                    "label": "Monthly Report", 
                    "subtype": "report",
                    "config": {
                        "title": "Sales Report Q1",
                        "description": "This report summarizes the sales performance for Q1.",
                        "format": "PDF",
                        "font": "NanumGothic",
                        "sections": [
                            {"heading": "Summary Stats", "type": "stats"},
                            {"heading": "Data Table", "type": "table"},
                            {"heading": "Remarks", "type": "text", "content": "Total items processed: {{row_count}} into {{column_count}} categories."}
                        ]
                    }
                }
            }
        ]
        
        edges = [
            {"id": "e1", "source": "input_1", "target": "report_1"}
        ]

        report_config = nodes[1]["data"]["config"]

        # 3. Request Report Generation
        resp = await client.post("/api/v1/workflows/report", json={
            "nodes": nodes,
            "edges": edges,
            "report_config": report_config
        })
        
        if resp.status_code != 200:
            print("PDF Report Generation Error:", resp.text)
            
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "success"
        assert "report_url" in result
        assert result["report_url"].endswith(".pdf")

        # 4. Download and Verify PDF
        download_url = result["report_url"]
        dl_resp = await client.get(download_url)
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
        # Check for PDF header
        assert dl_resp.content.startswith(b"%PDF")

@pytest.mark.asyncio
async def test_report_generation_markdown(sample_csv):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Upload CSV
        with open(sample_csv, 'rb') as f:
            resp = await client.post("/api/v1/data/upload", files={"file": f})
            assert resp.status_code == 200
            file_path = resp.json()["file_path"]

        # 2. Build Workflow
        nodes = [
            {"id": "in", "type": "input", "data": {"config": {"file_path": file_path}}},
            {
                "id": "rep",
                "type": "output",
                "data": {
                    "subtype": "report",
                    "config": {
                        "title": "MD Report",
                        "format": "Markdown",
                        "sections": [
                            {"heading": "Table", "type": "table"},
                            {"heading": "Info", "type": "text", "content": "Rows: {{row_count}}"}
                        ]
                    }
                }
            }
        ]
        edges = [{"id": "e1", "source": "in", "target": "rep"}]

        # 3. Generate MD Report
        resp = await client.post("/api/v1/workflows/report", json={
            "nodes": nodes,
            "edges": edges,
            "report_config": nodes[1]["data"]["config"]
        })
        
        assert resp.status_code == 200
        result = resp.json()
        assert result["report_url"].endswith(".md")

        # 4. Verify Content
        dl_resp = await client.get(result["report_url"])
        assert dl_resp.status_code == 200
        content = dl_resp.text
        assert "# MD Report" in content
        assert "## Table" in content
        assert "Rows: 4" in content
