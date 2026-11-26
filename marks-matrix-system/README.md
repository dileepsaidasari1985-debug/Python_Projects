# Student Marks Matrix Analysis System

**Case Study #42:** *Analyse a matrix of student marks across subjects, calculate row-wise and column-wise statistics, identify top performers, and detect subjects with low average performance.*

## Key Features
- **2D Nested List Matrix Engine**: Stores and processes `[student_id, name, [marks...]]` rows across 5 subjects.
- **Row-Wise & Column-Wise Statistics**: Computes per-student totals, averages, min/max, grades, and per-subject averages, highest/lowest scores, and pass rates.
- **Top Performers & Tie-Breaking**: Ranks students deterministically using tuple comparisons `(-average, -total, -min_mark, student_id)`.
- **Low-Average Subject Detection**: Highlights subjects scoring below configurable average thresholds alongside ASCII matrix reports and CSV exports.
