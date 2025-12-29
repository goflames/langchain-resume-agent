import os
from typing import TypedDict, List, Annotated
import operator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from main import build_llm
from tools import read_resume_file, generate_resume_pdf

# -------------------------------------------------------------------------
# Default Resume Template
# -------------------------------------------------------------------------
DEFAULT_RESUME_TEMPLATE = """
# 姓名

联系电话：xxx | 邮箱：xxx | 个人主页/博客：xxx

## 个人简介
（简短总结个人优势、经验年限和核心竞争力）

## 教育背景
**学校名称** | 专业 | 学历 | 时间
*   主修课程：xxx
*   荣誉奖项：xxx

## 技能清单
*   **编程语言**：xxx
*   **框架/工具**：xxx
*   **其他**：xxx

## 工作经历
**公司名称** | 职位 | 时间
*   **项目/职责**：简要描述项目背景或职责范围。
*   **行动/贡献**：详细描述你做了什么，使用了什么技术。
*   **成果**：量化成果（如提升了xx%效率，减少了xx%bug）。

## 项目经验
**项目名称** | 角色 | 时间
*   **项目描述**：xxx
*   **技术栈**：xxx
*   **主要贡献**：xxx
"""

# -------------------------------------------------------------------------
# 1. Memory / State Definition
# -------------------------------------------------------------------------
class AgentState(TypedDict):
    """
    The state of the agent, acting as its short-term memory across the workflow.
    """
    resume_file_path: str
    user_requirements: str  # User's additional requirements
    template_content: str   # Resume format template (User provided or Default)
    original_content: str
    analysis_report: str
    optimization_plan: str
    optimized_content: str
    pdf_output_path: str
    # Keep track of conversation history if needed (optional for this linear flow)
    messages: Annotated[List[BaseMessage], operator.add]

# -------------------------------------------------------------------------
# 2. Nodes Implementation (Perception, Processing, Planning, Action)
# -------------------------------------------------------------------------

def perception_node(state: AgentState):
    """
    Perception Module: Gathers information from the environment (resume file).
    """
    print("--- [Step 1] Perception: Reading Resume File ---")
    file_path = state['resume_file_path']
    content = read_resume_file(file_path)
    
    if content.startswith("Error"):
        # In a real agent, we might raise an error or ask for input again.
        print(f"Failed to read file: {content}")
        return {"original_content": ""}
        
    return {"original_content": content}

def analysis_node(state: AgentState):
    """
    Processing Module (Part 1): Analyzes the input data to understand current status.
    """
    print("--- [Step 2] Processing: Analyzing Resume ---")
    content = state['original_content']
    requirements = state.get('user_requirements', '')
    
    if not content:
        return {"analysis_report": "No content to analyze."}
    
    llm = build_llm()
    
    system_prompt = "你是一个资深的HR和简历专家。请详细分析以下简历内容的优缺点，指出格式、内容、用词等方面的问题。"
    user_msg = f"简历内容：\n{content}"
    
    if requirements:
        user_msg += f"\n\n用户附加要求：\n{requirements}\n请重点结合用户的附加要求进行分析。"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_msg}")
    ])
    chain = prompt | llm
    response = chain.invoke({"user_msg": user_msg})
    
    return {"analysis_report": response.content}

def planning_node(state: AgentState):
    """
    Planning Module: Decides on a plan of action based on the analysis.
    """
    print("--- [Step 3] Planning: Creating Optimization Plan ---")
    analysis = state['analysis_report']
    requirements = state.get('user_requirements', '')
    
    if not analysis:
        return {"optimization_plan": "No analysis available."}

    llm = build_llm()
    
    user_msg = f"分析报告：\n{analysis}"
    if requirements:
        user_msg += f"\n\n用户附加要求：\n{requirements}\n制定计划时请务必满足这些要求。"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "根据简历的分析报告，制定一个详细的修改计划。列出具体的修改步骤和策略，以便下一步执行模块进行重写。"),
        ("user", "{user_msg}")
    ])
    chain = prompt | llm
    response = chain.invoke({"user_msg": user_msg})
    
    return {"optimization_plan": response.content}

def execution_node(state: AgentState):
    """
    Processing Module (Part 2): Executes the plan (Rewriting the resume).
    """
    print("--- [Step 4] Processing: Rewriting Resume ---")
    original = state['original_content']
    plan = state['optimization_plan']
    requirements = state.get('user_requirements', '')
    template = state.get('template_content', '')

    if not template:
        print("No template provided, using default template.")
        template = DEFAULT_RESUME_TEMPLATE
    
    if not original:
        return {"optimized_content": "Cannot rewrite empty resume."}

    llm = build_llm()
    
    system_prompt = (
        "你是一个专业的简历写手。请根据原始简历和修改计划，重写一份高质量的简历。\n"
        "你需要严格遵循给定的【简历模板】的格式、结构和标题进行撰写。\n"
        "要求：\n1. 使用Markdown格式。\n2. 内容要专业、精炼。\n3. 突出候选人的优势。\n4. 填充模板中的内容，保留模板的章节结构。"
    )
    if requirements:
        system_prompt += f"\n5. 特别注意满足用户的附加要求：{requirements}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "【简历模板】：\n{template}\n\n原始简历：\n{original}\n\n修改计划：\n{plan}")
    ])
    chain = prompt | llm
    response = chain.invoke({"original": original, "plan": plan, "template": template})
    
    print("\n" + "="*20 + " LLM RAW OUTPUT START " + "="*20)
    print(response.content)
    print("="*20 + " LLM RAW OUTPUT END " + "="*20 + "\n")

    return {"optimized_content": response.content}

def action_node(state: AgentState):
    """
    Action Module: Performs the final action (Generating PDF).
    """
    print("--- [Step 5] Action: Generating PDF ---")
    optimized_text = state['optimized_content']
    
    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Simple logic to determine output path
    base_name = os.path.splitext(os.path.basename(state['resume_file_path']))[0]
    output_path = os.path.join(output_dir, f"{base_name}_optimized.pdf")
    
    result = generate_resume_pdf(optimized_text, output_path)
    print(result)
    
    return {"pdf_output_path": output_path}

# -------------------------------------------------------------------------
# 3. Graph Construction (Wiring the Agent)
# -------------------------------------------------------------------------

def build_resume_agent():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("perception", perception_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("action", action_node)
    
    # Define Edges (Linear flow for this demo)
    workflow.set_entry_point("perception")
    workflow.add_edge("perception", "analysis")
    workflow.add_edge("analysis", "planning")
    workflow.add_edge("planning", "execution")
    workflow.add_edge("execution", "action")
    workflow.add_edge("action", END)
    
    return workflow.compile()

# -------------------------------------------------------------------------
# Main Execution
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # Create a dummy resume for testing if not exists
    test_resume_path = "sample_resume.txt"
    if not os.path.exists(test_resume_path):
        with open(test_resume_path, "w", encoding="utf-8") as f:
            f.write("""
            姓名：张三
            电话：13800000000
            邮箱：zhangsan@example.com
            
            教育经历：
            2018-2022 某某大学 计算机专业 本科
            
            工作经历：
            2022-至今 某科技公司 程序员
            负责写代码，修bug。
            用了Python和Java。
            
            技能：
            会编程，会用电脑。
            """)
        print(f"Created sample resume at {test_resume_path}")

    # Initialize Agent
    agent = build_resume_agent()
    
    # Run Agent
    initial_state = {
        "resume_file_path": test_resume_path,
        "user_requirements": "希望强调我的Java后端开发能力，并且语气更正式一些。",
        "messages": []
    }
    
    print("Starting Resume Agent...")
    final_state = agent.invoke(initial_state)
    
    print("\n" + "="*50)
    print("Agent Workflow Completed!")
    print(f"Optimized Resume saved to: {final_state['pdf_output_path']}")
    print("="*50)
