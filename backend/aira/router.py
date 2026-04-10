from aira.admin_agent import get_admin_prompt
from aira.faculty_agent import get_faculty_prompt
from aira.student_agent import get_student_prompt
import ai_client
from app.db import query
from app.routes.aira import MCP_TOOLS, execute_tool

def route_query(message: str, user: dict, history: list, page_context: str, scope: dict):
    role = user.get("role", "student")
    
    if role in ["admin", "super_admin"]:
        system_prompt = get_admin_prompt()
    elif role == "staff":
        depts = query("SELECT name FROM department WHERE department_id IN %s", (tuple(scope.get("dept_ids", [0])),)) if scope.get("dept_ids") else []
        dept_names = [d["name"] for d in depts] if depts else []
        system_prompt = get_faculty_prompt(dept_names, [str(s) for s in scope.get("section_ids", [])])
    else:
        system_prompt = get_student_prompt(user.get("username", "Student"))
        
    system_prompt += f"\nPage Context: {page_context}"

    response = ai_client.generate_response(
        system_prompt=system_prompt,
        messages=history,
        tools=MCP_TOOLS
    )

    if not response.get("success"):
        return {"response": f"AI Engine Error: {response.get('error')}"}
        
    tool_calls_made = []
    
    # Check if a tool call was requested by Gemma 4
    if "tool_calls" in response and response["tool_calls"]:
        for tc in response["tool_calls"]:
            tool_name = tc.get("name")
            tool_args = tc.get("arguments", {})
            try:
                tool_result = execute_tool(tool_name, tool_args, user)
                tool_calls_made.append({"name": tool_name, "args": tool_args, "result": "executed"})
                
                # We could feed this back to the model, but to save tokens/time for the hackathon,
                # if the tool generated a frontend widget (like a bulk_confirm or report), 
                # we just return the tool_result directly to the frontend.
                if isinstance(tool_result, dict) and tool_result.get("response_type") in ["report", "navigate", "bulk_confirm"]:
                    return tool_result
                
                # Otherwise, give a generic success or feed it back.
                # For this implementation, returning real data directly as fallback string:
                return {
                    "response": f"Executed tool: {tool_name}. Result: {str(tool_result)[:500]}...", 
                    "tool_calls": tool_calls_made
                }
            except Exception as e:
                return {"response": f"Failed executing tool {tool_name}: {str(e)}"}
                
    return {"response": response.get("message", ""), "tool_calls": tool_calls_made}
