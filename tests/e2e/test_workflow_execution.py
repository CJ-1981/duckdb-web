import pytest
import httpx
import asyncio
import tempfile
import os
import json

BASE_URL = "http://localhost:8000/api/v1"

@pytest.fixture
def sample_csv():
    # Sample data with commas and spaces - corrected CSV quoting
    data = """id,name,value,date
1,"  Alice "," $1,200.50 ",2023-01-01
2," Bob "," $3,400.00 ",2023-02-01
3," CHARLIE "," 500 ",2023-03-01
4," "," "," 2023-04-01 " """
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    f.write(data)
    f.close()
    yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)

@pytest.fixture
def other_csv():
    data = "id,location\n1,NYC\n2,LA\n3,CHI"
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    f.write(data)
    f.close()
    yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)

@pytest.mark.asyncio
async def test_complete_cleaning_filtering_joining_pipeline(sample_csv, other_csv):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Upload both files
        with open(sample_csv, 'rb') as f1:
            resp1 = await client.post("/data/upload", files={"file": f1})
            assert resp1.status_code == 200
            file1_path = resp1.json()["file_path"]
        
        with open(other_csv, 'rb') as f2:
            resp2 = await client.post("/data/upload", files={"file": f2})
            assert resp2.status_code == 200
            file2_path = resp2.json()["file_path"]

        # 2. Build a workflow
        # [CSV1] -> [Clean Value] -> [Filter Value > 1000] -> [Join with CSV2] -> [Output]
        nodes = [
            {
                "id": "input_1",
                "type": "input",
                "data": {"label": "Source 1", "config": {"file_path": file1_path}}
            },
            {
                "id": "clean_1",
                "type": "default",
                "data": {
                    "label": "Clean Numeric", 
                    "subtype": "clean", 
                    "config": {"column": "value", "operation": "numeric"}
                }
            },
            {
                "id": "filter_1",
                "type": "default",
                "data": {
                    "label": "Filter Records", 
                    "subtype": "filter", 
                    "config": {"column": "value", "operator": ">", "value": "1000"}
                }
            },
            {
                "id": "input_2",
                "type": "input",
                "data": {"label": "Source 2", "config": {"file_path": file2_path}}
            },
            {
                "id": "combine_1",
                "type": "default",
                "data": {
                    "label": "Join Records", 
                    "subtype": "combine", 
                    "config": {"column": "id", "joinType": "inner"}
                }
            },
            {
                "id": "output_1",
                "type": "output",
                "data": {"label": "Final Output", "config": {"format": "CSV", "filename": "test_e2e_result.csv"}}
            }
        ]
        
        edges = [
            {"id": "e1", "source": "input_1", "target": "clean_1"},
            {"id": "e2", "source": "clean_1", "target": "filter_1"},
            {"id": "e3", "source": "filter_1", "target": "combine_1"},
            {"id": "e4", "source": "input_2", "target": "combine_1"},
            {"id": "e5", "source": "combine_1", "target": "output_1"}
        ]

        # 3. Execute Workflow
        exec_resp = await client.post("/workflows/execute", json={"nodes": nodes, "edges": edges})
        
        # Check for success
        if exec_resp.status_code != 200:
             print("Execution failed!")
             print(exec_resp.text)
             
        assert exec_resp.status_code == 200
        result = exec_resp.json()
        assert result["row_count"] == 2  # Alice and Bob should pass the filter after cleaning
        
        # Check preview data
        preview = result["preview"]
        assert len(preview) == 2
        assert any(row["location"] == "NYC" for row in preview)
        assert any(row["location"] == "LA" for row in preview)

@pytest.mark.asyncio
async def test_filter_operators(sample_csv):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        with open(sample_csv, 'rb') as f:
            resp = await client.post("/data/upload", files={"file": f})
            file_path = resp.json()["file_path"]

        # Test 'starts_with' (requires trim because of data)
        nodes = [
            {"id": "in", "type": "input", "data": {"config": {"file_path": file_path}}},
            {
                "id": "c", 
                "type": "default", 
                "data": {"subtype": "clean", "config": {"column": "name", "operation": "trim"}}
            },
            {
                "id": "f", 
                "type": "default", 
                "data": {"subtype": "filter", "config": {"column": "name", "operator": "starts_with", "value": "A"}}
            },
            {"id": "out", "type": "output", "data": {"config": {"format": "CSV"}}}
        ]
        edges = [
            {"id": "e1", "source": "in", "target": "c"},
            {"id": "e2", "source": "c", "target": "f"},
            {"id": "e3", "source": "f", "target": "out"}
        ]
        
        resp = await client.post("/workflows/execute", json={"nodes": nodes, "edges": edges})
        if resp.status_code != 200:
            print("Filter op test failed:", resp.text)
        assert resp.status_code == 200
        assert resp.json()["row_count"] == 1 # Alice (name starts with A)

@pytest.mark.asyncio
async def test_case_transformation(sample_csv):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        with open(sample_csv, 'rb') as f:
            resp = await client.post("/data/upload", files={"file": f})
            file_path = resp.json()["file_path"]

        nodes = [
            {"id": "in", "type": "input", "data": {"config": {"file_path": file_path}}},
            {
                "id": "c", 
                "type": "default", 
                "data": {"subtype": "clean", "config": {"column": "name", "operation": "upper"}}
            },
            {"id": "out", "type": "output", "data": {"config": {"format": "CSV"}}}
        ]
        edges = [{"id": "e1", "source": "in", "target": "c"}, {"id": "e2", "source": "c", "target": "out"}]
        
        resp = await client.post("/workflows/execute", json={"nodes": nodes, "edges": edges})
        if resp.status_code != 200:
             print("Case trans test failed:", resp.text)
        assert resp.status_code == 200
        # Result should show all names in UPPERCASE (verified via preview)
        preview = resp.json()["preview"]
        assert all(row["name"].upper() == row["name"] for row in preview if row["name"])
