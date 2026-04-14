import { useState } from "react";

const INITIAL = {
  num_files_changed: 5,
  lines_added: 100,
  lines_deleted: 20,
  test_count: 200,
  test_pass_count: 200,
  test_fail_count: 0,
  build_duration_seconds: 180,
  hour: 14,
  day_of_week: 2,
  is_late_night: 0,
  is_weekend: 0,
  branch_type: "feature",
  trigger_type: "pull_request",
};

function PredictionForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL);

  const set = (key, value) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value };

      // Auto-calc late night
      if (key === "hour") {
        const h = Number(value);
        next.is_late_night = h >= 22 || h <= 5 ? 1 : 0;
      }
      // Auto-calc weekend
      if (key === "day_of_week") {
        next.is_weekend = Number(value) >= 5 ? 1 : 0;
      }

      return next;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const totalLines = Number(form.lines_added) + Number(form.lines_deleted);
    const linesPerFile = Number(form.num_files_changed) > 0
      ? totalLines / Number(form.num_files_changed)
      : 0;
    const testFailRatio = Number(form.test_count) > 0
      ? Number(form.test_fail_count) / Number(form.test_count)
      : 0;

    // Branch flags
    const branchFlags = {
      branch_is_hotfix: form.branch_type === "hotfix" ? 1 : 0,
      branch_is_bugfix: form.branch_type === "bugfix" ? 1 : 0,
      branch_is_feature: form.branch_type === "feature" ? 1 : 0,
      branch_is_release: form.branch_type === "release" ? 1 : 0,
    };

    // Trigger flags
    const triggerFlags = {
      trigger_is_push: form.trigger_type === "push" ? 1 : 0,
      trigger_is_schedule: form.trigger_type === "schedule" ? 1 : 0,
    };

    const payload = {
      num_files_changed: Number(form.num_files_changed),
      lines_added: Number(form.lines_added),
      lines_deleted: Number(form.lines_deleted),
      test_count: Number(form.test_count),
      test_pass_count: Number(form.test_pass_count),
      test_fail_count: Number(form.test_fail_count),
      build_duration_seconds: Number(form.build_duration_seconds),
      hour: Number(form.hour),
      day_of_week: Number(form.day_of_week),
      is_late_night: Number(form.is_late_night),
      is_weekend: Number(form.is_weekend),
      total_lines_changed: totalLines,
      lines_per_file: Math.round(linesPerFile * 100) / 100,
      test_fail_ratio: Math.round(testFailRatio * 10000) / 10000,
      ...branchFlags,
      ...triggerFlags,
    };

    onSubmit(payload, form.branch_type, form.trigger_type);
  };

  const totalLines = Number(form.lines_added) + Number(form.lines_deleted);
  const linesPerFile = Number(form.num_files_changed) > 0
    ? (totalLines / Number(form.num_files_changed)).toFixed(1)
    : "0";
  const testFailRatio = Number(form.test_count) > 0
    ? (Number(form.test_fail_count) / Number(form.test_count) * 100).toFixed(2)
    : "0";

  return (
    <form onSubmit={handleSubmit} className="card">
      <div className="card-title">Build Features</div>

      <div className="form-section">
        <h3>Code Changes</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Files Changed</label>
            <input type="number" min="1" max="500" value={form.num_files_changed}
              onChange={(e) => set("num_files_changed", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Lines Added</label>
            <input type="number" min="0" value={form.lines_added}
              onChange={(e) => set("lines_added", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Lines Deleted</label>
            <input type="number" min="0" value={form.lines_deleted}
              onChange={(e) => set("lines_deleted", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Total Lines (auto)</label>
            <input type="text" value={totalLines} readOnly />
          </div>
          <div className="form-group">
            <label>Lines/File (auto)</label>
            <input type="text" value={linesPerFile} readOnly />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Tests</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Test Count</label>
            <input type="number" min="0" value={form.test_count}
              onChange={(e) => set("test_count", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Tests Passed</label>
            <input type="number" min="0" value={form.test_pass_count}
              onChange={(e) => set("test_pass_count", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Tests Failed</label>
            <input type="number" min="0" value={form.test_fail_count}
              onChange={(e) => set("test_fail_count", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Fail Ratio (auto)</label>
            <input type="text" value={`${testFailRatio}%`} readOnly />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Build</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Duration (seconds)</label>
            <input type="number" min="0" value={form.build_duration_seconds}
              onChange={(e) => set("build_duration_seconds", e.target.value)} required />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Timing</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Hour (0-23)</label>
            <input type="number" min="0" max="23" value={form.hour}
              onChange={(e) => set("hour", e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Day of Week</label>
            <select value={form.day_of_week} onChange={(e) => set("day_of_week", e.target.value)}>
              <option value="0">Monday</option>
              <option value="1">Tuesday</option>
              <option value="2">Wednesday</option>
              <option value="3">Thursday</option>
              <option value="4">Friday</option>
              <option value="5">Saturday</option>
              <option value="6">Sunday</option>
            </select>
          </div>
          <div className="form-group">
            <label>Late Night (auto)</label>
            <input type="text" value={form.is_late_night ? "Yes" : "No"} readOnly />
          </div>
          <div className="form-group">
            <label>Weekend (auto)</label>
            <input type="text" value={form.is_weekend ? "Yes" : "No"} readOnly />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Branch & Trigger</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Branch Type</label>
            <select value={form.branch_type} onChange={(e) => set("branch_type", e.target.value)}>
              <option value="main">main / develop</option>
              <option value="feature">feature</option>
              <option value="bugfix">bugfix</option>
              <option value="hotfix">hotfix</option>
              <option value="release">release</option>
            </select>
          </div>
          <div className="form-group">
            <label>Trigger Type</label>
            <select value={form.trigger_type} onChange={(e) => set("trigger_type", e.target.value)}>
              <option value="pull_request">Pull Request</option>
              <option value="push">Push</option>
              <option value="schedule">Schedule</option>
            </select>
          </div>
        </div>
      </div>

      <button type="submit" className="btn-predict" disabled={loading}>
        {loading ? "Predicting..." : "Predict Build Outcome"}
      </button>
    </form>
  );
}

export default PredictionForm;
