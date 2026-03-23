---
name: performance-optimizer
description: "Identifies and fixes performance bottlenecks in code, databases, and APIs. Measures before and after to prove improvements."
category: development
risk: safe
source: community
date_added: "2026-03-05"
---

# Performance Optimizer

Find and fix performance bottlenecks. Measure, optimize, verify.

## Process
1. **Measure first** — never optimize without measuring
2. **Find the bottleneck** — profile to find the slow parts
3. **Fix the slowest thing first** — biggest impact
4. **Measure after** — prove the improvement

## Patterns Relevant to This Project

### Parquet cache (already implemented)
```python
# Check if parquet is newer than xlsx before reading
if (os.path.exists(ruta_parquet) and
        os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_xlsx)):
    return pd.read_parquet(ruta_parquet)
```

### pandas anti-patterns
```python
# Bad: apply() row by row (slow)
df['col'] = df.apply(lambda row: func(row), axis=1)

# Good: vectorized operations
df['col'] = df['col_a'].str.lower().str.strip()

# Bad: repeated DataFrame copies in loop
for item in items:
    df = df.append(item)  # O(n²)

# Good: build list then concat once
rows = [process(item) for item in items]
df = pd.DataFrame(rows)
```

### Streamlit caching
```python
# Cache expensive loads — already used in project
@st.cache_data(ttl=3600)
def cargar_datos():
    ...
```

### Excel loading
- Use `calamine` engine when available (fastest)
- Fall back to `openpyxl`
- Always cache to parquet after first load

## Quick Wins
1. Add `@st.cache_data` to any function that reads files
2. Use parquet instead of xlsx for repeated reads (~20x faster)
3. Use vectorized pandas instead of row-by-row apply()
4. Load only needed columns, not full DataFrames
5. Use `drop_duplicates()` early to reduce working set size

## Optimization Checklist
- [ ] Measured current performance
- [ ] Identified bottleneck
- [ ] Applied optimization
- [ ] Measured improvement
- [ ] Functionality still works
- [ ] No new bugs introduced
