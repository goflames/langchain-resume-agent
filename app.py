import streamlit as st
import os
import time
from agent_demo import build_resume_agent

st.set_page_config(page_title="AI 简历优化助手", page_icon="📄")

st.title("📄 AI 简历优化助手")
st.markdown("上传您的简历（PDF/TXT），AI 将为您进行深度分析与优化，并生成全新的 PDF 简历。")

# Sidebar for inputs
with st.sidebar:
    st.header("配置")
    uploaded_file = st.file_uploader("1. 上传简历文件", type=["pdf", "txt", "md"])
    
    st.markdown("---")
    
    template_file = st.file_uploader("2. 上传目标简历模板（可选）", type=["md", "txt"], help="如果不上传，将使用默认的通用简历模板。")
    
    user_requirements = st.text_area(
        "3. 附加要求（可选）",
        placeholder="例如：请强调我的项目管理经验，或者将简历缩减到一页以内...",
        height=150
    )

    if st.button("开始优化", type="primary"):
        st.session_state['start_btn_clicked'] = True
        # Clear previous results to force re-run
        if 'final_state' in st.session_state:
            del st.session_state['final_state']

# Main area
if not uploaded_file and not st.session_state.get('start_btn_clicked', False):
    st.info("👈 请在左侧侧边栏上传简历，并点击“开始优化”")

if st.session_state.get('start_btn_clicked', False):
    if not uploaded_file:
        st.error("请先上传简历文件！")
    else:
        # Save uploaded file temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Only write file if it doesn't exist or we want to overwrite
        # But for simplicity, just write it.
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.info(f"文件已接收：{uploaded_file.name}")
        
        # Handle template file
        template_content = ""
        if template_file:
            try:
                # Assuming text/markdown template
                template_content = template_file.getvalue().decode("utf-8")
                st.info(f"已加载自定义模板：{template_file.name}")
            except Exception as e:
                st.warning(f"模板文件读取失败，将使用默认模板。错误：{e}")

        # Check if we already have results
        if 'final_state' in st.session_state:
            final_state = st.session_state['final_state']
            
            # Show completion status immediately
            st.success("简历优化成功！（已加载缓存结果）")
            
            pdf_path = final_state.get("pdf_output_path")
            optimized_content = final_state.get("optimized_content")
            analysis_report = final_state.get("analysis_report")
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 分析报告")
                with st.expander("点击查看详细分析", expanded=False):
                    st.markdown(analysis_report)
                    
            with col2:
                st.subheader("📝 优化后内容预览")
                with st.expander("点击查看内容", expanded=False):
                    st.markdown(optimized_content)
            
            st.divider()
            
            # Download Button
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    
                st.download_button(
                    label="📥 下载优化后的 PDF 简历",
                    data=pdf_bytes,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    key="download_btn"
                )
            else:
                st.error("PDF 生成失败，请检查日志。")

        else:
            try:
                # Build Agent
                agent = build_resume_agent()
                
                # Prepare state
                initial_state = {
                    "resume_file_path": file_path,
                    "user_requirements": user_requirements,
                    "template_content": template_content,
                    "messages": []
                }
                
                # Initialize final_state
                final_state = initial_state.copy()

                # Run Agent with streaming status
                with st.status("🚀 AI Agent 启动中...", expanded=True) as status:
                    st.write("⚙️ 初始化系统资源...")
                    
                    for step_output in agent.stream(initial_state):
                        for node_name, node_state in step_output.items():
                            # Update final_state with new data from this node
                            final_state.update(node_state)
                            
                            if node_name == "perception":
                                st.write("👀 **[感知]** 已读取并解析简历文件")
                                status.update(label="正在进行深度分析...", state="running")
                                
                            elif node_name == "analysis":
                                st.write("🧠 **[分析]** 完成简历诊断与评估")
                                # Show a snippet of analysis
                                if "analysis_report" in node_state:
                                    with st.expander("查看分析摘要"):
                                        st.markdown(node_state["analysis_report"][:500] + "...")
                                status.update(label="正在制定优化策略...", state="running")
                                
                            elif node_name == "planning":
                                st.write("📝 **[规划]** 已生成针对性优化方案")
                                if "optimization_plan" in node_state:
                                    with st.expander("查看优化策略"):
                                        st.markdown(node_state["optimization_plan"])
                                status.update(label="正在重写并应用模板...", state="running")
                                
                            elif node_name == "execution":
                                template_used = "自定义模板" if initial_state.get("template_content") else "默认通用模板"
                                st.write(f"✍️ **[执行]** 已选用 **{template_used}**，简历内容重写完成")
                                status.update(label="正在生成 PDF 文件...", state="running")
                                
                            elif node_name == "action":
                                st.write("📄 **[生成]** PDF 简历生成完毕")
                    
                    status.update(label="🎉 简历优化完成！", state="complete", expanded=False)
                
                # Save result to session state
                st.session_state['final_state'] = final_state
                
                pdf_path = final_state.get("pdf_output_path")
                optimized_content = final_state.get("optimized_content")
                analysis_report = final_state.get("analysis_report")
                
                st.success("简历优化成功！")
                
                # Rerun to show results using the "cached" branch logic to avoid code duplication?
                # Or just duplicate display logic for now to keep it simple and explicit.
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 分析报告")
                    with st.expander("点击查看详细分析", expanded=False):
                        st.markdown(analysis_report)
                        
                with col2:
                    st.subheader("📝 优化后内容预览")
                    with st.expander("点击查看内容", expanded=False):
                        st.markdown(optimized_content)
                
                st.divider()
                
                # Download Button
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        
                    st.download_button(
                        label="📥 下载优化后的 PDF 简历",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        key="download_btn"
                    )
                else:
                    st.error("PDF 生成失败，请检查日志。")
                    
            except Exception as e:
                st.error(f"发生错误：{str(e)}")
            finally:
                pass
