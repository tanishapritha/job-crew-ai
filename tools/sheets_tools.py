from crewai.tools import tool
import json
from sheets_client import get_sheet

@tool("SheetsReadTool")
def sheets_read_tool(input: str) -> list[list]:
    """Reads all rows from a Google Sheet. Input should be a JSON string with {"sheet_name": "Name"}"""
    try:
        data = json.loads(input)
        sheet_name = data.get("sheet_name")
        if not sheet_name: return [[]]
        sheet = get_sheet(sheet_name)
        return sheet.get_all_values()
    except Exception as e:
        return [[str(e)]]

@tool("SheetsWriteTool")
def sheets_write_tool(input: str) -> str:
    """Appends a row to a Google Sheet. Input: JSON string with {"sheet_name": "Name", "row": []}"""
    try:
        data = json.loads(input)
        sheet_name = data.get("sheet_name")
        row = data.get("row")
        if not sheet_name or not isinstance(row, list): return "Error: Invalid arguments"
        sheet = get_sheet(sheet_name)
        sheet.append_row(row, value_input_option="USER_ENTERED")
        return "OK"
    except Exception as e:
        return f"Error: {e}"

@tool("SheetsUpdateCellTool")
def sheets_update_cell_tool(input: str) -> str:
    """Updates a cell in a sheet. Input: JSON string {"sheet_name": "Name", "row": 1, "col": 1, "value": "val"}"""
    try:
        data = json.loads(input)
        sheet_name = data.get("sheet_name")
        r = int(data.get("row"))
        c = int(data.get("col"))
        val = str(data.get("value"))
        sheet = get_sheet(sheet_name)
        sheet.update_cell(r, c, val)
        return "OK"
    except Exception as e:
        return f"Error: {e}"
