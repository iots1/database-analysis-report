import streamlit as st
import pandas as pd
import json
import os
import glob

# --- CONFIGURATION ---
st.set_page_config(page_title="HIS Migration Toolkit", layout="wide", page_icon="🏥")

# 1. Define Paths relative to ROOT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis_report")
MIGRATION_REPORT_DIR = os.path.join(ANALYSIS_DIR, "migration_report")
CONFIG_FILE = os.path.join(ANALYSIS_DIR, "config.json")

# --- HELPER FUNCTIONS ---

def load_config():
    """Load database config from analysis_report folder"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def get_report_folders():
    """Find all report folders in analysis_report/migration_report"""
    if not os.path.exists(MIGRATION_REPORT_DIR):
        return []
    folders = glob.glob(os.path.join(MIGRATION_REPORT_DIR, "*"))
    folders.sort(reverse=True) # Newest first
    return folders

@st.cache_data
def load_data_profile(report_folder):
    """Load CSV from selected report folder"""
    csv_path = os.path.join(report_folder, "data_profile", "data_profile.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

def to_camel_case(snake_str):
    """Convert snake_case to camelCase"""
    if pd.isna(snake_str): return ""
    components = str(snake_str).split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def generate_ts_definition(table_name, target_table, mappings_df):
    """Generate TypeScript Definition Code"""
    mappings_str = ""
    for _, row in mappings_df.iterrows():
        if row['Ignore']: continue
            
        props = [f"      source: '{row['Source Column']}'", f"      target: '{row['Target Column']}'"]
        
        if row['Transformer']: props.append(f"      transformer: '{row['Transformer']}'")
        if row['Validator']: props.append(f"      validator: '{row['Validator']}'")
        if row['Required']: props.append(f"      required: true")
            
        mappings_str += "    {\n" + ",\n".join(props) + "\n    },\n"

    class_name = str(table_name).capitalize() + "Definition"
    
    return f"""import {{ TableDefinition }} from '../../../types';

export const {class_name}: TableDefinition = {{
  name: '{table_name}',
  targetTable: '{target_table}',
  description: 'Auto-generated definition for {table_name}',
  
  defaultBatchSize: 5000,
  defaultPriority: 50,
  
  commonMappings: [
{mappings_str}  ]
}};"""

# --- UI LAYOUT ---

st.title("🏥 HIS Migration Toolkit Center")
st.markdown("ศูนย์รวมเครื่องมือวิเคราะห์และจัดการ Migration (Mockup -> Analysis -> Config)")

# Sidebar Navigation
with st.sidebar:
    st.header("Navigate")
    page = st.radio("Go to", ["📊 Schema Mapper", "📁 File Explorer", "⚙️ Configuration"])
    
    st.divider()
    st.caption(f"📂 Root: {BASE_DIR}")

if page == "📊 Schema Mapper":
    # --- SCHEMA MAPPER LOGIC (From previous script) ---
    
    report_folders = get_report_folders()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("1. Select Source")
        if not report_folders:
            st.warning("⚠️ No reports found in `analysis_report/`")
            st.info("Run `./unified_db_analyzer.sh` first.")
            st.stop()
            
        selected_folder = st.selectbox("Report Run", report_folders, format_func=lambda x: os.path.basename(x))
        
        df = load_data_profile(selected_folder)
        if df is None:
            st.error("❌ data_profile.csv missing!")
            st.stop()
            
        tables = df['Table'].unique()
        selected_table = st.selectbox("Select Table", tables)
        
        # Mini Stats
        if selected_table:
            stats = df[df['Table'] == selected_table].iloc[0]
            st.metric("Rows", f"{stats.get('Total_Rows', 0):,}")
            st.metric("Size (MB)", f"{stats.get('Table_Size_MB', 0)}")

    with col2:
        if selected_table:
            st.subheader(f"2. Map Schema: {selected_table}")
            table_data = df[df['Table'] == selected_table]
            
            target_table_name = st.text_input("Target Table Name", value=selected_table)
            
            # Prepare Data for Editor
            editor_data = []
            for _, row in table_data.iterrows():
                src_col = row['Column']
                dtype = row['DataType']
                
                # Auto-Guess
                target_col = to_camel_case(src_col)
                transformer = ""
                validator = ""
                
                if "date" in str(dtype).lower() or "time" in str(dtype).lower():
                    transformer = "BUDDHIST_TO_ISO"
                    validator = "VALID_DATE"
                elif "char" in str(dtype).lower():
                    transformer = "TRIM"
                
                if src_col == "hn": 
                    transformer = "UPPER_TRIM"; validator = "HN_FORMAT"
                
                editor_data.append({
                    "Source Column": src_col,
                    "Type": dtype,
                    "Target Column": target_col,
                    "Transformer": transformer,
                    "Validator": validator,
                    "Required": False,
                    "Ignore": False,
                    "Sample": str(row.get('Sample_Values', ''))[:50]
                })
            
            # Data Editor
            edit_df = st.data_editor(
                pd.DataFrame(editor_data),
                column_config={
                    "Source Column": st.column_config.TextColumn(disabled=True),
                    "Type": st.column_config.TextColumn(disabled=True, width="small"),
                    "Transformer": st.column_config.SelectboxColumn(options=["", "TRIM", "UPPER_TRIM", "BUDDHIST_TO_ISO", "SPLIT_NAME", "FORMAT_PHONE"]),
                    "Validator": st.column_config.SelectboxColumn(options=["", "REQUIRED", "THAI_ID", "HN_FORMAT", "VALID_DATE"]),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{selected_table}"
            )
            
            st.subheader("3. Result")
            if st.button("⚡ Generate TypeScript Config", type="primary"):
                ts_code = generate_ts_definition(selected_table, target_table_name, edit_df)
                st.code(ts_code, language="typescript")
        else:
            st.info("👈 Please select a table from the left sidebar.")

elif page == "📁 File Explorer":
    st.subheader("Project Files Structure")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📂 Analysis Report")
        st.markdown("Scripts for analyzing real database.")
        if os.path.exists(ANALYSIS_DIR):
            files = os.listdir(ANALYSIS_DIR)
            st.code("\n".join(files))
        else:
            st.error("Folder not found!")

    with col2:
        st.markdown("### 📂 Mini HIS (Mockup)")
        st.markdown("Scripts for generating mock data.")
        mini_his_dir = os.path.join(BASE_DIR, "mini_his")
        if os.path.exists(mini_his_dir):
            files = os.listdir(mini_his_dir)
            st.code("\n".join(files))
        else:
            st.error("Folder not found!")

elif page == "⚙️ Configuration":
    st.subheader("Database Configuration")
    config = load_config()
    
    if config:
        st.json(config)
        st.info(f"Edit this config at: `{CONFIG_FILE}`")
    else:
        st.warning("Config file not found or invalid.")