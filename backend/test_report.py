from app import create_app
from app.db import query
from app.routes.aira import _execute_generate_report

app = create_app()

with app.app_context():
    # Pass a dummy user dict
    user = {"user_id": 1}
    tool_args = {"report_type": "defaulter", "format": "pdf"}
    
    print("Executing generate_report tool...")
    res = _execute_generate_report(tool_args, user)
    print("Result:")
    print(res)
