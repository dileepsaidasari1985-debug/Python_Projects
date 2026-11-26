# Step-by-Step Algorithm

1. **Start** and load student marks matrix and thresholds (`low_avg_threshold`, `pass_mark`) from SQLite.
2. **Row-Wise Pass**: Loop over every student row `(student_id, name, marks)`:
   - Sum `marks`, track `min_mark` and `max_mark`, count subjects `< pass_mark`, compute `average = total / num_subjects`, and assign letter grade.
3. **Ranking Pass**: Sort row summaries by `(-average, -total, -min_mark, student_id)` and extract the top 3 performers.
4. **Column-Wise Pass**: For each subject column `c` from `0` to `num_subjects - 1`:
   - Inner loop over every student row: accumulate `col_sum`, track `highest`, `lowest`, and `pass_count`.
   - Compute `subj_avg = col_sum / num_students` and `pass_rate`.
   - If `subj_avg < low_avg_threshold`, append subject to `low_avg_subjects`.
5. **Output**: Generate ASCII summary table, render web tables, and support CSV export.
6. **End**.
