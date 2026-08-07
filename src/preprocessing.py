"""
Data loading and cleaning for AI ETR Predictor SMKKJ.

The two source workbooks (`GPS_Bidang_SMKKJ_2026.xlsx` and
`ANALISIS_PPT_2026_T5_OPTIMISED.xlsx`) are formatted as printable reports:
decorative title rows, merged header cells, emoji status markers, and (for
the 18 per-subject PPT sheets) a grade-distribution table spread across two
header rows. `DataPreprocessor` turns each relevant block into a tidy
`pandas.DataFrame` by locating header cells by *text* rather than hardcoded
row/column numbers, so parsing degrades gracefully (skips + logs a warning)
instead of crashing when a sheet doesn't exactly match the expected
template.

Important: the source data is aggregated at class / subject / bidang level.
There is no per-student data anywhere in these workbooks.
"""

import re
from pathlib import Path

import pandas as pd

from src.config import GPS_BIDANG_FILE, PPT_ANALYSIS_FILE, PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.exceptions import DataFileNotFoundError, DataParsingError
from src.logging_config import get_logger

logger = get_logger(__name__)

_SUBJECT_CODE_RE = re.compile(r"^(\d+)\s+(.*)$")

# Official GP performance bands, as printed on every PPT subject sheet
# ("🏆 CEMERLANG GP ≤ 2.0 | ✅ BAIK GP 2.01-3.00 | ⚠️ SEDERHANA GP 3.01-5.00 |
#  ⛔ LEMAH GP 5.01-7.00 | 🚨 KRITIKAL GP > 7.00"). Kept here as a documented
# constant (sourced from the data, not invented) so callers can classify a
# GP value without re-parsing that legend from a sheet.
GP_BAND_LEGEND = {
    "CEMERLANG": (None, 2.00),
    "BAIK": (2.01, 3.00),
    "SEDERHANA": (3.01, 5.00),
    "LEMAH": (5.01, 7.00),
    "KRITIKAL": (7.01, None),
}


def classify_gp_band(gp):
    """Classify a GRED PURATA value into its official performance band.

    Returns None if `gp` is missing/unparseable.
    """
    if gp is None or (isinstance(gp, float) and pd.isna(gp)):
        return None
    for label, (low, high) in GP_BAND_LEGEND.items():
        if low is not None and gp < low:
            continue
        if high is not None and gp > high:
            continue
        return label
    return None


def _clean_status(text):
    """Strip emoji/decoration from a STATUS cell, keeping the plain label."""
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def _to_float(value):
    """Best-effort numeric coercion: handles '81.72%', '-', ints, floats, None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return None if pd.isna(value) else float(value)
    text = str(value).strip()
    if text in ("", "-", "–", "nan", "NaN"):
        return None
    text = text.replace("%", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value):
    f = _to_float(value)
    return int(f) if f is not None else None


def _find_exact_cell(raw: pd.DataFrame, target: str):
    """First (row, col) whose stripped string value equals `target` exactly."""
    for r in range(len(raw)):
        for c, val in enumerate(raw.iloc[r]):
            if isinstance(val, str) and val.strip() == target:
                return r, c
    return None


def _find_cell_startswith(raw: pd.DataFrame, prefix: str):
    """First (row, col) whose stripped value starts with `prefix` (case-insensitive).

    Uses a prefix match (not a substring match) so a label embedded
    mid-sentence in an unrelated title/caption row won't be mistaken for
    the real data cell (e.g. "Sasaran GPS Sekolah: ..." vs the actual
    "GPS SEKOLAH (Purata 4 Bidang)" summary row).
    """
    needle = prefix.lower()
    for r in range(len(raw)):
        for c, val in enumerate(raw.iloc[r]):
            if isinstance(val, str) and val.strip().lower().startswith(needle):
                return r, c
    return None


def _find_row_with_all(raw: pd.DataFrame, targets):
    """First row index whose cells (exact match) cover every label in `targets`."""
    for r in range(len(raw)):
        row_vals = {v.strip() for v in raw.iloc[r] if isinstance(v, str)}
        if all(t in row_vals for t in targets):
            return r
    return None


def _col_for_label(raw: pd.DataFrame, row_idx: int, label: str):
    """Column index of the cell exactly matching `label` within row `row_idx`."""
    for c, val in enumerate(raw.iloc[row_idx]):
        if isinstance(val, str) and val.strip() == label:
            return c
    return None


class DataPreprocessor:
    """Loads, parses and cleans SMKKJ exam-performance workbooks.

    `load_gps()`/`load_ppt()` are kept for backward compatibility and now
    delegate to the tidy loaders below (`load_gps_ringkasan_bidang` /
    `load_ppt_summary`) instead of returning the raw, multi-header sheet.
    """

    def __init__(self, raw_path: Path = RAW_DATA_DIR, processed_path: Path = PROCESSED_DATA_DIR):
        self.raw_path = Path(raw_path)
        self.processed_path = Path(processed_path)

    # ------------------------------------------------------------------
    # Generic Excel I/O (original behaviour, unchanged signatures)
    # ------------------------------------------------------------------

    def load_excel(self, filename):
        file_path = self.raw_path / filename
        if not file_path.exists():
            raise DataFileNotFoundError(f"Fail data tidak dijumpai: {file_path}")
        logger.info("Memuatkan fail Excel: %s", file_path)
        return pd.read_excel(file_path)

    def save_processed(self, dataframe, filename):
        output = self.processed_path / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(output, index=False)
        logger.info("Data diproses disimpan di: %s", output)
        return output

    def clean_dataframe(self, df):
        df = df.dropna(how="all")
        df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
        df = df.reset_index(drop=True)
        df = df.drop_duplicates()
        df = df.fillna("")
        return df

    def load_gps(self):
        """Backward-compatible entry point -> bidang-level GPS rollup."""
        return self.load_gps_ringkasan_bidang()

    def load_ppt(self):
        """Backward-compatible entry point -> subject-level PPT summary."""
        return self.load_ppt_summary()

    # ------------------------------------------------------------------
    # Raw sheet access
    # ------------------------------------------------------------------

    def _read_raw_sheet(self, filename, sheet_name):
        file_path = self.raw_path / filename
        if not file_path.exists():
            raise DataFileNotFoundError(f"Fail data tidak dijumpai: {file_path}")
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except ValueError as exc:
            raise DataParsingError(
                f"Helaian '{sheet_name}' tidak dijumpai dalam {filename}"
            ) from exc

    def _subject_sheet_names(self, filename=PPT_ANALYSIS_FILE):
        file_path = self.raw_path / filename
        if not file_path.exists():
            raise DataFileNotFoundError(f"Fail data tidak dijumpai: {file_path}")
        xl = pd.ExcelFile(file_path)
        return [s for s in xl.sheet_names if s.strip().upper() != "00. RINGKASAN"]

    # ------------------------------------------------------------------
    # GPS_Bidang_SMKKJ_2026.xlsx
    # ------------------------------------------------------------------

    def load_gps_ringkasan_bidang(self):
        """Bidang-level rollup from the 'Ringkasan Bidang' sheet.

        Columns: BIDANG, BIL_SUBJEK, GPS_TERENDAH, GP_BIDANG, STATUS, STATUS_CLEAN.
        """
        raw = self._read_raw_sheet(GPS_BIDANG_FILE, "Ringkasan Bidang")
        anchor = _find_exact_cell(raw, "BIDANG")
        if anchor is None:
            raise DataParsingError("Header 'BIDANG' tidak dijumpai dalam helaian Ringkasan Bidang")
        header_row, col = anchor

        rows = []
        for r in range(header_row + 1, len(raw)):
            bidang = raw.iat[r, col]
            if pd.isna(bidang) or not str(bidang).strip():
                break
            if str(bidang).strip().upper().startswith("GPS SEKOLAH"):
                break
            rows.append(
                {
                    "BIDANG": bidang,
                    "BIL_SUBJEK": _to_int(raw.iat[r, col + 1]) if col + 1 < raw.shape[1] else None,
                    "GPS_TERENDAH": _to_float(raw.iat[r, col + 2]) if col + 2 < raw.shape[1] else None,
                    "GP_BIDANG": _to_float(raw.iat[r, col + 3]) if col + 3 < raw.shape[1] else None,
                    "STATUS": raw.iat[r, col + 4] if col + 4 < raw.shape[1] else None,
                }
            )
        if not rows:
            raise DataParsingError("Tiada baris bidang dijumpai dalam helaian Ringkasan Bidang")

        df = pd.DataFrame(rows)
        df["STATUS_CLEAN"] = df["STATUS"].map(_clean_status)
        logger.info("load_gps_ringkasan_bidang: %d baris dimuatkan", len(df))
        return df

    def load_gps_school_summary(self) -> dict:
        """School-level GPS achievement (target vs actual) from 'Ringkasan Bidang'."""
        raw = self._read_raw_sheet(GPS_BIDANG_FILE, "Ringkasan Bidang")
        summary = {}

        gps_anchor = _find_cell_startswith(raw, "GPS SEKOLAH")
        if gps_anchor:
            r, c = gps_anchor
            summary["label"] = str(raw.iat[r, c]).strip()
            summary["bidang_count"] = raw.iat[r, c + 1] if c + 1 < raw.shape[1] else None
            summary["gp_purata"] = _to_float(raw.iat[r, c + 3]) if c + 3 < raw.shape[1] else None
            status = raw.iat[r, c + 4] if c + 4 < raw.shape[1] else None
            summary["status"] = status
            summary["status_clean"] = _clean_status(status)

        etr_anchor = _find_cell_startswith(raw, "ETR SASARAN")
        if etr_anchor:
            r, c = etr_anchor
            summary["etr_sasaran"] = _to_float(raw.iat[r, c + 3]) if c + 3 < raw.shape[1] else None

        if not summary:
            raise DataParsingError("Ringkasan GPS sekolah tidak dijumpai dalam Ringkasan Bidang")
        logger.info("load_gps_school_summary: %s", summary)
        return summary

    def load_gps_dashboard(self):
        """Subject-level GPS targets across all bidang, from 'GP Bidang Dashboard'.

        Columns: BIL, BIDANG, SUBJEK, GPS_SASARAN, GP_BIDANG, STATUS, STATUS_CLEAN.
        BIDANG/GP_BIDANG/STATUS are forward-filled to their per-subject row since
        the source sheet only prints them once per bidang group (merged cells).
        """
        raw = self._read_raw_sheet(GPS_BIDANG_FILE, "GP Bidang Dashboard")
        anchor = _find_exact_cell(raw, "SUBJEK")
        if anchor is None:
            raise DataParsingError("Header 'SUBJEK' tidak dijumpai dalam GP Bidang Dashboard")
        header_row, subjek_col = anchor

        cols = {
            "BIL": _col_for_label(raw, header_row, "Bil"),
            "BIDANG": _col_for_label(raw, header_row, "BIDANG"),
            "SUBJEK": subjek_col,
            "GPS_SASARAN": _col_for_label(raw, header_row, "GPS SASARAN"),
            "GP_BIDANG": _col_for_label(raw, header_row, "GP BIDANG"),
            "STATUS": _col_for_label(raw, header_row, "STATUS"),
        }
        missing = [k for k, v in cols.items() if v is None]
        if missing:
            raise DataParsingError(f"Lajur {missing} tiada dalam GP Bidang Dashboard")

        rows = []
        for r in range(header_row + 1, len(raw)):
            subjek = raw.iat[r, cols["SUBJEK"]]
            if pd.isna(subjek) or not str(subjek).strip():
                break
            rows.append({name: raw.iat[r, c] for name, c in cols.items()})

        df = pd.DataFrame(rows)
        df["BIDANG"] = df["BIDANG"].replace("", pd.NA).ffill()
        df["STATUS"] = df["STATUS"].replace("", pd.NA).ffill()
        df["GP_BIDANG"] = df["GP_BIDANG"].apply(_to_float).ffill()
        df["GPS_SASARAN"] = df["GPS_SASARAN"].apply(_to_float)
        df["BIL"] = df["BIL"].apply(_to_int)
        df["STATUS_CLEAN"] = df["STATUS"].map(_clean_status)
        logger.info("load_gps_dashboard: %d baris dimuatkan", len(df))
        return df

    def load_gps_kemanusiaan_detail(self):
        """Subject-level detail (incl. teacher/PIC) for Bidang Kemanusiaan."""
        raw = self._read_raw_sheet(GPS_BIDANG_FILE, "Bidang Kemanusiaan")
        anchor = _find_exact_cell(raw, "SUBJEK")
        if anchor is None:
            raise DataParsingError("Header 'SUBJEK' tidak dijumpai dalam Bidang Kemanusiaan")
        header_row, subjek_col = anchor

        cols = {
            "BIL": _col_for_label(raw, header_row, "Bil"),
            "SUBJEK": subjek_col,
            "GPS_SASARAN": _col_for_label(raw, header_row, "GPS SASARAN"),
            "STATUS": _col_for_label(raw, header_row, "STATUS"),
            "GURU_PIC": _col_for_label(raw, header_row, "GURU / PIC"),
        }
        missing = [k for k, v in cols.items() if v is None]
        if missing:
            raise DataParsingError(f"Lajur {missing} tiada dalam Bidang Kemanusiaan")

        rows = []
        for r in range(header_row + 1, len(raw)):
            subjek = raw.iat[r, cols["SUBJEK"]]
            if pd.isna(subjek) or not str(subjek).strip():
                break
            rows.append({name: raw.iat[r, c] for name, c in cols.items()})

        df = pd.DataFrame(rows)
        df["GPS_SASARAN"] = df["GPS_SASARAN"].apply(_to_float)
        df["BIL"] = df["BIL"].apply(_to_int)
        df["STATUS_CLEAN"] = df["STATUS"].map(_clean_status)
        logger.info("load_gps_kemanusiaan_detail: %d baris dimuatkan", len(df))
        return df

    # ------------------------------------------------------------------
    # ANALISIS_PPT_2026_T5_OPTIMISED.xlsx
    # ------------------------------------------------------------------

    def load_ppt_summary(self):
        """Subject-level PPT summary from the '00. RINGKASAN' sheet.

        Columns: KOD, MATA_PELAJARAN, BIL_DAFTAR, PCT_LULUS, GRED_PURATA,
        STATUS, STATUS_CLEAN, GP_BAND (cross-check against `classify_gp_band`).
        """
        raw = self._read_raw_sheet(PPT_ANALYSIS_FILE, "00. RINGKASAN")
        anchor = _find_exact_cell(raw, "MATA PELAJARAN")
        if anchor is None:
            raise DataParsingError("Header 'MATA PELAJARAN' tidak dijumpai dalam 00. RINGKASAN")
        header_row, subj_col = anchor

        cols = {
            "MATA_PELAJARAN": subj_col,
            "BIL_DAFTAR": _col_for_label(raw, header_row, "BIL DAFTAR"),
            "PCT_LULUS": _col_for_label(raw, header_row, "% LULUS"),
            "GRED_PURATA": _col_for_label(raw, header_row, "GRED PURATA"),
            "STATUS": _col_for_label(raw, header_row, "STATUS"),
        }
        missing = [k for k, v in cols.items() if v is None]
        if missing:
            raise DataParsingError(f"Lajur {missing} tiada dalam 00. RINGKASAN")

        rows = []
        for r in range(header_row + 1, len(raw)):
            subj = raw.iat[r, cols["MATA_PELAJARAN"]]
            if pd.isna(subj) or not str(subj).strip():
                break
            rows.append({name: raw.iat[r, c] for name, c in cols.items()})

        df = pd.DataFrame(rows)
        split = df["MATA_PELAJARAN"].astype(str).str.strip().str.extract(_SUBJECT_CODE_RE)
        df["KOD"] = split[0]
        df["MATA_PELAJARAN"] = split[1].fillna(df["MATA_PELAJARAN"])
        df["BIL_DAFTAR"] = df["BIL_DAFTAR"].apply(_to_int)
        df["PCT_LULUS"] = df["PCT_LULUS"].apply(_to_float)
        df["GRED_PURATA"] = df["GRED_PURATA"].apply(_to_float)
        df["STATUS_CLEAN"] = df["STATUS"].map(_clean_status)
        df["GP_BAND"] = df["GRED_PURATA"].apply(classify_gp_band)
        df = df[["KOD", "MATA_PELAJARAN", "BIL_DAFTAR", "PCT_LULUS", "GRED_PURATA", "STATUS", "STATUS_CLEAN", "GP_BAND"]]
        logger.info("load_ppt_summary: %d subjek dimuatkan", len(df))
        return df

    def load_ppt_school_gp(self) -> float:
        """Overall school GRED PURATA SEKOLAH (GPS) for this PPT round."""
        raw = self._read_raw_sheet(PPT_ANALYSIS_FILE, "00. RINGKASAN")
        anchor = _find_cell_startswith(raw, "GRED PURATA SEKOLAH")
        if anchor is None:
            raise DataParsingError("'GRED PURATA SEKOLAH' tidak dijumpai dalam 00. RINGKASAN")
        r, c = anchor
        for val in raw.iloc[r, c:]:
            gp = _to_float(val)
            if gp is not None:
                logger.info("load_ppt_school_gp: %.2f", gp)
                return gp
        raise DataParsingError("Nilai GPS sekolah tidak dijumpai dalam 00. RINGKASAN")

    def load_ppt_class_breakdown(self):
        """Per-class grade distribution across every subject sheet (tidy long format).

        Columns: KOD, SUBJEK, KELAS, PCT_LULUS, GP, A_PLUS, A, A_MINUS, B_PLUS,
        B, C_PLUS, C, D, E, G, TH (grade columns are student counts).
        Sheets that don't match the expected template are skipped with a
        logged warning rather than aborting the whole load.
        """
        frames = []
        for sheet in self._subject_sheet_names():
            try:
                frame = self._parse_subject_class_table(sheet)
                if frame is not None and not frame.empty:
                    frames.append(frame)
            except DataParsingError as exc:
                logger.warning("Helaian '%s' dilangkau: %s", sheet, exc)

        if not frames:
            raise DataParsingError("Tiada helaian subjek berjaya dihurai untuk pecahan kelas")

        df = pd.concat(frames, ignore_index=True)
        logger.info("load_ppt_class_breakdown: %d baris kelas dari %d helaian", len(df), len(frames))
        return df

    def _parse_subject_class_table(self, sheet_name):
        raw = self._read_raw_sheet(PPT_ANALYSIS_FILE, sheet_name)

        kod = subjek = None
        for text in raw.iloc[:5, 0].dropna().astype(str):
            m = _SUBJECT_CODE_RE.match(text.strip())
            if m:
                kod, subjek = m.group(1), m.group(2)
                break
        if kod is None:
            raise DataParsingError(f"Kod/nama subjek tidak dijumpai pada helaian {sheet_name}")

        # The workbook prints a fully flattened per-class table (single header
        # row: KELAS, % LULUS, GP, A+, A, ..., TH) further right on the sheet,
        # separate from the two-row merged-header table used for printing.
        # It's identified by having both "KELAS" and "A+" in the same row.
        header_row = _find_row_with_all(raw, {"KELAS", "A+", "% LULUS", "GP"})
        if header_row is None:
            raise DataParsingError(f"Jadual pecahan kelas tidak dijumpai pada helaian {sheet_name}")

        label_to_key = {
            "KELAS": "KELAS", "% LULUS": "PCT_LULUS", "GP": "GP",
            "A+": "A_PLUS", "A": "A", "A-": "A_MINUS", "B+": "B_PLUS", "B": "B",
            "C+": "C_PLUS", "C": "C", "D": "D", "E": "E", "G": "G", "TH": "TH",
        }
        col_map = {}
        for label, key in label_to_key.items():
            col = _col_for_label(raw, header_row, label)
            if col is None:
                raise DataParsingError(f"Lajur '{label}' tiada pada jadual pecahan kelas {sheet_name}")
            col_map[key] = col

        rows = []
        for r in range(header_row + 1, len(raw)):
            kelas = raw.iat[r, col_map["KELAS"]]
            if pd.isna(kelas) or not str(kelas).strip():
                break
            record = {"KOD": kod, "SUBJEK": subjek}
            for key, col in col_map.items():
                value = raw.iat[r, col]
                record[key] = value if key == "KELAS" else _to_float(value)
            rows.append(record)

        if not rows:
            raise DataParsingError(f"Tiada baris kelas dijumpai pada helaian {sheet_name}")

        return pd.DataFrame(rows)
