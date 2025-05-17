import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import process, fuzz
import re
import concurrent.futures

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# --------- CODE CLEANER ------------ #
def extract_executable_code(llm_output: str) -> str:
    """
    Extract only executable Python code from LLM output.
    Removes imports, markdown fences, and explanations.
    """
    code = re.sub(r"```(\w+)?", "", llm_output)     # Remove markdown code fences
    code = re.sub(r"```", "", code)
    code_lines = []
    for line in code.splitlines():
        l = line.strip()
        if l.lower().startswith("this code") or l.lower().startswith("the code"):         # Stop at explanations
            break
        if not l:         # Skip blank lines
            continue
        if l.startswith("import "):         # Remove imports
            continue
        code_lines.append(line)
    return "\n".join(code_lines)
# ----------------------------------- #

# ------------- SETUP ---------------
st.set_page_config(page_title="Flexible NLProc DataFrame Agent", layout="wide")

@st.cache_resource
def load_llm():
    api_key = st.secrets["GROQ_API_KEY"]  
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.0,
        max_tokens=256,
        timeout=None,
        max_retries=2,
        api_key=api_key
    )
llm = load_llm()

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")
embedder = load_embedder()

# ------------- INTENT/ACTION TEMPLATES ---------------
ACTION_TEMPLATES = [
    "add column",
    "remove column",
    "set cell value",
    "add row",
    "remove row",
    "plot column",
    "plot ratio column by group",
    "calculate ratio between two columns",
    "sum two columns",
    "average of column grouped by another column",
]

ACTION_TEMPLATES_EMB = embedder.encode(ACTION_TEMPLATES)

# ------------- GUARDRAILS ---------------
FORBIDDEN = ['os.', 'sys.', '__', 'open(', 'eval(', 'exec(', 'subprocess', 'shutil', 'exit(']

def is_code_safe(code: str) -> bool:
    """Guardrails: Not exhaustive, but blocks most dangerous code."""
    for pat in FORBIDDEN:
        if pat in code:
            return False
    return True

# ------------- COLUMN MATCHING (fuzzy/embedding) ---------------
def best_column_match(user_token, columns, threshold=0.7):
    if not columns:
        return None
    user_emb = embedder.encode([user_token])
    col_embs = embedder.encode(columns)
    cos = util.cos_sim(user_emb, col_embs)[0]
    max_idx = cos.argmax().item()
    if cos[max_idx] > threshold:
        return columns[max_idx]
    match, score, _ = process.extractOne(user_token, columns, scorer=fuzz.WRatio)
    return match if score > 80 else None

def extract_relevant_columns(user_cmd, columns):
    tokens = re.findall(r'\b\w+\b', user_cmd)
    found = []
    for tok in tokens:
        cand = best_column_match(tok, columns)
        if cand and cand not in found:
            found.append(cand)
    return found

# ------------- INTENT/STRUCTURED MAPPING ---------------
def extract_intent_and_slots(user_cmd, columns):
    cmd_emb = embedder.encode([user_cmd])
    sim = util.cos_sim(cmd_emb, ACTION_TEMPLATES_EMB)[0]
    action_idx = sim.argmax().item()
    best_action = ACTION_TEMPLATES[action_idx]
    op = None
    for o in ["ratio", "sum", "average", "mean", "median"]:
        if o in user_cmd.lower():
            op = o
            break
    plot_type = None
    for p in ["plot", "histogram", "bar", "pie", "line", "box"]:
        if p in user_cmd.lower():
            plot_type = p
            break
    group_by = None
    match = re.search(r"(by|against|grouped by|vs)\s+([\w ]+)", user_cmd.lower())
    if match:
        group_by = best_column_match(match[2].strip(), columns)

    col_list = extract_relevant_columns(user_cmd, columns)
    new_col = None
    m = re.search(r"(?:as|named|call(ed)?|new column named)\s*([\w\d_ ]+)", user_cmd)
    if m:
        new_col = m.group(2).strip()

    return {
        "action": best_action,
        "columns": col_list[:3],  # up to 3
        "operation": op,
        "plot_type": plot_type,
        "new_column": new_col,
        "group_by": group_by,
        "raw": user_cmd
    }

# ------------- LLM CODEGEN WITH TIMEOUT ---------------
def codegen_prompt_from_structured(struct, columns):
    schema = f"DataFrame columns: {columns}\n"

    instruction = f"Action: {struct['action']}; "
    if struct["operation"]:
        instruction += f"Operation: {struct['operation']}; "
    if struct["columns"]:
        instruction += f"Columns: {struct['columns']}; "
    if struct["new_column"]:
        instruction += f"New column: {struct['new_column']}; "
    if struct["plot_type"]:
        instruction += f"Plot: {struct['plot_type']}; "
    if struct["group_by"]:
        instruction += f"Group by: {struct['group_by']}; "
    instruction += (
        "USE MINIMUM NEEDED OPTIMUM CODE"
        "If the user asks for a comparison or a specific value, "
        "If the user mentions a filter then filter DataFrame to that entity before calculating IF NEEDED."
        "If the user asks for a specific task DO NOT HALLUCINATE OR DO EXTRA TASK do the task as instructed AS IT IS."
        "If the INSTRUCTION is CONCISE make the CODE CONCISE too NO REDUNDANT HALLUCINATIONS. "
        f"Only OPERATE on PRESENT COLUMNS: {schema}. IF USER DO NOT MENTION Do not add UI/input unless asked."
        "compute and display the result using st.write(), do NOT add a new column unless specifically requested."
    )
    prompt = (
    schema + instruction + f"DataFrame columns: {columns}\n"
    "You are writing code for Streamlit with an ALREADY LOADED DataFrame `df`.\n"
    "DO NOT use any import statements. DO NOT define a new DataFrame.\n"
    "For statistics like mean, median, or sum, compute ONLY on the correctly filtered subset and display the result using st.write().\n"
    "For plots, use only plt and show with st.pyplot(plt.gcf()) and make sure to USE CORRECT ARGUMENTS."
    f"# {instruction}\n"
    "User question: {}\n"
    ).format(struct['raw'])
    return prompt

def get_code_from_llm(prompt):
    result = llm.invoke([HumanMessage(content=prompt)])
    code = result.content.strip("` \n")
    if code.lower().startswith("python"):
        code = code[len("python"):].lstrip()
    return code

def get_code_from_llm_with_timeout(prompt, timeout_sec=15):
    code = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(get_code_from_llm, prompt)
        try:
            code = future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            pass
    return code

# ------------- STREAMLIT RUN LOOP ---------------
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    df.columns = [str(col).strip() for col in df.columns]
    st.session_state.df = df
    columns = list(df.columns)

    st.dataframe(df)
    user_cmd = st.text_area("Ask your question or give a command (freeform, natural language):", height=90)
    code_to_run = None
    safe_to_run = False

    if user_cmd:
        # --- Structured intent+slots extraction ---
        struct = extract_intent_and_slots(user_cmd, columns)

        # --- Template match (instant, if possible) ---
        if struct["action"] == "remove column" and struct["columns"]:
            code_to_run = f"df = df.drop('{struct['columns'][0]}', axis=1)"
            safe_to_run = True
        else:
            # --- LLM fallback: time-limited codegen ---
            prompt = codegen_prompt_from_structured(struct, columns)
            with st.spinner("⏳ Trying to generate code with AI agent. (Up to 15 seconds)..."):
                code_to_run = get_code_from_llm_with_timeout(prompt, timeout_sec=15)
            if code_to_run is None or not code_to_run.strip():
                st.error("⚠️ The agent could not produce code in time. Please try a simpler step or rephrase.")
            else:
                safe_to_run = is_code_safe(code_to_run)
                if not safe_to_run:
                    st.error("🚨 LLM attempted unsafe code (guardrails blocked execution).")
                cleaned_code = extract_executable_code(code_to_run)
                st.markdown(f"**Generated code:**\n```python\n{cleaned_code}\n```")

        # ----------- Execute if safe -----------
        if safe_to_run and code_to_run:
            try:
                exec_env = {'df': df, 'pd': pd, 'plt': plt, 'st': st}
                cleaned_code = extract_executable_code(code_to_run)
                exec(cleaned_code, exec_env)
                df = exec_env['df']
                st.session_state.df = df
                st.success("✅ Operation performed!")
                if 'plt' in cleaned_code or 'plot' in cleaned_code:
                    st.pyplot(plt.gcf())
                    plt.clf()
            except Exception as e:
                st.error(f"❌ Code execution error: {e}")

        st.dataframe(df, use_container_width=True)

        # --- If nothing could run, prompt user guidance ---
        if (not code_to_run or not safe_to_run):
            st.warning(
                f"⚠️ I couldn't confidently interpret or execute your request.\n"
                f"Please break down your question into a simpler, single-step action.\n\n"
                f"Here are your current column names:\n\n"
                f"`{columns}`"
            )

    st.markdown("---")
    st.subheader("Download updated data")
    file_format = st.selectbox("Choose format:", ["CSV", "Excel"])
    if st.button("Download"):
        if file_format == "CSV":
            csv_data = st.session_state.df.to_csv(index=False).encode('utf-8')
            st.download_button("📤 Download CSV", data=csv_data, file_name="updated_data.csv", mime="text/csv")
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.df.to_excel(writer, index=False)
                writer.save()
            st.download_button(
                "📤 Download Excel",
                data=output.getvalue(),
                file_name="updated_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.info("📁 Please upload a CSV or Excel file to get started.")
