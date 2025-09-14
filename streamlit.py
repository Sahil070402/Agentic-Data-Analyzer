import streamlit as st
import asyncio
import os
import base64
import glob
import zipfile
import uuid
import time
import pandas as pd
from io import BytesIO
from models.openai_model_client import get_model_client
from teams.analyzer_gpt import getDataAnalyzerTeam
from config.docker_utils import getDockerCommandLineExecutor, start_docker_container, stop_docker_container
from agents.query_clarity_agent import create_query_clarity_agent, get_csv_info
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult

# --- Page Configuration ---
st.set_page_config(
    page_title="Agentic Data Analyzer",
    page_icon="📊",
    layout="wide"
)

# --- Helper Functions ---
def get_image_b64(path):
    """Converts an image file to a base64 string."""
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def create_new_chat():
    """Create a new chat session."""
    new_chat_id = str(uuid.uuid4())
    new_chat = {
        "id": new_chat_id,
        "name": f"New Chat",
        "created_at": time.time(),
        "messages": [],
        "team_state": None,
        "suggestions": [],
        "show_suggestions": False,
        "refined_query": "",
        "session_start_time": time.time(),
        "session_files": [],
        "files_before_analysis": set(),
        "uploaded_file_name": None
    }
    return new_chat

def get_chat_display_name(chat):
    """Get display name for chat."""
    if chat.get("uploaded_file_name"):
        return f"📊 {chat['uploaded_file_name']}"
    elif len(chat.get("messages", [])) > 0:
        # Use first user message as chat name (truncated)
        for msg in chat["messages"]:
            if msg["role"] == "user":
                content = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
                return f"💬 {content}"
    return f"💭 {chat['name']}"

def switch_to_chat(chat_id):
    """Switch to a specific chat session."""
    if chat_id in st.session_state.chats:
        chat = st.session_state.chats[chat_id]
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = chat["messages"]
        st.session_state.team_state = chat["team_state"]
        st.session_state.suggestions = chat["suggestions"]
        st.session_state.show_suggestions = chat["show_suggestions"]
        st.session_state.refined_query = chat["refined_query"]
        st.session_state.session_start_time = chat["session_start_time"]
        st.session_state.session_files = chat["session_files"]
        st.session_state.files_before_analysis = chat["files_before_analysis"]

def save_current_chat():
    """Save current chat state."""
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
        chat = st.session_state.chats[st.session_state.current_chat_id]
        chat["messages"] = st.session_state.messages
        chat["team_state"] = st.session_state.team_state
        chat["suggestions"] = st.session_state.suggestions
        chat["show_suggestions"] = st.session_state.show_suggestions
        chat["refined_query"] = st.session_state.refined_query
        chat["session_files"] = st.session_state.session_files
        chat["files_before_analysis"] = st.session_state.files_before_analysis

def get_temp_files_before_analysis(temp_dir):
    """Get list of files in temp directory before analysis."""
    if not os.path.exists(temp_dir):
        return set()
    return set(os.listdir(temp_dir))

def get_session_files(temp_dir, files_before, session_start_time):
    """Get files created during current session."""
    if not os.path.exists(temp_dir):
        return []
    
    current_files = set(os.listdir(temp_dir))
    new_files = current_files - files_before
    
    # Filter files by creation time to ensure they're from current session
    session_files = []
    for file in new_files:
        file_path = os.path.join(temp_dir, file)
        if os.path.isfile(file_path):
            # Check if file was created after session start
            file_creation_time = os.path.getctime(file_path)
            if file_creation_time >= session_start_time:
                session_files.append(file)
    
    return session_files

def create_export_zip(temp_dir, session_files):
    """Create a ZIP file containing session files, converting CSV files to JSON format."""
    if not session_files:
        return None
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_name in session_files:
            file_path = os.path.join(temp_dir, file_name)
            if os.path.exists(file_path):
                # Check if it's a CSV file that should be converted to JSON
                if file_name.endswith('.csv') and not file_name.startswith('tmp_') and not file_name.endswith('_full.csv'):
                    try:
                        # Read CSV and convert to JSON
                        df = pd.read_csv(file_path)
                        json_data = df.to_json(orient='records', indent=2)
                        
                        # Create new filename with .json extension
                        json_filename = file_name.replace('.csv', '.json')
                        
                        # Add JSON data to ZIP
                        zip_file.writestr(json_filename, json_data)
                    except Exception as e:
                        # If conversion fails, include original CSV file
                        zip_file.write(file_path, file_name)
                else:
                    # For non-CSV files (PNG, JSON, etc.), add as-is
                    zip_file.write(file_path, file_name)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def cleanup_session_files(temp_dir, session_files):
    """Delete session files from temp directory."""
    deleted_count = 0
    for file_name in session_files:
        file_path = os.path.join(temp_dir, file_name)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_count += 1
        except Exception as e:
            st.error(f"Could not delete {file_name}: {str(e)}")
    return deleted_count

def cleanup_all_temp_files(temp_dir):
    """Delete ALL files from temp directory (except .gitkeep)."""
    if not os.path.exists(temp_dir):
        return 0
    
    deleted_count = 0
    failed_files = []
    
    for file_name in os.listdir(temp_dir):
        # Skip .gitkeep file to preserve directory structure
        if file_name == '.gitkeep':
            continue
            
        file_path = os.path.join(temp_dir, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_count += 1
            elif os.path.isdir(file_path):
                # Remove directory and its contents
                import shutil
                shutil.rmtree(file_path)
                deleted_count += 1
        except Exception as e:
            failed_files.append(f"{file_name}: {str(e)}")
    
    return deleted_count, failed_files

def display_csv_data_file(file_path, file_name):
    """Display a CSV data file as a scrollable dataframe in chat."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Display file info
        st.markdown(f"### 📄 **{file_name}**")
        
        # Show basic metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Rows", len(df))
        with col2:
            st.metric("📋 Columns", len(df.columns))
        
        # Calculate adaptive height based on data size
        row_height = 35    # Approximate height per row
        header_height = 40 # Header height
        padding = 20       # Extra padding for better appearance
        
        # Calculate the natural height needed for the data
        natural_height = header_height + (len(df) * row_height) + padding
        
        # For small datasets (<=10 rows), use natural height with minimal constraints
        # For larger datasets, use scrollable height with reasonable bounds
        if len(df) <= 10:
            # Small datasets: use natural height, minimum 120px for very small tables
            table_height = max(120, natural_height)
        else:
            # Large datasets: use scrollable height between 200px and 600px
            min_height = 200
            max_height = 600
            table_height = max(min_height, min(natural_height, max_height))
        
        # Display the dataframe with adaptive height
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=False,
            height=table_height
        )
        
        return True
        
    except Exception as e:
        st.error(f"Error displaying CSV file {file_name}: {str(e)}")
        return False

def display_analysis_results_with_data_files(temp_dir, session_files, final_analyzer_message, chat_id):
    """Display analysis results with data files first, then charts, then explain button."""
    
    # Filter session files by type
    session_csv_files = [f for f in session_files if f.endswith('.csv') and not f.startswith('tmp_') and not f.endswith('_full.csv')]
    session_png_files = [f for f in session_files if f.endswith('.png')]
    
    # Create unique analysis ID for this specific analysis
    analysis_id = f"{chat_id}_{len(st.session_state.messages)}"
    
    # Store CSV data and analysis text for persistent access with unique analysis ID
    if session_csv_files:
        # Store CSV data in session state for persistent access with unique key
        csv_data_key = f"csv_data_{analysis_id}"
        st.session_state[csv_data_key] = {}
        
        for csv_file in session_csv_files:
            csv_path = os.path.join(temp_dir, csv_file)
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    st.session_state[csv_data_key][csv_file] = df
                except Exception as e:
                    st.session_state[csv_data_key][csv_file] = f"Error reading file: {str(e)}"
    
    # Store analysis text for persistent access with unique key
    analysis_key = f"analysis_text_{analysis_id}"
    st.session_state[analysis_key] = final_analyzer_message
    
    # 1. Display CSV data files first
    if session_csv_files:
        with st.chat_message("assistant", avatar="📊"):
            st.markdown("## 📋 **Generated Data Files**")
            
            for csv_file in session_csv_files:
                csv_path = os.path.join(temp_dir, csv_file)
                if os.path.exists(csv_path):
                    display_csv_data_file(csv_path, csv_file)
                    st.markdown("---")
        
        # Save CSV data to chat history with special marker for persistent display
        csv_message = {
            "role": "assistant", 
            "content": f"CSV_DATA_DISPLAY:{analysis_id}",
            "message_type": "csv_data"
        }
        st.session_state.messages.append(csv_message)
    
    # 2. Display charts second
    if session_png_files:
        with st.chat_message("assistant", avatar="📈"):
            st.success("📊 **Charts generated successfully!**")
            
            # Create content for chat history (without base64 images)
            image_content_for_chat = "📊 **Charts generated successfully!**\n\n"
            
            for image_file in session_png_files:
                image_path = os.path.join(temp_dir, image_file)
                if os.path.exists(image_path):
                    img_b64 = get_image_b64(image_path)
                    st.image(f"data:image/png;base64,{img_b64}", caption=image_file)
                    
                    # Add image info to chat content (without base64)
                    image_content_for_chat += f"- 📈 **{image_file}** (Chart generated)\n"
            
            # Save image info to chat history (without base64 data)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": image_content_for_chat
            })
    
    # 3. Display explain button last (after both CSV data and charts)
    if session_csv_files or session_png_files:  # Show explain button if we have any results
        with st.chat_message("assistant", avatar="💡"):
            st.info("📖 **Explain Analysis** - Click to view detailed analysis explanation")
        
        explain_message = {
            "role": "assistant", 
            "content": f"EXPLAIN_BUTTON:{analysis_id}",
            "message_type": "explain_button"
        }
        st.session_state.messages.append(explain_message)

def display_csv_preview(uploaded_file):
    """Display a preview of the uploaded CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Display basic info
        st.subheader("📋 Data Preview")
        
        # File info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        
        # Data preview (first 5 rows)
        st.write("**🔍 Sample Data (First 5 rows):**")
        preview_df = df.head(5)
        
        # Display with better formatting
        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True,
            height=200
        )
        
        # Data types info
        with st.expander("📈 Column Details"):
            col_info = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                col_info.append({
                    "Column": col,
                    "Type": dtype,
                    "Null Values": null_count
                })
            
            info_df = pd.DataFrame(col_info)
            st.dataframe(info_df, use_container_width=True, hide_index=True)
        
        return True
        
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return False

# --- Main Application ---
st.title("📊 Agentic Data Analyzer")
st.caption("Your AI-powered data analysis assistant. Upload a CSV, ask a question, and get insights.")

# --- Multi-Chat State Initialization ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    # Create first chat
    first_chat = create_new_chat()
    st.session_state.chats[first_chat["id"]] = first_chat
    st.session_state.current_chat_id = first_chat["id"]

# Initialize current session variables from current chat
if st.session_state.current_chat_id in st.session_state.chats:
    current_chat = st.session_state.chats[st.session_state.current_chat_id]
    if "messages" not in st.session_state:
        st.session_state.messages = current_chat["messages"]
    if "team_state" not in st.session_state:
        st.session_state.team_state = current_chat["team_state"]
    if "suggestions" not in st.session_state:
        st.session_state.suggestions = current_chat["suggestions"]
    if "show_suggestions" not in st.session_state:
        st.session_state.show_suggestions = current_chat["show_suggestions"]
    if "refined_query" not in st.session_state:
        st.session_state.refined_query = current_chat["refined_query"]
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = current_chat["session_start_time"]
    if "session_files" not in st.session_state:
        st.session_state.session_files = current_chat["session_files"]
    if "files_before_analysis" not in st.session_state:
        st.session_state.files_before_analysis = current_chat["files_before_analysis"]

# Legacy compatibility
if "session_id" not in st.session_state:
    st.session_state.session_id = st.session_state.current_chat_id

# --- Chat Management Sidebar ---
with st.sidebar:
    # --- Chat Management Section ---
    st.header("💬 Chats")
    
    # New Chat Button and Chat Selector in one row
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("➕ New Chat", use_container_width=True):
            # Save current chat before creating new one
            save_current_chat()
            # Create new chat
            new_chat = create_new_chat()
            st.session_state.chats[new_chat["id"]] = new_chat
            switch_to_chat(new_chat["id"])
            st.rerun()
    
    with col2:
        # Chat count indicator
        st.caption(f"({len(st.session_state.chats)})")
    
    # Chat Dropdown Selector
    if st.session_state.chats and len(st.session_state.chats) > 1:
        # Sort chats by creation time (newest first)
        sorted_chats = sorted(st.session_state.chats.items(), 
                            key=lambda x: x[1]["created_at"], reverse=True)
        
        # Create options for selectbox
        chat_options = []
        chat_ids = []
        current_index = 0
        
        for i, (chat_id, chat) in enumerate(sorted_chats):
            chat_name = get_chat_display_name(chat)
            chat_options.append(chat_name)
            chat_ids.append(chat_id)
            if chat_id == st.session_state.current_chat_id:
                current_index = i
        
        # Chat selector dropdown
        selected_chat_name = st.selectbox(
            "Select Chat:",
            options=chat_options,
            index=current_index,
            key="chat_selector",
            help="Switch between different chat sessions"
        )
        
        # Handle chat selection change
        if selected_chat_name:
            selected_index = chat_options.index(selected_chat_name)
            selected_chat_id = chat_ids[selected_index]
            
            if selected_chat_id != st.session_state.current_chat_id:
                # Save current chat before switching
                save_current_chat()
                switch_to_chat(selected_chat_id)
                st.rerun()
    
    elif st.session_state.chats:
        # Show current chat name when there's only one chat
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        current_name = get_chat_display_name(current_chat)
        st.info(f"📍 Current: {current_name}")
    
    st.markdown("---")
    
    # --- Setup Section ---
    st.header("📊 Setup")
    
    # Step 1: CSV Upload
    uploaded_file = st.file_uploader("1. Upload your CSV file", type="csv")
    
    # Step 2: CSV Preview (only show if file is uploaded)
    if uploaded_file is not None:
        # Update current chat with uploaded file name
        if st.session_state.current_chat_id in st.session_state.chats:
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            if current_chat.get("uploaded_file_name") != uploaded_file.name:
                current_chat["uploaded_file_name"] = uploaded_file.name
                # Update chat name if it's still default
                if current_chat["name"] == "New Chat":
                    current_chat["name"] = f"Analysis: {uploaded_file.name}"
        
        # Display CSV preview in sidebar
        st.markdown("---")
        display_csv_preview(uploaded_file)
        
        # Step 3: Query Input (only show after CSV is uploaded and previewed)
        st.markdown("---")
        user_question = st.text_area(
            "2. Ask a question about your data", 
            height=100,
            help="Enter your data analysis question here. You can write longer, more detailed queries."
        )
        analyze_button = st.button("Analyze Data")
    else:
        # Initialize empty variables when no file is uploaded
        user_question = ""
        analyze_button = False
    
    # Generate Suggestions button (only show if CSV and query are available)
    if uploaded_file is not None and user_question:
        generate_suggestions_button = st.button("💡 Generate Query Suggestions")
        
        # Handle Generate Suggestions button click
        if generate_suggestions_button:
            # Save uploaded file to temp directory for processing
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Generate suggestions
            async def generate_suggestions():
                try:
                    openai_model_client = get_model_client()
                    clarity_agent = create_query_clarity_agent(openai_model_client)
                    
                    # Get CSV information
                    csv_info = get_csv_info(file_path)
                    
                    # Generate suggestions
                    suggestions_result = await clarity_agent.generate_query_suggestions(user_question, csv_info)
                    
                    if "error" not in suggestions_result and suggestions_result.get("suggestions"):
                        st.session_state.suggestions = suggestions_result["suggestions"]
                        st.session_state.show_suggestions = True
                        st.rerun()
                    else:
                        st.error("Unable to generate suggestions. Please try again.")
                except Exception as e:
                    st.error(f"Error generating suggestions: {str(e)}")
            
            # Run suggestion generation
            asyncio.run(generate_suggestions())
    
    # --- Suggestions Panel (in sidebar) ---
    if st.session_state.show_suggestions and st.session_state.suggestions:
        st.markdown("---")
        st.subheader("💡 Query Suggestions")
        st.write("**Here are some related query suggestions:**")
        
        for i, suggestion in enumerate(st.session_state.suggestions, 1):
            if st.button(f"{suggestion}", key=f"suggestion_{i}", use_container_width=True):
                # When user clicks a suggestion, use it as the new query
                st.session_state.refined_query = suggestion
                st.session_state.show_suggestions = False
                st.rerun()
        
        # Clear suggestions button
        if st.button("❌ Clear Suggestions"):
            st.session_state.show_suggestions = False
            st.session_state.suggestions = []
            st.rerun()
    
    # --- Export Panel (in sidebar) ---
    # Show export panel only if there are session-specific files
    if st.session_state.session_files:
        # Filter session files by type
        session_png_files = [f for f in st.session_state.session_files if f.endswith('.png')]
        session_csv_files = [f for f in st.session_state.session_files if f.endswith('.csv') and not f.startswith('tmp_') and not f.endswith('_full.csv')]
        session_json_files = [f for f in st.session_state.session_files if f.endswith('.json') and not f.startswith('tmp_')]
        
        st.markdown("---")
        st.subheader("📥 Export Analysis Results")
        
        # Show current session indicator
        st.caption(f"🎯 Current chat session files only")
        
        # Show available files from current session
        st.write("**Files created in this chat:**")
        
        if session_png_files:
            st.write("📊 **Charts:**")
            for png_file in session_png_files:
                st.write(f"• {png_file}")
        
        if session_csv_files:
            st.write("📄 **Data Files:**")
            for csv_file in session_csv_files:
                st.write(f"• {csv_file}")
        
        if session_json_files:
            st.write("🔧 **JSON Files:**")
            for json_file in session_json_files:
                st.write(f"• {json_file}")
        
        # Single download button for all session files
        temp_dir = "temp"
        if st.session_state.session_files:
            zip_data = create_export_zip(temp_dir, st.session_state.session_files)
            if zip_data:
                st.download_button(
                    label="📥 Download Analysis Results",
                    data=zip_data,
                    file_name=f"chat_analysis_{st.session_state.session_id[:8]}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    help="Download all files created in this chat session"
                )
                
                # Cleanup button to delete ALL files from temp directory
                if st.button("🗑️ Clean Up Files", use_container_width=True, help="Delete ALL files from temp directory to keep it clean"):
                    deleted_count, failed_files = cleanup_all_temp_files(temp_dir)
                    if deleted_count > 0:
                        st.success(f"✅ Cleaned up {deleted_count} files from temp directory")
                        if failed_files:
                            st.warning(f"⚠️ Could not delete {len(failed_files)} files:")
                            for failed_file in failed_files[:3]:  # Show first 3 failed files
                                st.write(f"• {failed_file}")
                            if len(failed_files) > 3:
                                st.write(f"• ... and {len(failed_files) - 3} more")
                        st.session_state.session_files = []  # Clear the session files list
                        st.rerun()  # Refresh to hide the export panel
                    else:
                        st.warning("No files were deleted - temp directory might be empty")

# --- Main Chat Interface (full width) ---
st.header("💬 Analysis Chat")

# --- Chat Display ---
for i, message in enumerate(st.session_state.messages):
    message_content = message["content"]
    message_type = message.get("message_type", "normal")
    
    # Handle special message types
    if message_type == "csv_data":
        # Display CSV data from session state
        chat_id = message_content.replace("CSV_DATA_DISPLAY:", "")
        csv_data_key = f"csv_data_{chat_id}"
        
        if csv_data_key in st.session_state and st.session_state[csv_data_key]:
            with st.chat_message("assistant", avatar="📊"):
                st.markdown("## 📋 **Generated Data Files**")
                
                for csv_file, csv_data in st.session_state[csv_data_key].items():
                    if isinstance(csv_data, pd.DataFrame):
                        # Display file info
                        st.markdown(f"### 📄 **{csv_file}**")
                        
                        # Show basic metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("📊 Rows", len(csv_data))
                        with col2:
                            st.metric("📋 Columns", len(csv_data.columns))
                        
                        # Calculate adaptive height based on data size
                        row_height = 35    # Approximate height per row
                        header_height = 40 # Header height
                        padding = 20       # Extra padding for better appearance
                        
                        # Calculate the natural height needed for the data
                        natural_height = header_height + (len(csv_data) * row_height) + padding
                        
                        # For small datasets (<=10 rows), use natural height with minimal constraints
                        # For larger datasets, use scrollable height with reasonable bounds
                        if len(csv_data) <= 10:
                            # Small datasets: use natural height, minimum 120px for very small tables
                            table_height = max(120, natural_height)
                        else:
                            # Large datasets: use scrollable height between 200px and 600px
                            min_height = 200
                            max_height = 600
                            table_height = max(min_height, min(natural_height, max_height))
                        
                        # Display the dataframe with adaptive height
                        st.dataframe(
                            csv_data,
                            use_container_width=True,
                            hide_index=False,
                            height=table_height
                        )
                        st.markdown("---")
                    else:
                        st.error(f"Error with {csv_file}: {csv_data}")
    
    elif message_type == "explain_button":
        # Display explain button with functionality
        chat_id = message_content.replace("EXPLAIN_BUTTON:", "")
        analysis_key = f"analysis_text_{chat_id}"
        
        with st.chat_message("assistant", avatar="💡"):
            st.info("📖 **Explain Analysis** - Click to view detailed analysis explanation")
            
            # Create unique button key for this message
            button_key = f"explain_btn_{chat_id}_{i}"
            
            if st.button("📖 Explain Analysis", key=button_key, use_container_width=True):
                # Display the detailed analysis
                if analysis_key in st.session_state and st.session_state[analysis_key]:
                    with st.chat_message("assistant", avatar="🔍"):
                        st.markdown("## 📖 **Detailed Analysis Explanation**")
                        st.markdown(st.session_state[analysis_key])
                else:
                    st.error("Analysis explanation not available.")
    
    else:
        # Handle normal messages
        with st.chat_message(message["role"]):
            # Check if this is an image content message and try to display images
            if "Charts generated successfully!" in message_content and message["role"] == "assistant":
                st.markdown(message_content)
                
                # Extract image file names from the message content instead of scanning temp directory
                # This prevents showing all images from temp directory
                lines = message_content.split('\n')
                for line in lines:
                    if line.strip().startswith('- 📈 **') and line.strip().endswith('** (Chart generated)'):
                        # Extract filename from the line format: "- 📈 **filename.png** (Chart generated)"
                        start_idx = line.find('**') + 2
                        end_idx = line.rfind('**')
                        if start_idx < end_idx:
                            png_file = line[start_idx:end_idx]
                            temp_dir = "temp"
                            png_path = os.path.join(temp_dir, png_file)
                            if os.path.exists(png_path):
                                try:
                                    img_b64 = get_image_b64(png_path)
                                    st.image(f"data:image/png;base64,{img_b64}", caption=png_file)
                                except Exception as e:
                                    st.caption(f"📈 {png_file} (Image file exists but cannot be displayed)")
            else:
                st.markdown(message_content)

# --- Handle Refined Query from Suggestions ---
if st.session_state.refined_query and uploaded_file is not None:
    # Use the refined query instead of the original
    user_question = st.session_state.refined_query
    st.session_state.refined_query = ""  # Clear it after use
    
    # Save uploaded file to the temp directory
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Record files before analysis
    st.session_state.files_before_analysis = get_temp_files_before_analysis(temp_dir)
    
    # Add refined question to chat
    st.session_state.messages.append({"role": "user", "content": f"**Refined Query:** {user_question}"})
    with st.chat_message("user"):
        st.markdown(f"**Refined Query:** {user_question}")
    
    # Clear suggestions and proceed directly to analysis (refined queries are assumed to be clear)
    st.session_state.show_suggestions = False
    
    with st.chat_message("assistant", avatar="✅"):
        st.success("**Using refined query - proceeding with analysis.**")
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "**Using refined query - proceeding with analysis.**"
    })

    # Run the AutoGen team directly
    async def run_analysis():
        # Initialize components
        docker = getDockerCommandLineExecutor()
        openai_model_client = get_model_client()
        team = getDataAnalyzerTeam(docker, openai_model_client)

        # Load previous state if it exists
        if st.session_state.team_state:
            await team.load_state(st.session_state.team_state)

        # Get CSV info to provide column context
        csv_info = get_csv_info(file_path)
        column_info = f"CSV COLUMNS: {csv_info['columns']}\nSAMPLE DATA:\n{csv_info['sample_data']}\n\n"
        full_task = f"{column_info}Using the data from '{uploaded_file.name}', {user_question}"

        try:
            await start_docker_container(docker)

            # Progress tracking variables
            progress_placeholder = st.empty()
            progress_steps = [
                "🔄 Initializing analysis...",
                "📊 Data Analyzer is planning the approach...",
                "🐍 Executing Python code...",
                "📈 Processing results...",
                "✅ Analysis complete!"
            ]
            current_step = 0
            
            # Show initial progress
            with progress_placeholder.container():
                st.info(progress_steps[current_step])
            
            # Track messages for final analysis
            final_analyzer_message = None
            
            async for message in team.run_stream(task=full_task):
                if isinstance(message, TextMessage) and message.source != "user":
                    agent_name = message.source
                    
                    # Update progress based on agent activity
                    if agent_name == "Data_Analyzer_agent":
                        current_step = min(current_step + 1, len(progress_steps) - 2)
                        # Clean the analyzer message by removing "STOP" and extra whitespace
                        cleaned_content = message.content.replace("STOP", "").strip()
                        final_analyzer_message = cleaned_content  # Keep updating with latest analyzer message
                    elif agent_name == "Python_Code_Executor":
                        current_step = min(current_step + 1, len(progress_steps) - 2)
                    
                    # Update progress display
                    if current_step < len(progress_steps) - 1:
                        with progress_placeholder.container():
                            st.info(progress_steps[current_step])

                elif isinstance(message, TaskResult):
                    if message.stop_reason:
                        # Show final progress
                        current_step = len(progress_steps) - 1
                        with progress_placeholder.container():
                            st.success(progress_steps[current_step])
                        
                        # Display the final detailed analysis using new format
                        if final_analyzer_message:
                            # Get session-specific files
                            session_files = get_session_files(temp_dir, st.session_state.files_before_analysis, st.session_state.session_start_time)
                            st.session_state.session_files = session_files
                            
                            # Use new display function that shows CSV data first, then explain button
                            display_analysis_results_with_data_files(temp_dir, session_files, final_analyzer_message, st.session_state.current_chat_id)
                        
                        # Add completion message
                        with st.chat_message("assistant"):
                            st.success("✅ **Analysis completed successfully!**")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "✅ **Analysis completed successfully!**"
                        })

            # Save the state after the run
            st.session_state.team_state = await team.save_state()
            
            # Force UI refresh to show export panel immediately
            if session_files:
                st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            await stop_docker_container(docker)

    # Run the async function
    asyncio.run(run_analysis())

# --- Core Logic ---
elif analyze_button and uploaded_file is not None and user_question:
    # 1. Save uploaded file to the temp directory
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Record files before analysis
    st.session_state.files_before_analysis = get_temp_files_before_analysis(temp_dir)
    
    st.info(f"File '{uploaded_file.name}' uploaded successfully.")

    # Add user question to chat
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Clear any existing suggestions since user chose to proceed directly
    st.session_state.show_suggestions = False
    
    with st.chat_message("assistant", avatar="✅"):
        st.success("**Proceeding with analysis using your query.**")
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "**Proceeding with analysis using your query.**"
    })

    # Run the AutoGen team directly (no query clarity check)
    async def run_analysis():
        # Initialize components
        docker = getDockerCommandLineExecutor()
        openai_model_client = get_model_client()
        team = getDataAnalyzerTeam(docker, openai_model_client)

        # Load previous state if it exists
        if st.session_state.team_state:
            await team.load_state(st.session_state.team_state)

        # Get CSV info to provide column context
        csv_info = get_csv_info(file_path)
        column_info = f"CSV COLUMNS: {csv_info['columns']}\nSAMPLE DATA:\n{csv_info['sample_data']}\n\n"
        full_task = f"{column_info}Using the data from '{uploaded_file.name}', {user_question}"

        try:
            await start_docker_container(docker)

            # Progress tracking variables
            progress_placeholder = st.empty()
            progress_steps = [
                "🔄 Initializing analysis...",
                "📊 Data Analyzer is planning the approach...",
                "🐍 Executing Python code...",
                "📈 Processing results...",
                "✅ Analysis complete!"
            ]
            current_step = 0
            
            # Show initial progress
            with progress_placeholder.container():
                st.info(progress_steps[current_step])
            
            # Track messages for final analysis
            final_analyzer_message = None
            
            async for message in team.run_stream(task=full_task):
                if isinstance(message, TextMessage) and message.source != "user":
                    agent_name = message.source
                    
                    # Update progress based on agent activity
                    if agent_name == "Data_Analyzer_agent":
                        current_step = min(current_step + 1, len(progress_steps) - 2)
                        # Clean the analyzer message by removing "STOP" and extra whitespace
                        cleaned_content = message.content.replace("STOP", "").strip()
                        final_analyzer_message = cleaned_content  # Keep updating with latest analyzer message
                    elif agent_name == "Python_Code_Executor":
                        current_step = min(current_step + 1, len(progress_steps) - 2)
                    
                    # Update progress display
                    if current_step < len(progress_steps) - 1:
                        with progress_placeholder.container():
                            st.info(progress_steps[current_step])

                elif isinstance(message, TaskResult):
                    if message.stop_reason:
                        # Show final progress
                        current_step = len(progress_steps) - 1
                        with progress_placeholder.container():
                            st.success(progress_steps[current_step])
                        
                        # Display the final detailed analysis using new format
                        if final_analyzer_message:
                            # Get session-specific files
                            session_files = get_session_files(temp_dir, st.session_state.files_before_analysis, st.session_state.session_start_time)
                            st.session_state.session_files = session_files
                            
                            # Use new display function that shows CSV data first, then explain button
                            display_analysis_results_with_data_files(temp_dir, session_files, final_analyzer_message, st.session_state.current_chat_id)
                        
                        # Add completion message
                        with st.chat_message("assistant"):
                            st.success("✅ **Analysis completed successfully!**")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "✅ **Analysis completed successfully!**"
                        })

            # Save the state after the run
            st.session_state.team_state = await team.save_state()
            
            # Force UI refresh to show export panel immediately
            if session_files:
                st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            await stop_docker_container(docker)

    # Run the async function
    asyncio.run(run_analysis())

elif analyze_button:
    st.warning("Please upload a CSV file and enter a question.")