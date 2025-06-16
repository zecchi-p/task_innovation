import streamlit as st
import json
import os
import time
import random

# Set the data file path to a location in Google Drive
DATA_FILE = '/content/drive/MyDrive/task_app_data/tasks.json'

def load_tasks():
    """Loads tasks from the JSON data file."""
    if not os.path.exists(DATA_FILE):
        # Ensure the directory exists before saving
        data_dir = os.path.dirname(DATA_FILE)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True) # Use exist_ok=True to avoid error if directory already exists
        # Initialize with some sample tasks if the file doesn't exist
        initial_tasks = {
            '1': {'id': '1', 'name': 'デザイン検討', 'area': 'アイデア', 'creator': 'system', 'chat': [{'sender': 'system', 'message': '最初のデザイン案について話しましょう。'}]},
            '2': {'id': '2', 'name': '機能実装', 'area': '進行中', 'creator': 'system', 'chat': []},
            '3': {'id': '3', 'name': '最終チェック', 'area': '決定', 'creator': 'system', 'chat': []}
        }
        save_tasks(initial_tasks)
        return initial_tasks
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if JSON is invalid
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return {}


def save_tasks(tasks):
    """Saves tasks to the JSON data file."""
    # Ensure the directory exists before saving
    data_dir = os.path.dirname(DATA_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)

def add_task(task_name, area, creator):
    """Adds a new task to the tasks data."""
    tasks = load_tasks()
    # Generate a unique ID based on current timestamp and a small random number
    task_id = str(int(time.time() * 1000) + random.randint(0, 999))
    new_task = {
        'id': task_id,
        'name': task_name,
        'area': area,
        'creator': creator,
        'chat': []
    }
    tasks[task_id] = new_task
    save_tasks(tasks)
    return new_task

def update_task(task_id, **kwargs):
    """Updates an existing task."""
    tasks = load_tasks()
    if task_id in tasks:
        tasks[task_id].update(kwargs)
        save_tasks(tasks)
        return tasks[task_id]
    return None

def add_chat_message(task_id, sender, message):
    """Adds a chat message to a task."""
    tasks = load_tasks()
    if task_id in tasks:
        # Ensure the chat key exists
        if 'chat' not in tasks[task_id]:
            tasks[task_id]['chat'] = []
        tasks[task_id]['chat'].append({'sender': sender, 'message': message})
        save_tasks(tasks)
        return tasks[task_id]
    return None


# --- Simple Login Simulation ---
# This is a placeholder login. In a real app, you'd handle authentication properly.
# Using session state to keep track of logged-in user.
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

# Initialize session state for single-page navigation and task selection
if 'page' not in st.session_state:
    st.session_state['page'] = 'main' # 'main' or 'chat'

if 'current_task_id' not in st.session_state:
    st.session_state['current_task_id'] = None

# Initialize session state for chat input value for each task
# This helps in clearing the input box after sending a message
if 'chat_input_values' not in st.session_state:
    st.session_state['chat_input_values'] = {}

st.set_page_config(layout="wide")
st.title("タスク管理アプリ")

# Basic login form if no user is logged in
if st.session_state['logged_in_user'] is None:
    st.sidebar.header("ログイン")
    username_input = st.sidebar.text_input("ユーザー名", key="login_username")
    # In a real app, you'd have a password field and verify credentials
    if st.sidebar.button("ログイン", key="login_button"):
        if username_input:
            st.session_state['logged_in_user'] = username_input
            st.sidebar.success(f"{username_input} としてログインしました！")
            st.rerun() # Rerun to show the app content
        else:
            st.sidebar.warning("ユーザー名を入力してください。")
    st.stop() # Stop execution until user logs in

# Display logged-in user and logout button
st.sidebar.write(f"ログイン中: **{st.session_state['logged_in_user']}**")
if st.sidebar.button("ログアウト", key="logout_button"):
    st.session_state['logged_in_user'] = None
    # Clear other relevant session state variables on logout
    if 'page' in st.session_state:
        del st.session_state['page']
    if 'current_task_id' in st.session_state:
        del st.session_state['current_task_id']
    if 'clicked_task_id' in st.session_state:
        del st.session_state['clicked_task_id']
    if 'chat_input_values' in st.session_state:
        del st.session_state['chat_input_values'] # Clear chat input values on logout
    st.rerun()


# --- Single Page Application Logic ---

if st.session_state['page'] == 'main':
    st.header("タスク一覧")

    # --- Task Creation Form ---
    st.subheader("新しいタスクを作成")
    # Use columns for a slightly better layout for the form elements
    form_col1, form_col2 = st.columns([2, 1])
    with st.form("new_task_form", clear_on_submit=True):
        with form_col1:
            task_name = st.text_input("タスク名", key="task_name_input")
        with form_col2:
             area = st.selectbox("初期エリア", ["アイデア", "進行中", "決定", "完了"], key="area_select")

        submitted = st.form_submit_button("タスクを作成")
        if submitted:
            if task_name:
                creator = st.session_state.get('logged_in_user', 'ゲスト')
                add_task(task_name, area, creator)
                st.success("タスクが作成されました！")
                st.rerun() # Rerun to show the new task
            else:
                st.warning("タスク名を入力してください。")

    st.markdown("---") # Separator

    # --- Task Display Areas ---
    st.subheader("タスクボード")

    tasks = load_tasks()

    # Filter tasks by area, excluding '完了' for the main board
    idea_tasks = {k: v for k, v in tasks.items() if v['area'] == 'アイデア'}
    in_progress_tasks = {k: v for k, v in tasks.items() if v['area'] == '進行中'}
    decided_tasks = {k: v for k, v in tasks.items() if v['area'] == '決定'}
    completed_tasks = {k: v for k, v in tasks.items() if v['area'] == '完了'} # Also get completed tasks for the completed view

    # Define CSS for task bubbles and chat messages
    custom_css = """
    <style>
    /* Improve column spacing */
    div.st-emotion-cache-1r6encode { /* Target Streamlit's column divs by class */
        padding-right: 1rem; /* Add padding between columns */
    }
    div.st-emotion-cache-1r6encode:last-child {
         padding-right: 0; /* Remove padding from the last column */
    }

    /* Style for the buttons simulating bubbles */
    .stButton > button {
        background-color: #e6f3ff; /* Light blue background */
        border-radius: 20px; /* Rounded corners */
        padding: 10px 15px; /* Padding inside the bubble */
        margin: 5px 0; /* Space between bubbles */
        border: 1px solid #b3d9ff; /* Light blue border */
        width: 100%; /* Make buttons take full column width */
        text-align: left; /* Align text to the left */
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Subtle shadow */
        color: #333; /* Darken text color */
        font-weight: bold; /* Bold text */
    }
    .stButton > button:hover {
        background-color: #cce5ff; /* Slightly darker blue on hover */
        border-color: #99c2ff; /* Darker border on hover */
        color: #000; /* Even darker text on hover */
    }
    .stButton > button:active {
        background-color: #b3d9ff; /* Even darker blue when active */
        border-color: #66a3ff; /* Darkest border when active */
    }

    /* Improve chat message display */
    .chat-message {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 10px;
        max-width: 80%; /* Limit message width */
        word-wrap: break-word; /* Break long words */
    }
    .chat-message.user {
        background-color: #dcf8c6; /* Light green for user messages */
        margin-left: auto; /* Align user messages to the right */
        text-align: left; /* Align text to the left */
    }
     .chat-message.system {
        background-color: #e6e6ea; /* Light grey for system messages */
        margin-right: auto; /* Align system messages to the left */
        text-align: left; /* Align text to the left */
    }
    .chat-message strong {
        display: block; /* Put sender name on a new line */
        margin-bottom: 2px;
        font-size: 0.9em;
    }

    /* Ensure the chat container has a scrollbar */
    .st-emotion-cache-1kyxreq /* Target the scrollable container class */ {
        overflow-y: auto;
    }

    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    # Display tasks in columns for main areas
    col1, col2, col3 = st.columns(3)

    def display_tasks_in_area(area_name, tasks_dict, column):
        with column:
            st.header(area_name)
            if tasks_dict:
                # Sort tasks by creation time (approximate using ID) for consistency
                sorted_tasks = sorted(tasks_dict.items(), key=lambda item: item[0])
                for task_id, task in sorted_tasks:
                    # Use a Streamlit button to represent the task bubble and handle clicks
                    # Add a unique key for each button
                    if st.button(task['name'], key=f"{area_name}_{task_id}", help=f"クリックしてチャットを開く"):
                         st.session_state['current_task_id'] = task_id
                         st.session_state['page'] = 'chat' # Change page state to 'chat'
                         # Initialize chat input value for this task if not exists
                         if task_id not in st.session_state.get('chat_input_values', {}):
                             st.session_state.setdefault('chat_input_values', {})[task_id] = ""
                         st.rerun() # Rerun the app to switch to the chat view


            else:
                st.info(f"{area_name} にタスクはありません。")


    display_tasks_in_area("アイデア", idea_tasks, col1)
    display_tasks_in_area("進行中", in_progress_tasks, col2)
    display_tasks_in_area("決定", decided_tasks, col3)

    st.markdown("---") # Separator

    # --- Completed Tasks Section on the Main Page ---
    st.subheader("完了したタスク")
    if completed_tasks:
        # Sort completed tasks by creation time (approximate using ID)
        sorted_completed_tasks = sorted(completed_tasks.items(), key=lambda item: item[0])
        for task_id, task in sorted_completed_tasks:
            # Display completed tasks as expandable sections
             with st.expander(f"完了: {task['name']}"):
                 st.write(f"作成者: {task['creator']}")
                 # Optional: Display chat or other details here if needed
                 if task.get('chat'):
                      st.write("チャット履歴:")
                      # Use a small container for chat history within the expander if needed
                      # chat_history_container = st.container(height=150) # Optional: fixed height
                      for msg in task['chat']:
                           # Apply custom CSS class for chat messages
                           sender_class = "user" if msg['sender'] == st.session_state.get('logged_in_user', 'ゲスト') else "system"
                           st.markdown(f"<div class='chat-message {sender_class}'><strong>{msg['sender']}</strong>{msg['message']}</div>", unsafe_allow_html=True)
                 else:
                      st.info("このタスクにはチャット履歴がありません。")
                 # Optional: Add a button to view full chat for completed tasks if needed
                 # if st.button(f"チャットを開く (タask_id: {task_id})", key=f"completed_chat_{task_id}"):
                 #      st.session_state['current_task_id'] = task_id
                 #      st.session_state['page'] = 'chat'
                 #      st.rerun()

    else:
        st.info("完了したタスクはありません。")


elif st.session_state['page'] == 'chat':
    # --- Chat Page Content ---
    st.title("タスクチャット")

    # Add a button to go back to the main task view at the top
    if st.button("← タスクボードに戻る", key="back_to_main_top"):
        st.session_state['page'] = 'main'
        st.session_state['current_task_id'] = None # Clear the current task ID
        st.rerun()

    current_task_id = st.session_state.get('current_task_id')

    if not current_task_id:
        st.warning("表示するタスクが選択されていません。タスクボードに戻ってください。")
        # The back button is already displayed at the top, no need for another one here
        # if st.button("タスクボードに戻る"):
        #     st.session_state['page'] = 'main'
        #     st.rerun()
        # return
    else:
        # Load all tasks and find the current task
        tasks = load_tasks()
        current_task = tasks.get(current_task_id)

        if not current_task:
            st.error(f"タスクID {current_task_id} が見つかりません。")
            # The back button is already displayed at the top, no need for another one here
            # if st.button("タスクボードに戻る"):
            #     st.session_state['page'] = 'main'
            #     st.rerun()
            # return
        else:
            st.subheader(f"タスク: {current_task['name']}")

            # --- Task Area Change UI ---
            st.write(f"現在のエリア: **{current_task['area']}**")
            # Use a unique key for the selectbox based on task ID
            new_area = st.selectbox(
                "エリアを変更",
                ["アイデア", "進行中", "決定", "完了"],
                index=["アイデア", "進行中", "決定", "完了"].index(current_task['area']),
                key=f"area_selectbox_{current_task_id}"
            )
            # Add a button to apply the area change
            if st.button("エリアを更新", key=f"update_area_button_{current_task_id}"):
                 update_task(current_task_id, area=new_area)
                 st.success(f"タスクのエリアを '{new_area}' に更新しました！")
                 # Rerun to reflect the change (will stay on chat page unless area becomes '完了')
                 st.rerun()

            st.markdown("---") # Separator

            # Display chat messages
            st.write("チャット履歴:")
            # Use a container with fixed height and scrollbar for chat history
            chat_container = st.container(height=400, border=True)
            if current_task.get('chat'):
                # Display messages in a chat-like format with improved styling
                for i, message in enumerate(current_task['chat']):
                    with chat_container: # Display inside the scrollable container
                        # Apply custom CSS class for chat messages
                        sender_class = "user" if message['sender'] == st.session_state.get('logged_in_user', 'ゲスト') else "system"
                        st.markdown(f"<div class='chat-message {sender_class}'><strong>{message['sender']}</strong>{message['message']}</div>", unsafe_allow_html=True)
            else:
                with chat_container:
                    st.info("まだチャットメッセージはありません。")
            st.write("---") # Separator

            # Input for new message
            # Use a unique key for the input widget itself
            new_message_input_key = f"new_chat_message_input_{current_task_id}"
            # Get the current value from session state, default to empty string
            current_input_value = st.session_state.get('chat_input_values', {}).get(current_task_id, "")

            new_message = st.text_input("新しいメッセージを入力", key=new_message_input_key, value=current_input_value)

            # Handle message sending
            if st.button("送信", key=f"send_message_button_{current_task_id}"):
                if new_message:
                    sender = st.session_state.get('logged_in_user', 'ゲスト')
                    add_chat_message(current_task_id, sender, new_message)
                    # Clear the input box by updating the value in session state
                    st.session_state.setdefault('chat_input_values', {})[current_task_id] = ""
                    st.rerun() # Rerun to display the new message and clear input
                else:
                    st.warning("メッセージを入力してください。")

            st.write("") # Add some space
            # The back button is already displayed at the top, no need for another one here
            # if st.button("タスクボードに戻る", key="back_to_main_bottom"):
            #     st.session_state['page'] = 'main'
            #     st.session_state['current_task_id'] = None # Clear the current task ID
            #     st.rerun()
