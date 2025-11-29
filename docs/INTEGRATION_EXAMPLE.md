# Integration Example: AI Column Analysis in Schema Mapper

## Quick Integration Guide

This guide shows how to integrate the AI column analysis into the Schema Mapper UI.

## Option 1: Add "Analyze Column" Button (Per Row)

Add a button in the Quick Edit Panel that analyzes the selected column:

```python
# In schema_mapper.py, inside the Quick Edit Panel section (around line 390)

with c_edit_3:
    new_vals = st.multiselect("Validators", VALIDATOR_OPTIONS, default=def_vals, key=f"ms_vd_{src_col}")

# ADD THIS NEW SECTION:
with st.container():
    if st.button("🔬 AI Analyze", key=f"ai_analyze_{src_col}", help="Analyze sample data to suggest transformers"):
        with st.spinner(f"Analyzing {src_col}..."):
            # Get source database info
            source_db = st.session_state.get("mapper_source_db")
            source_table = st.session_state.get("mapper_source_tbl")

            # Only works if connected to live datasource
            if source_db and source_db != "Run ID (CSV)":
                import database as db
                from services.db_connector import get_column_sample_values
                from services.ml_mapper import ml_mapper

                # Get datasource info
                src_ds = db.get_datasource_by_name(source_db)

                if src_ds:
                    # Fetch sample values
                    ok, samples = get_column_sample_values(
                        src_ds['db_type'], src_ds['host'], src_ds['port'],
                        src_ds['dbname'], src_ds['username'], src_ds['password'],
                        source_table, src_col, limit=20
                    )

                    if ok:
                        # Run AI analysis
                        result = ml_mapper.analyze_column_with_sample(
                            source_col_name=src_col,
                            target_col_name=new_target,
                            sample_values=samples
                        )

                        # Display results
                        st.info(f"**Analysis Result**\n\n{result['reason']}")
                        st.metric("Confidence", f"{result['confidence_score']:.0%}")

                        # Apply suggestions if confidence is high
                        if result['confidence_score'] >= 0.7 and result['transformers']:
                            if st.button("✅ Apply Suggestions", key=f"apply_{src_col}"):
                                st.session_state[f"df_{active_table}"].at[idx, 'Transformers'] = ", ".join(result['transformers'])
                                if result['should_ignore']:
                                    st.session_state[f"df_{active_table}"].at[idx, 'Ignore'] = True
                                st.session_state.mapper_editor_ver = time.time()
                                st.rerun()
                    else:
                        st.warning(f"Could not fetch sample data: {samples}")
            else:
                st.warning("AI Analysis only available for live datasource connections")
```

## Option 2: Enhance AI Auto-Map (Batch Analysis)

Enhance the existing AI Auto-Map button to include sample data analysis:

```python
# In schema_mapper.py, around line 322 (inside the AI Auto-Map button handler)

if st.button("🤖 AI Auto-Map", type="primary", use_container_width=True):
    with st.spinner("🤖 AI is analyzing columns and sample data..."):
        source_cols = st.session_state[f"df_{active_table}"]["Source Column"].tolist()

        # STEP 1: Get semantic mappings (existing)
        suggestions = ml_mapper.suggest_mapping(source_cols, real_target_columns)

        # STEP 2: NEW - Analyze sample data for each column
        source_db = st.session_state.get("mapper_source_db")
        source_table = st.session_state.get("mapper_source_tbl")

        transformer_suggestions = {}
        confidence_scores = {}

        if source_db and source_db != "Run ID (CSV)":
            import database as db
            from services.db_connector import get_column_sample_values

            src_ds = db.get_datasource_by_name(source_db)

            if src_ds:
                for src_col in source_cols:
                    # Fetch sample data
                    ok, samples = get_column_sample_values(
                        src_ds['db_type'], src_ds['host'], src_ds['port'],
                        src_ds['dbname'], src_ds['username'], src_ds['password'],
                        source_table, src_col, limit=20
                    )

                    if ok and samples:
                        # Get target column from suggestions
                        target_col = suggestions.get(src_col, "")

                        # Analyze with sample data
                        analysis = ml_mapper.analyze_column_with_sample(
                            source_col_name=src_col,
                            target_col_name=target_col,
                            sample_values=samples
                        )

                        transformer_suggestions[src_col] = analysis['transformers']
                        confidence_scores[src_col] = analysis['confidence_score']

        # STEP 3: Apply both mappings and transformers
        df_current = st.session_state[f"df_{active_table}"]
        match_count = 0
        transformer_count = 0

        for idx, row in df_current.iterrows():
            src = row['Source Column']

            # Apply column mapping
            if src in suggestions and suggestions[src]:
                df_current.at[idx, 'Target Column'] = suggestions[src]
                match_count += 1

            # Apply transformer suggestions
            if src in transformer_suggestions and transformer_suggestions[src]:
                df_current.at[idx, 'Transformers'] = ", ".join(transformer_suggestions[src])
                transformer_count += 1

            # Add confidence indicator (optional - as a comment or metadata)
            # You could add a new column "AI_Confidence" to show scores

        st.session_state[f"df_{active_table}"] = df_current
        st.session_state.mapper_editor_ver = time.time()

        st.success(f"🤖 AI matched {match_count} columns with {transformer_count} transformer suggestions!")
        st.rerun()
```

## Option 3: Add Sample Data Preview Column

Add a new column to the AgGrid showing sample values:

```python
# In init_editor_state(), around line 551

editor_data.append({
    "Status": "",
    "Source Column": src_col,
    "Type": dtype,
    "Target Column": target_col,
    "Transformers": ", ".join(transformers),
    "Validators": ", ".join(validators),
    "Required": False,
    "Ignore": ignore,
    # NEW: Add sample preview column
    "Samples": ""  # Will be populated on demand
})
```

Then fetch samples on-demand when user clicks "Show Samples" button.

## Option 4: Background Analysis with Progress

Run analysis in background when datasource is selected:

```python
# After target configuration (around line 303)

if target_db_input and target_table_input:
    # Run background analysis
    analysis_key = f"analysis_{source_db_input}_{source_table_name}"

    if analysis_key not in st.session_state:
        with st.spinner("Analyzing source data patterns..."):
            # Run analysis for all columns
            # Store results in session state
            # Use progress bar for UX
            pass
```

## Complete Example: Single Column Analysis

Here's a complete standalone example:

```python
import streamlit as st
from services.ml_mapper import ml_mapper
from services.db_connector import get_column_sample_values
import database as db

def analyze_single_column(datasource_name, table_name, column_name, target_column_name):
    """
    Analyze a single column with AI and display results.

    Args:
        datasource_name: Name of datasource in database
        table_name: Source table name
        column_name: Source column to analyze
        target_column_name: Target column it's mapped to
    """

    # Get datasource config
    ds = db.get_datasource_by_name(datasource_name)

    if not ds:
        st.error(f"Datasource '{datasource_name}' not found")
        return

    # Fetch sample values
    st.info(f"Fetching sample values from {table_name}.{column_name}...")

    ok, samples = get_column_sample_values(
        db_type=ds['db_type'],
        host=ds['host'],
        port=ds['port'],
        db_name=ds['dbname'],
        user=ds['username'],
        password=ds['password'],
        table_name=table_name,
        column_name=column_name,
        limit=20
    )

    if not ok:
        st.error(f"Failed to fetch samples: {samples}")
        return

    if not samples:
        st.warning("No sample data found (all values are NULL or empty)")
        return

    # Run AI analysis
    st.info("Running AI analysis...")

    result = ml_mapper.analyze_column_with_sample(
        source_col_name=column_name,
        target_col_name=target_column_name,
        sample_values=samples
    )

    # Display results
    st.success("Analysis Complete!")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Confidence", f"{result['confidence_score']:.0%}")

    with col2:
        st.metric("Match Status", "✅ Match" if result['is_match'] else "❌ Mismatch")

    with col3:
        st.metric("Should Ignore", "Yes" if result['should_ignore'] else "No")

    st.write("**Reason:**", result['reason'])

    if result['transformers']:
        st.write("**Suggested Transformers:**")
        for transformer in result['transformers']:
            st.code(transformer, language="")
    else:
        st.write("**Transformers:** None needed")

    # Show sample preview
    with st.expander("View Sample Data"):
        st.write(samples[:10])  # Show first 10 samples


# Usage in Streamlit UI:
if __name__ == "__main__":
    st.title("AI Column Analysis Demo")

    datasource = st.text_input("Datasource Name", value="HIS_Production")
    table = st.text_input("Table Name", value="patients")
    source_col = st.text_input("Source Column", value="birth_date")
    target_col = st.text_input("Target Column", value="dob")

    if st.button("🔬 Analyze"):
        analyze_single_column(datasource, table, source_col, target_col)
```

## Performance Considerations

### Caching Sample Data

To avoid repeated database queries:

```python
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_cached_samples(ds_name, table_name, column_name):
    """Cache sample values to reduce database load."""
    ds = db.get_datasource_by_name(ds_name)
    if not ds:
        return False, "Datasource not found"

    return get_column_sample_values(
        ds['db_type'], ds['host'], ds['port'],
        ds['dbname'], ds['username'], ds['password'],
        table_name, column_name, limit=20
    )
```

### Batch Analysis Optimization

```python
def analyze_all_columns_batch(datasource, table_name, column_list, target_mappings):
    """
    Analyze multiple columns in batch to reduce overhead.

    Returns: dict of {column_name: analysis_result}
    """
    results = {}

    with st.progress(0) as progress_bar:
        total = len(column_list)

        for i, col in enumerate(column_list):
            # Update progress
            progress_bar.progress((i + 1) / total)

            # Fetch and analyze
            ok, samples = get_cached_samples(datasource, table_name, col)

            if ok and samples:
                target = target_mappings.get(col, "")
                results[col] = ml_mapper.analyze_column_with_sample(col, target, samples)

    return results
```

## UI/UX Best Practices

1. **Show Confidence Visually**
   - Use color coding: Green (>0.7), Yellow (0.5-0.7), Red (<0.5)
   - Add confidence badges to column rows

2. **Progressive Disclosure**
   - Show basic mappings first
   - Offer "Deep Analysis" as optional enhancement
   - Allow users to override AI suggestions

3. **Feedback Loop**
   - Let users mark suggestions as "Helpful" or "Not Helpful"
   - Track which patterns work well for future improvements

4. **Error Handling**
   - Gracefully handle missing sample data
   - Provide fallback to name-based mapping
   - Clear error messages

## Testing

Test the integration with:

```bash
# 1. Run test suite
python test_column_analysis.py

# 2. Test database connectivity
streamlit run app.py

# 3. Manual test in Schema Mapper:
# - Select a live datasource
# - Choose a table
# - Click analyze on date column
# - Verify transformer suggestions
```

---

**Next Steps:**
1. Choose integration option that fits your workflow
2. Test with real HIS data
3. Gather user feedback
4. Refine pattern detection as needed
