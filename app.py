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
    uploaded_file = st.file_uploader("上传简历文件", type=["pdf", "txt", "md"])
    user_requirements = st.text_area(
        "附加要求（可选）",
        placeholder="例如：请强调我的项目管理经验，或者将简历缩减到一页以内...",
        height=150
    )
    start_btn = st.button("开始优化", type="primary")

# Main area
if start_btn:
    if not uploaded_file:
        st.error("请先上传简历文件！")
    else:
        # Save uploaded file temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.info(f"文件已接收：{uploaded_file.name}")
        
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Build Agent
            agent = build_resume_agent()
            
            # Prepare state
            initial_state = {
                "resume_file_path": file_path,
                "user_requirements": user_requirements,
                "messages": []
            }
            
            # Run Agent
            status_text.text("正在启动 Agent...")
            progress_bar.progress(10)
            
            # Since invoke is blocking, we can't easily show real-time progress for each node 
            # unless we use streaming or callbacks. For this demo, we'll just simulate/wait.
            # Or better, we can manually print steps if we break down the invoke, 
            # but standard .invoke() is easiest.
            
            status_text.text("AI 正在深度阅读、分析与重写您的简历，请稍候...")
            progress_bar.progress(30)
            
            final_state = agent.invoke(initial_state)
            
            progress_bar.progress(90)
            status_text.text("正在生成最终 PDF...")
            
            pdf_path = final_state.get("pdf_output_path")
            optimized_content = final_state.get("optimized_content")
            analysis_report = final_state.get("analysis_report")
            
            progress_bar.progress(100)
            status_text.text("完成！")
            
            st.success("简历优化成功！")
            
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
                    mime="application/pdf"
                )
            else:
                st.error("PDF 生成失败，请检查日志。")
                
        except Exception as e:
            st.error(f"发生错误：{str(e)}")
        finally:
            # Cleanup temp file (optional)
            # if os.path.exists(file_path):
            #     os.remove(file_path)
            pass
else:
    if not uploaded_file:
        st.info("👈 请在左侧上传简历并点击“开始优化”")
