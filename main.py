import os, sys, traceback as tb
from io import StringIO
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def execute_python_code(code: str) -> dict:
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        exec(code, {})
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}
    except Exception:
        output = tb.format_exc()
        return {"success": False, "output": output}
    finally:
        sys.stdout = old_stdout

class ErrorAnalysis(BaseModel):
    error_lines: List[int]

def analyze_error_with_ai(code: str, traceback: str) -> List[int]:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = f"""Analyze this Python code and its error traceback.
Identify the line number(s) where the error occurred.
CODE:\n{code}\nTRACEBACK:\n{traceback}\nReturn the line number(s) where the error is located."""
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={"error_lines": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.INTEGER)
                )},
                required=["error_lines"],
            ),
        ),
    )
    return ErrorAnalysis.model_validate_json(response.text).error_lines

class CodeRequest(BaseModel):
    code: str

@app.post("/code-interpreter")
async def code_interpreter(req: CodeRequest):
    execution = execute_python_code(req.code)
    if execution["success"]:
        return {"error": [], "result": execution["output"]}
    else:
        error_lines = analyze_error_with_ai(req.code, execution["output"])
        return {"error": error_lines, "result": execution["output"]}