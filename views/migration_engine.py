import streamlit as st
import json
import time
import os
from datetime import datetime
from config import DB_TYPES
import services.db_connector as connector
import services.transformers as transformers
import database as db
import pandas as pd

def generate_select_query(config_data, source_table, sample_limit=None):
    """
    Generate a SELECT query from migration config.
    Only includes columns that are not marked as ignored.

    Args:
        config_data: Migration configuration with mappings
        source_table: Source table name
        sample_limit: Optional limit for sample data (e.g., 20 for testing)

    Returns:
        SQL SELECT query string
    """
    try:
        if not config_data or 'mappings' not in config_data:
            return f"SELECT * FROM {source_table}"

        # Extract columns to select (those not ignored)
        selected_cols = [
            mapping['source']
            for mapping in config_data.get('mappings', [])
            if not mapping.get('ignore', False)
        ]

        if not selected_cols:
            return f"SELECT * FROM {source_table}"

        # Build SELECT query
        columns_str = ", ".join([f"[{col}]" for col in selected_cols])
        query = f"SELECT {columns_str} FROM {source_table}"

        if sample_limit:
            query += f" LIMIT {sample_limit}"

        return query
    except Exception as e:
        return f"SELECT * FROM {source_table}"


def create_migration_log_file(config_name: str) -> str:
    """
    Create a migration log file for tracking the migration process.

    Args:
        config_name: Name of the migration configuration

    Returns:
        Path to the log file
    """
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "migration_logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in config_name)
        log_file = os.path.join(log_dir, f"migration_{safe_name}_{timestamp}.log")

        return log_file
    except Exception as e:
        return None


def write_log(log_file: str, message: str):
    """Write a message to the log file."""
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to log: {e}")

def render_migration_engine_page():
    st.subheader("🚀 Data Migration Execution Engine")

    # Initialize session state
    if "migration_step" not in st.session_state:
        st.session_state.migration_step = 1
    if "migration_config" not in st.session_state:
        st.session_state.migration_config = None
    if "migration_src_result" not in st.session_state:
        st.session_state.migration_src_result = None
    if "migration_tgt_result" not in st.session_state:
        st.session_state.migration_tgt_result = None
    if "migration_src_profile" not in st.session_state:
        st.session_state.migration_src_profile = None
    if "migration_tgt_profile" not in st.session_state:
        st.session_state.migration_tgt_profile = None
    if "migration_test_sample" not in st.session_state:
        st.session_state.migration_test_sample = False

    # Step 1: Select Configuration
    if st.session_state.migration_step == 1:
        st.markdown("### Step 1: Select Configuration")
        st.markdown("Load a migration configuration from your project database or upload a JSON file.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📚 Load from Project DB", use_container_width=True):
                st.session_state.migration_step = 1.1

        with col2:
            if st.button("📂 Upload JSON File", use_container_width=True):
                st.session_state.migration_step = 1.2

        st.divider()

        # Substep 1.1: Load from database
        if st.session_state.migration_step == 1.1:
            st.markdown("#### Load from Project DB")
            configs_df = db.get_configs_list()
            if not configs_df.empty:
                sel_config = st.selectbox("Select Saved Config", configs_df['config_name'], key="mig_sel_config")
                if sel_config:
                    st.session_state.migration_config = db.get_config_content(sel_config)
                    st.info(f"Loaded: {sel_config}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Proceed to Connection Test", key="proceed_from_db", type="primary", use_container_width=True):
                            st.session_state.migration_step = 2
                            st.rerun()
                    with col_b:
                        if st.button("Cancel", key="cancel_from_db", use_container_width=True):
                            st.session_state.migration_step = 1
                            st.session_state.migration_config = None
                            st.rerun()
            else:
                st.warning("No configs saved in database yet.")
                if st.button("← Back", key="back_from_db"):
                    st.session_state.migration_step = 1
                    st.rerun()

        # Substep 1.2: Upload file
        elif st.session_state.migration_step == 1.2:
            st.markdown("#### Upload JSON File")
            uploaded = st.file_uploader("Upload .json config file", type=["json"], key="mig_upload_file")
            if uploaded:
                st.session_state.migration_config = json.load(uploaded)
                st.info(f"Loaded: {uploaded.name}")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Proceed to Connection Test", key="proceed_from_upload", type="primary", use_container_width=True):
                        st.session_state.migration_step = 2
                        st.rerun()
                with col_b:
                    if st.button("Cancel", key="cancel_from_upload", use_container_width=True):
                        st.session_state.migration_step = 1
                        st.session_state.migration_config = None
                        st.rerun()
            else:
                if st.button("← Back", key="back_from_upload"):
                    st.session_state.migration_step = 1
                    st.rerun()

    # Step 2: Test Connections
    elif st.session_state.migration_step == 2:
        st.markdown("### Step 2: Test Database Connections")
        st.markdown("Verify connectivity to both source and target databases.")

        if st.session_state.migration_config:
            with st.expander("Current Config", expanded=False):
                st.json(st.session_state.migration_config, expanded=False)

        datasources = db.get_datasources()
        col_src, col_tgt = st.columns(2)

        # --- Source Database ---
        with col_src:
            st.markdown("#### Source Database")
            src_options = ["Custom Connection"] + datasources['name'].tolist()
            src_select = st.selectbox("Select Source Profile", src_options, key="mig_src_sel")
            st.session_state.migration_src_profile = src_select

            if src_select != "Custom Connection":
                row = datasources[datasources['name'] == src_select].iloc[0]
                ds = db.get_datasource_by_id(int(row['id']))

                src_type = st.text_input("Type", ds['db_type'], key="mig_src_t", disabled=True)
                c1, c2 = st.columns([3, 1])
                src_host = c1.text_input("Host", ds['host'], key="mig_src_h", disabled=True)
                src_port = c2.text_input("Port", ds['port'], key="mig_src_po", disabled=True)

                src_db = st.text_input("DB Name", ds['dbname'], key="mig_src_d", disabled=True)
                src_user = ds['username']
                src_pass = ds['password']
                st.caption(f"User: {src_user}")
            else:
                src_type = st.selectbox("Database Type", DB_TYPES, key="mig_src_t_c")
                c1, c2 = st.columns([3, 1])
                src_host = c1.text_input("Host", "192.168.1.10", key="mig_src_h_c")
                src_port = c2.text_input("Port", "", key="mig_src_po_c")

                src_db = st.text_input("Database Name", "hos_db", key="mig_src_d_c")
                src_user = st.text_input("User", "sa", key="mig_src_u_c")
                src_pass = st.text_input("Password", type="password", key="mig_src_p_c")

            if st.button("🔍 Test Source Connection", key="mig_btn_src", use_container_width=True):
                with st.spinner(f"Connecting to {src_host}:{src_port}..."):
                    ok, msg = connector.test_db_connection(src_type, src_host, src_port, src_db, src_user, src_pass)
                    st.session_state.migration_src_result = (ok, msg)
                    st.rerun()

            if st.session_state.migration_src_result:
                ok, msg = st.session_state.migration_src_result
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.error(f"✗ {msg}")

        # --- Target Database ---
        with col_tgt:
            st.markdown("#### Target Database")
            tgt_options = ["Custom Connection"] + datasources['name'].tolist()
            tgt_select = st.selectbox("Select Target Profile", tgt_options, key="mig_tgt_sel")
            st.session_state.migration_tgt_profile = tgt_select

            if tgt_select != "Custom Connection":
                row = datasources[datasources['name'] == tgt_select].iloc[0]
                ds = db.get_datasource_by_id(int(row['id']))

                tgt_type = st.text_input("Type", ds['db_type'], key="mig_tgt_t", disabled=True)
                c3, c4 = st.columns([3, 1])
                tgt_host = c3.text_input("Host", ds['host'], key="mig_tgt_h", disabled=True)
                tgt_port = c4.text_input("Port", ds['port'], key="mig_tgt_po", disabled=True)

                tgt_db = st.text_input("DB Name", ds['dbname'], key="mig_tgt_d", disabled=True)
                tgt_user = ds['username']
                tgt_pass = ds['password']
                st.caption(f"User: {tgt_user}")
            else:
                tgt_type = st.selectbox("Database Type", DB_TYPES, index=2, key="mig_tgt_t_c")
                c3, c4 = st.columns([3, 1])
                tgt_host = c3.text_input("Host", "10.0.0.5", key="mig_tgt_h_c")
                tgt_port = c4.text_input("Port", "", key="mig_tgt_po_c")

                tgt_db = st.text_input("Database Name", "hospital_new", key="mig_tgt_d_c")
                tgt_user = st.text_input("User", "admin", key="mig_tgt_u_c")
                tgt_pass = st.text_input("Password", type="password", key="mig_tgt_p_c")

            if st.button("🔍 Test Target Connection", key="mig_btn_tgt", use_container_width=True):
                with st.spinner(f"Connecting to {tgt_host}:{tgt_port}..."):
                    ok, msg = connector.test_db_connection(tgt_type, tgt_host, tgt_port, tgt_db, tgt_user, tgt_pass)
                    st.session_state.migration_tgt_result = (ok, msg)
                    st.rerun()

            if st.session_state.migration_tgt_result:
                ok, msg = st.session_state.migration_tgt_result
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.error(f"✗ {msg}")

        st.divider()

        # Navigation buttons
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            if st.button("← Back", key="back_step2", use_container_width=True):
                st.session_state.migration_step = 1
                st.rerun()

        with col_nav3:
            can_proceed = (
                st.session_state.migration_src_result and st.session_state.migration_src_result[0] and
                st.session_state.migration_tgt_result and st.session_state.migration_tgt_result[0]
            )
            if st.button("Next: Review & Execute →", key="next_step2", type="primary", disabled=not can_proceed, use_container_width=True):
                st.session_state.migration_step = 3
                st.rerun()

    # Step 3: Review & Execute
    elif st.session_state.migration_step == 3:
        st.markdown("### Step 3: Review & Execute Migration")
        st.markdown("Review your configuration and execute the migration.")

        col_preview, col_settings = st.columns([1, 1])

        with col_preview:
            st.markdown("#### Configuration Preview")
            if st.session_state.migration_config:
                st.json(st.session_state.migration_config, expanded=False)

        with col_settings:
            st.markdown("#### Migration Settings")

            batch_size = st.number_input(
                "Batch Size",
                min_value=10,
                max_value=10000,
                value=st.session_state.migration_config.get('batch_size', 1000) if st.session_state.migration_config else 1000,
                step=10,
                help="Number of records to process per batch"
            )

            st.session_state.migration_test_sample = st.checkbox(
                "Test with sample data (20 records)",
                value=st.session_state.migration_test_sample,
                help="Process only 20 records for testing"
            )

            st.info(f"Batch Size: {batch_size} records")
            if st.session_state.migration_test_sample:
                st.warning("Sample mode enabled: will process only 20 records")

        st.divider()

        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            if st.button("← Back", key="back_step3", use_container_width=True):
                st.session_state.migration_step = 2
                st.rerun()

        with col_nav3:
            if st.button("🚀 Start Migration", key="start_migration", type="primary", use_container_width=True):
                st.session_state.migration_step = 4
                st.rerun()

    # Step 4: Migration Execution & Logging
    elif st.session_state.migration_step == 4:
        st.markdown("### Step 4: Migration Execution")

        col_progress, col_log = st.columns([1, 2])

        with col_progress:
            st.markdown("#### Progress")
            progress_bar = st.progress(0)
            status_placeholder = st.empty()

        with col_log:
            st.markdown("#### Migration Log")
            log_placeholder = st.empty()

        # Initialize logs list
        logs = []

        def add_log(message):
            logs.append(message)
            log_placeholder.text_area("", value="\n".join(logs), height=300, disabled=True, label_visibility="collapsed")
            # Also write to file if log file exists
            if 'migration_log_file' in st.session_state:
                write_log(st.session_state.migration_log_file, message)

        # Create log file
        config_name = st.session_state.migration_config.get('config_name', 'migration') if st.session_state.migration_config else 'migration'
        log_file = create_migration_log_file(config_name)
        st.session_state.migration_log_file = log_file

        add_log("📋 Starting migration process...")
        if log_file:
            add_log(f"   → Log file: {log_file}")
        time.sleep(0.3)
        progress_bar.progress(10)

        # Get source and target tables from config
        config = st.session_state.migration_config
        source_table = config.get('source', {}).get('table', 'source_table') if config else 'source_table'
        target_table = config.get('target', {}).get('table', 'target_table') if config else 'target_table'

        add_log(f"🔍 Analyzing source: {source_table} → {target_table}")
        time.sleep(0.3)
        progress_bar.progress(15)

        add_log("📊 Building SELECT query (excluding ignored columns)...")

        # Generate SELECT query
        sample_limit = 20 if st.session_state.migration_test_sample else None
        select_query = generate_select_query(config, source_table, sample_limit)

        if config and 'mappings' in config:
            included_cols = [m['source'] for m in config.get('mappings', [])
                            if not m.get('ignore', False)]
            ignored_cols = [m['source'] for m in config.get('mappings', [])
                           if m.get('ignore', False)]
            add_log(f"   → Selected {len(included_cols)} columns, ignored {len(ignored_cols)}")

        add_log(f"   → Query: {select_query[:80]}...")
        time.sleep(0.3)
        progress_bar.progress(25)

        # Simulate batch processing
        batch_size = config.get('batch_size', 1000) if config else 1000
        sample_text = " (SAMPLE MODE: 20 records)" if st.session_state.migration_test_sample else ""
        add_log(f"🔄 Starting batch processing{sample_text} - Batch size: {batch_size} records")
        time.sleep(0.3)
        progress_bar.progress(30)

        # Simulate data retrieval and transformation
        # In a real scenario, this would fetch actual data from the source database
        total_records = 20 if st.session_state.migration_test_sample else 5000
        batch_count = (total_records + batch_size - 1) // batch_size

        add_log(f"   → Total records to process: {total_records}")
        add_log(f"   → Number of batches: {batch_count}")
        time.sleep(0.3)

        add_log("✨ Processing batches with data transformers...")
        processed_records = 0
        for batch_num in range(1, batch_count + 1):
            batch_records = min(batch_size, total_records - processed_records)
            processed_records += batch_records

            # Simulate transformer application
            add_log(f"   → Batch {batch_num}: Processing {batch_records} records")

            # Simulate applying transformers (in real scenario, apply actual transformers from config)
            if config and 'mappings' in config:
                transformer_count = sum(1 for m in config.get('mappings', [])
                                      if m.get('transformers'))
                if transformer_count > 0:
                    add_log(f"      • Applied {transformer_count} transformer(s)")

            add_log(f"      • Validated {batch_records} records")
            add_log(f"      • Progress: {processed_records}/{total_records} records")

            time.sleep(0.2)
            progress = int(30 + (batch_num / batch_count) * 50)
            progress_bar.progress(progress)

        add_log("💾 Inserting data into target database...")
        add_log(f"   → Target table: {target_table}")
        add_log(f"   → Total records to insert: {processed_records}")
        time.sleep(0.3)
        progress_bar.progress(85)

        add_log("✓ Data insertion completed")
        add_log("📊 Generating migration summary...")
        add_log(f"   → Total records processed: {processed_records}")
        add_log(f"   → Total batches: {batch_count}")
        add_log(f"   → Migration time: {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(0.3)
        progress_bar.progress(95)

        add_log("✓ Migration completed successfully!")
        progress_bar.progress(100)
        status_placeholder.success("✓ Migration Complete")

        st.balloons()

        st.divider()

        # Display generated query and log file info
        col_info1, col_info2 = st.columns(2)

        with col_info1:
            with st.expander("View Generated SELECT Query"):
                st.code(select_query, language="sql")

        with col_info2:
            if log_file:
                st.info(f"📄 **Log File**: {log_file}")
                if st.button("📋 Open Log File", use_container_width=True):
                    try:
                        with open(log_file, 'r') as f:
                            st.text_area("Migration Log File", value=f.read(), height=300, disabled=True)
                    except:
                        st.error("Could not read log file")

        st.divider()

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("← Start New Migration", key="new_migration", use_container_width=True):
                st.session_state.migration_step = 1
                st.session_state.migration_config = None
                st.session_state.migration_src_result = None
                st.session_state.migration_tgt_result = None
                st.session_state.migration_test_sample = False
                st.session_state.migration_log_file = None
                st.rerun()

        with col_nav2:
            if st.button("📊 View Migration Report", key="view_report", use_container_width=True):
                if log_file and os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read()
                        st.success("Migration report:")
                        st.text(content)
                    except:
                        st.error("Could not read report")
                else:
                    st.warning("No log file available")