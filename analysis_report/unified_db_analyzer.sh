#!/usr/bin/env bash

# ==============================================================================
# HIS DATABASE MIGRATION ANALYZER (v7.5 - Final MSSQL Fix)
# Fix: Simplified Dynamic SQL construction to prevent variable scope errors
# ==============================================================================

# ... [ส่วน Check Version, Setup, Log เหมือนเดิม] ...
# (เพื่อความกระชับ ผมขอยกเฉพาะส่วน analyze_mssql ที่แก้ใหม่มาให้ครับ)
# คุณสามารถ copy ทั้งก้อนนี้ไปวางทับได้เลย

# --- SETUP ---
BASE_OUTPUT_DIR="./migration_report"
DATE_NOW=$(date +"%Y%m%d_%H%M")
RUN_DIR="$BASE_OUTPUT_DIR/$DATE_NOW"
PROFILE_DIR="$RUN_DIR/data_profile"
DDL_DIR="$RUN_DIR/ddl_schema"

mkdir -p "$PROFILE_DIR"
mkdir -p "$DDL_DIR"

REPORT_FILE="$PROFILE_DIR/data_profile.csv"
DDL_FILE="$DDL_DIR/schema.sql"
LOG_FILE="$RUN_DIR/process.log"

# Initialize Log
echo "----------------------------------------------------------------" > "$LOG_FILE"
echo "HIS Database Migration Analyzer Log" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "----------------------------------------------------------------" >> "$LOG_FILE"

log_activity() {
    local msg="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $msg" >> "$LOG_FILE"
}

# Header CSV
echo "Table,Column,DataType,PK,FK,Default,Comment,Total_Rows,Table_Size_MB,Null_Count,Empty_Count,Zero_Count,Max_Length,Distinct_Values,Min_Val,Max_Val,Top_5_Values,Sample_Values" > "$REPORT_FILE"

# --- DEPENDENCIES ---
check_command() {
    local cmd="$1"
    local brew_pkg="$2"
    if [ -n "$brew_pkg" ] && command -v brew &> /dev/null; then
         BREW_PREFIX=$(brew --prefix)
         POSSIBLE_PATHS=("$BREW_PREFIX/opt/$brew_pkg/bin" "$BREW_PREFIX/Cellar/$brew_pkg/*/bin" "/usr/local/opt/$brew_pkg/bin")
         for p in "${POSSIBLE_PATHS[@]}"; do
             for expanded_path in $p; do
                 if [ -x "$expanded_path/$cmd" ]; then export PATH="$expanded_path:$PATH"; break 2; fi
             done
         done
    fi
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: ไม่พบคำสั่ง '$cmd'"; exit 1
    fi
}
check_command "jq" "jq"

# --- LOAD CONFIG ---
CONFIG_FILE="config.json"
if [ ! -f "$CONFIG_FILE" ]; then echo "❌ Error: ไม่พบไฟล์ $CONFIG_FILE"; exit 1; fi

DB_TYPE=$(jq -r '.database.type' "$CONFIG_FILE")
DB_HOST=$(jq -r '.database.host' "$CONFIG_FILE")
DB_PORT=$(jq -r '.database.port' "$CONFIG_FILE")
DB_NAME=$(jq -r '.database.name' "$CONFIG_FILE")
DB_USER=$(jq -r '.database.user' "$CONFIG_FILE")
DB_PASS=$(jq -r '.database.password' "$CONFIG_FILE")
SELECTED_TABLES_STR=$(jq -r '.database.tables[]?' "$CONFIG_FILE" | tr '\n' ' ')

case "$DB_TYPE" in
    "mysql") DB_CHOICE=1 ;;
    "postgresql"|"postgres") DB_CHOICE=2 ;;
    "mssql"|"sqlserver") DB_CHOICE=3 ;;
    *) echo "❌ Error: Unknown database type"; exit 1 ;;
esac

DEFAULT_LIMIT=$(jq -r '.sampling.default_limit // 10' "$CONFIG_FILE")
MAX_TEXT_LEN=$(jq -r '.sampling.max_text_length // 300' "$CONFIG_FILE")
DEEP_ANALYSIS=$(jq -r '.sampling.deep_analysis // false' "$CONFIG_FILE")
EXCEPTIONS_STRING=$(jq -r '.sampling.exceptions[] | "\(.table).\(.column)=\(.limit)|"' "$CONFIG_FILE" | tr -d '\n')

log_activity "Target: $DB_NAME ($DB_TYPE)"

get_sample_limit() {
    local tbl="$1"; local col="$2"; local distinct_val="$3"
    if [ "$distinct_val" == "1" ]; then echo "1"; return; fi
    local search_key="$tbl.$col="
    if [[ "$EXCEPTIONS_STRING" == *"$search_key"* ]]; then
        local temp="${EXCEPTIONS_STRING#*${search_key}}"
        echo "${temp%%|*}"
        return
    fi
    echo "$DEFAULT_LIMIT"
}

is_date_type() {
    local type=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    if [[ "$type" =~ "date" ]] || [[ "$type" =~ "time" ]] || [[ "$type" =~ "year" ]]; then echo "true"; else echo "false"; fi
}

START_TIME=$(date +%s)
draw_progress() {
    local current=$1; local total=$2; local msg=$3
    local percent=0
    if [ "$total" -gt 0 ]; then percent=$(( 100 * current / total )); fi
    local elapsed=$(( $(date +%s) - START_TIME ))
    local time_str=$(printf "%02d:%02d" $((elapsed/60)) $((elapsed%60)))
    local width=25
    local filled=$(( width * percent / 100 )); local empty=$(( width - filled ))
    local bar="["; for ((i=0; i<filled; i++)); do bar+="="; done; bar+=">"; for ((i=0; i<empty; i++)); do bar+=" "; done; bar+="]"
    printf "\r\033[K%s %3d%% [Tbl %s/%s] (%s) -> %s" "$bar" "$percent" "$current" "$total" "$time_str" "$msg"
}

# ... (MySQL & Postgres functions remain same as v7.2) ...

# === MSSQL LOGIC (REWRITTEN) ===
analyze_mssql() {
    check_command "sqlcmd" "mssql-tools18"
    
    if command -v mssql-scripter &> /dev/null; then
        log_activity "Starting DDL Export..."
        mssql-scripter -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASS" -d "$DB_NAME" --schema-and-data schema --file-path "$DDL_FILE" > /dev/null
    fi

    log_activity "Fetching Tables..."
    if [ -n "$SELECTED_TABLES_STR" ]; then
        TABLES_ARRAY=($SELECTED_TABLES_STR)
    else
        RAW_TABLES=$(sqlcmd -S "$DB_HOST,$DB_PORT" -C -U "$DB_USER" -P "$DB_PASS" -d "$DB_NAME" -h-1 -W -Q "SET NOCOUNT ON; SELECT s.name + '.' + t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.type='U' ORDER BY s.name, t.name")
        IFS=$'\n' read -rd '' -a TABLES_ARRAY <<< "$RAW_TABLES"
    fi
    
    TOTAL_TABLES=${#TABLES_ARRAY[@]}
    CURRENT_IDX=0; START_TIME=$(date +%s)

    for TABLE in "${TABLES_ARRAY[@]}"; do
        ((CURRENT_IDX++))
        TABLE=$(echo "$TABLE" | xargs)
        if [ -z "$TABLE" ]; then continue; fi
        
        draw_progress "$CURRENT_IDX" "$TOTAL_TABLES" "$TABLE"
        log_activity "Processing Table: $TABLE"

        # T-SQL: Inject variables directly into SQL string to avoid scope issues
        TSQL="
        SET NOCOUNT ON;
        DECLARE @SchemaName NVARCHAR(50) = PARSENAME('$TABLE', 2);
        DECLARE @TableNameOnly NVARCHAR(255) = PARSENAME('$TABLE', 1);
        IF @SchemaName IS NULL SET @SchemaName = 'dbo';
        IF @TableNameOnly IS NULL SET @TableNameOnly = '$TABLE';
        
        -- 1. Get Table Size first (Outer Scope)
        DECLARE @SizeMB DECIMAL(10,2);
        SELECT @SizeMB = CAST(SUM(used_page_count) * 8.0 / 1024 AS DECIMAL(10,2)) 
        FROM sys.dm_db_partition_stats WHERE object_id = OBJECT_ID(@SchemaName + '.' + @TableNameOnly);
        SET @SizeMB = ISNULL(@SizeMB, 0);

        -- 2. Cursor Loop
        DECLARE @CName NVARCHAR(255), @DType NVARCHAR(100), @PK NVARCHAR(10), @FK NVARCHAR(255), @Def NVARCHAR(MAX), @Comm NVARCHAR(MAX);
        DECLARE @SQL NVARCHAR(MAX);

        DECLARE cur CURSOR FOR 
            SELECT c.name, ty.name,
                CASE WHEN EXISTS(SELECT 1 FROM sys.indexes i JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id WHERE i.is_primary_key=1 AND ic.object_id=t.object_id AND ic.column_id=c.column_id) THEN 'YES' ELSE '' END,
                ISNULL((SELECT TOP 1 '-> ' + OBJECT_NAME(fkc.referenced_object_id) + '.' + COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) FROM sys.foreign_key_columns fkc WHERE fkc.parent_object_id=t.object_id AND fkc.parent_column_id=c.column_id), ''),
                ISNULL(object_definition(c.default_object_id), ''), ISNULL(CAST(ep.value AS NVARCHAR(MAX)), '')
            FROM sys.tables t 
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            JOIN sys.columns c ON t.object_id = c.object_id 
            JOIN sys.types ty ON c.user_type_id = ty.user_type_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
            WHERE t.name = @TableNameOnly AND s.name = @SchemaName
            ORDER BY c.column_id;

        OPEN cur; FETCH NEXT FROM cur INTO @CName, @DType, @PK, @FK, @Def, @Comm;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            BEGIN TRY
                -- Build Dynamic SQL by injecting @SizeMB directly
                DECLARE @ColSafe NVARCHAR(255) = QUOTENAME(@CName);
                DECLARE @TableSafe NVARCHAR(512) = QUOTENAME(@SchemaName) + '.' + QUOTENAME(@TableNameOnly);
                
                -- Skip BLOBs
                IF @DType IN ('image','text','ntext','binary','geography','geometry','varbinary')
                BEGIN
                    PRINT '$TABLE,' + @CName + ',' + @DType + ',' + @PK + ',' + @FK + ',,,0,' + CAST(@SizeMB AS VARCHAR) + ',0,0,0,0,0,\"\",\"\",\"\",\"Skipped BLOB\"';
                END
                ELSE
                BEGIN
                    SET @SQL = N'
                        DECLARE @Tot BIGINT, @Nul BIGINT, @Emp BIGINT, @Zer BIGINT, @MaxL INT, @Dst BIGINT;
                        DECLARE @Min NVARCHAR(MAX), @Max NVARCHAR(MAX), @Top5 NVARCHAR(MAX), @Sam NVARCHAR(MAX);

                        SELECT @Tot = COUNT(*), 
                               @Nul = SUM(CASE WHEN ' + @ColSafe + ' IS NULL THEN 1 ELSE 0 END),
                               @Emp = SUM(CASE WHEN CAST(' + @ColSafe + ' AS NVARCHAR(MAX)) = '''' THEN 1 ELSE 0 END),
                               @Zer = SUM(CASE WHEN CAST(' + @ColSafe + ' AS NVARCHAR(MAX)) = ''0'' THEN 1 ELSE 0 END),
                               @Dst = COUNT(DISTINCT ' + @ColSafe + ')
                        FROM ' + @TableSafe + ';
                        
                        -- Handle MaxLen (avoid error on non-string types)
                        IF ''' + @DType + ''' LIKE ''%char%'' OR ''' + @DType + ''' LIKE ''%text%''
                           SELECT @MaxL = MAX(LEN(' + @ColSafe + ')) FROM ' + @TableSafe + ';
                        ELSE SET @MaxL = 0;

                        IF ''$DEEP_ANALYSIS'' = ''true''
                        BEGIN
                             SELECT @Min = CAST(MIN(' + @ColSafe + ') AS NVARCHAR(MAX)), @Max = CAST(MAX(' + @ColSafe + ') AS NVARCHAR(MAX)) FROM ' + @TableSafe + ';
                             
                             IF ''' + @DType + ''' NOT LIKE ''%date%'' AND ''' + @DType + ''' NOT LIKE ''%time%''
                                SELECT @Top5 = STUFF((SELECT '' | '' + CAST(val AS NVARCHAR(MAX)) + '' ('' + CAST(cnt AS NVARCHAR(MAX)) + '')'' FROM (SELECT TOP 5 CAST(' + @ColSafe + ' AS NVARCHAR(MAX)) as val, COUNT(*) as cnt FROM ' + @TableSafe + ' WHERE ' + @ColSafe + ' IS NOT NULL GROUP BY ' + @ColSafe + ' ORDER BY cnt DESC) x FOR XML PATH('''')), 1, 3, '''');
                        END

                        DECLARE @Lim INT = $DEFAULT_LIMIT;
                        IF @Dst = 1 SET @Lim = 1;
                        
                        SELECT @Sam = STUFF((SELECT TOP (@Lim) '' | '' + REPLACE(LEFT(CAST(' + @ColSafe + ' AS NVARCHAR(MAX)), $MAX_TEXT_LEN), ''\"'', ''\"\"'') FROM ' + @TableSafe + ' WHERE ' + @ColSafe + ' IS NOT NULL FOR XML PATH('''')), 1, 3, '''');

                        -- Final Output Row
                        SELECT ''$TABLE'',''' + @CName + ''',''' + @DType + ''',''' + @PK + ''',''' + @FK + ''',''' + REPLACE(@Def,'''','''''') + ''',''' + REPLACE(@Comm,'''','''''') + ''',' + 
                               'CAST(@Tot AS VARCHAR) + '','' + 
                               ''' + CAST(@SizeMB AS VARCHAR) + ''' + '','' + 
                               'CAST(@Nul AS VARCHAR) + '','' + CAST(@Emp AS VARCHAR) + '','' + CAST(@Zer AS VARCHAR) + '','' + CAST(ISNULL(@MaxL,0) AS VARCHAR) + '','' + CAST(@Dst AS VARCHAR) + '','' +
                               ''\"'' + ISNULL(REPLACE(@Min,''\"'',''\"\"''),'''') + ''\",\"'' + ISNULL(REPLACE(@Max,''\"'',''\"\"''),'''') + ''\",\"'' + ISNULL(@Top5,'''') + ''\",\"'' + ISNULL(@Sam,'''') + ''\"''';
                    
                    EXEC(@SQL);
                END
            END TRY
            BEGIN CATCH
                -- Error Fallback Row
                PRINT '$TABLE,' + @CName + ',' + @DType + ',ERROR,,,,0,' + CAST(@SizeMB AS VARCHAR) + ',0,0,0,0,0,\"\",\"\",\"\",\"Error: ' + REPLACE(ERROR_MESSAGE(), ',', ';') + '\"';
            END CATCH
            FETCH NEXT FROM cur INTO @CName, @DType, @PK, @FK, @Def, @Comm;
        END
        CLOSE cur; DEALLOCATE cur;
        "
        sqlcmd -S "$DB_HOST,$DB_PORT" -C -U "$DB_USER" -P "$DB_PASS" -d "$DB_NAME" -h-1 -W -Q "$TSQL" >> "$REPORT_FILE"
    done
    echo ""
}

# --- MAIN EXECUTION ---
# Add dummy functions for MySQL/Postgres if not using them, or keep full file content
# For brevity, assuming analyze_mysql and analyze_postgres are already defined above or file is replaced fully.
# (Make sure to copy the FULL file provided in previous context if you need multi-db support)

# ... (Existing MySQL/PG Logic) ...

# Execute Choice
if [ "$DB_CHOICE" == "1" ]; then analyze_mysql;
elif [ "$DB_CHOICE" == "2" ]; then analyze_postgres;
elif [ "$DB_CHOICE" == "3" ]; then analyze_mssql;
else echo "Invalid Selection"; exit 1; fi

echo "========================================="
echo "✅ Analysis Complete!"
echo "📄 Run Folder: $RUN_DIR"
echo "├── 📄 Schema:  $DDL_FILE"
echo "├── 📊 Profile: $REPORT_FILE"
echo "└── 📝 Log:     $LOG_FILE"

if [ -f "csv_to_html.py" ]; then
    echo "🌍 Generating HTML Report..."
    python3 csv_to_html.py "$REPORT_FILE"
    HTML_FILE="${REPORT_FILE%.csv}.html"
    if [ -f "$HTML_FILE" ]; then
        # Auto Open
        if command -v open &> /dev/null; then open "$HTML_FILE"; fi
    fi
fi