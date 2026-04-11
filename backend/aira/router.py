from aira.admin_agent import get_admin_prompt
from aira.faculty_agent import get_faculty_prompt
from aira.student_agent import get_student_prompt
import ai_client
from app.db import query
from app.routes.aira import MCP_TOOLS, execute_tool, _get_db_context, get_user_scope
import json


def _format_tool_result_for_model(tool_name: str, tool_result: dict) -> str:
    """Convert a raw tool result dict into a clean text summary for the LLM to synthesize."""
    if not tool_result.get("success"):
        return f"Tool '{tool_name}' returned an error: {tool_result.get('error', 'Unknown error')}"

    data = tool_result.get("data")

    # Summary tool (nested dict)
    if isinstance(data, dict) and "summary" in data:
        s = data["summary"]
        dept_lines = ""
        if data.get("departments"):
            dept_lines = "\nBy Department:\n" + "\n".join(
                f"  - {d['name']}: {d['students']} students, {d['staff']} staff"
                for d in data["departments"]
            )
        return (
            f"College Summary:\n"
            f"  Active Students: {s.get('active_students', 0)}\n"
            f"  Active Staff: {s.get('active_staff', 0)}\n"
            f"  Departments: {s.get('departments', 0)}\n"
            f"  Courses: {s.get('courses', 0)}\n"
            f"  Subjects: {s.get('subjects', 0)}\n"
            f"  Total Fees Collected: {s.get('total_fees_collected', 0):.2f}\n"
            f"  Avg Attendance: {s.get('avg_attendance_pct', 0)}%" + dept_lines
        )

    # Simple balance dict
    if isinstance(data, dict) and "balance" in data:
        return f"Fee balance: {data['balance']:.2f}"

    # List of records
    if isinstance(data, list):
        if not data:
            return f"Tool '{tool_name}' returned 0 records."
        # Serialize top 30 records as compact JSON for LLM to reason about
        sample = data[:30]
        return f"Tool '{tool_name}' returned {len(data)} records. Sample (up to 30):\n" + json.dumps(sample, default=str, ensure_ascii=False)

    return f"Tool '{tool_name}' result: {json.dumps(data, default=str, ensure_ascii=False)[:1000]}"


def route_query(message: str, user: dict, history: list, page_context: str, scope: dict):
    role = user.get("role", "student")

    # --- Build rich, live-context-injected system prompt ---
    db_context = _get_db_context(user)  # Live DB snapshot scoped to user's role

    if role in ["admin", "super_admin"]:
        base_prompt = get_admin_prompt()
    elif role == "staff":
        depts = query(
            "SELECT name FROM department WHERE department_id IN %s",
            (tuple(scope.get("dept_ids", [0])),)
        ) if scope.get("dept_ids") else []
        dept_names = [d["name"] for d in depts] if depts else []
        base_prompt = get_faculty_prompt(dept_names, [str(s) for s in scope.get("section_ids", [])])
    else:
        base_prompt = get_student_prompt(user.get("username", "Student"))

    # Inject live DB context + page context into the system prompt
    system_prompt = base_prompt + db_context + f"\nCurrent Page: {page_context}\n"

    # --- First LLM call: intent + tool call detection ---
    response = ai_client.generate_response(
        system_prompt=system_prompt,
        messages=history,
        tools=MCP_TOOLS
    )

    if not response.get("success"):
        return {"response": f"AI Engine Error: {response.get('error')}"}

    tool_calls_made = []

    # --- Handle Tool Calls from Gemma 4 ---
    if response.get("tool_calls"):
        all_tool_results = []

        for tc in response["tool_calls"]:
            tool_name = tc.get("name")
            tool_args = tc.get("arguments", {})

            try:
                tool_result = execute_tool(tool_name, tool_args, user)
                tool_calls_made.append({"name": tool_name, "args": tool_args, "result": "executed"})

                # If the tool produced a frontend widget (report download, navigation, bulk confirm)
                # return it directly — the frontend renders it specially
                if isinstance(tool_result, dict) and tool_result.get("response_type") in ["report", "navigate", "bulk_confirm"]:
                    return tool_result

                # Otherwise, format the result for the LLM to synthesize into natural language
                result_text = _format_tool_result_for_model(tool_name, tool_result)
                all_tool_results.append(f"[Tool: {tool_name}]\n{result_text}")

            except Exception as e:
                all_tool_results.append(f"[Tool: {tool_name}] ERROR: {str(e)}")

        if all_tool_results:
            # --- Second LLM call: synthesize tool results into a clean natural-language answer ---
            synthesis_history = history + [
                {"role": "assistant", "content": response.get("message", "")},
                {
                    "role": "user",
                    "content": (
                        "The database tools were executed. Here are the results:\n\n"
                        + "\n\n".join(all_tool_results)
                        + "\n\nPlease synthesize this data into a clean, well-formatted markdown response "
                          "for the user. Use markdown tables where there are multiple rows. "
                          "Be concise and highlight the key insights."
                    )
                }
            ]
            synthesis = ai_client.generate_response(
                system_prompt=system_prompt,
                messages=synthesis_history,
                tools=None  # No tools needed for synthesis
            )
            if synthesis.get("success") and synthesis.get("message"):
                return {"response": synthesis["message"], "tool_calls": tool_calls_made}

            # Fallback if synthesis fails
            return {"response": "\n\n".join(all_tool_results), "tool_calls": tool_calls_made}

    # --- No tool call: return direct LLM response ---
    return {"response": response.get("message", ""), "tool_calls": tool_calls_made}
