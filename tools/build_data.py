#!/usr/bin/env python3
"""Build the website preload data from the supplied current SOTK master.

Usage:
  python3 build_data.py <SOTK_MASTER.xlsx> <data.js> [DATA_SOTK_CABANG_FORMASI.xlsx]

The source workbook is read-only. Existing SOTK columns and rows are preserved;
POSITION is derived as an additional display column. Both position-tier rule
sheets are emitted to data.js so the runtime can use the same source of truth.
"""
import sys, json, datetime, re
import pandas as pd

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
SRC = sys.argv[1]
OUT = sys.argv[2]
FORMASI_SRC = sys.argv[3] if len(sys.argv) > 3 else None

SHEETS = [
    'SOTK_WILAYAH', 'SOTK_AREA', 'SOTK_CABANG', 'CORPORATE_TITLE',
    'UNIT_MASTER_CABANG', 'WEB_FILTER_MASTER', 'POSITION_GRADE_RULES',
    'POSITION_GRADE_TIER_MAP'
]
CODE_COLS = {'ORG CODE', 'UNIT_KEY', 'BRANCH_KEY', 'FORMASI_KEY', 'JOB CODE'}
# Rule documentation columns are useful in the Excel source, but are not used as
# runtime fields by the legacy matcher. The canonical runtime map is emitted in
# POSITION_GRADE_TIER_MAP instead.
DROP_COLS = {'SOTK_CABANG': {
    'CURRENT_JOB_CODE_FIELD', 'DEFINITIVE_JOB_CODE_FIELD', 'CURRENT_POSITION_FIELD',
    'DEFINITIVE_POSITION_FIELD', 'CURRENT_JOB_GRADE_FIELD', 'DEFINITIVE_JOB_GRADE_FIELD',
    'MATCH_PRIORITY_RULE'
}}


def clean(v, col=None):
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT:
        return None
    if isinstance(v, (datetime.datetime, pd.Timestamp)):
        return v.strftime('%Y-%m-%d')
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if col in CODE_COLS and not isinstance(v, str):
        v = str(int(v)) if isinstance(v, (int, float)) else str(v)
    if isinstance(v, str):
        v = v.strip()
        return v if v else None
    # Convert numpy scalar types to native Python types for JSON serialization.
    if hasattr(v, 'item'):
        try:
            return v.item()
        except Exception:
            pass
    return v


def read(name):
    df = pd.read_excel(SRC, sheet_name=name, dtype=object)
    df = df.dropna(how='all')
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col(df, candidates):
    """Return the first existing header from candidates, case-insensitively."""
    lut = {str(c).strip().upper(): c for c in df.columns}
    for c in candidates:
        if c.strip().upper() in lut:
            return lut[c.strip().upper()]
    return None


def to_grade(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    m = re.search(r'\d+', str(v))
    return int(m.group(0)) if m else None


TIERED = {'AMNG', 'PSR', 'SAO', 'AO', 'PAGN'}


def tier_text(rules, key):
    key_col = find_col(rules, ['SOTK_JOB_KEY'])
    name_col = find_col(rules, ['POSITION_NAME_PREFIX_MATCH', 'POSITION NAME / LEVEL', 'POSITION_NAME_PREFIX'])
    grade_col = find_col(rules, ['FALLBACK_JOB_GRADE', 'JOB GRADE TARGET', 'JOB_GRADE_PASANGAN'])
    if not key_col or not name_col:
        return ''
    items, seen = [], set()
    for _, r in rules[rules[key_col].astype(str).str.strip() == key].iterrows():
        nm = str(r.get(name_col) or '').strip()
        if not nm or nm.lower() in ('nan', 'none') or 'fallback lama' in nm.lower():
            continue
        grade = to_grade(r.get(grade_col)) if grade_col else None
        item = f'{nm} (JG {grade})' if grade is not None else nm
        if item not in seen:
            seen.add(item); items.append(item)
    return ' · '.join(items)


def position_cabang(row, rules_text):
    job = str(row.get('JOB CODE') or '').strip()
    jn = str(row.get('JOB NAME ', row.get('JOB NAME', '')) or '').strip()
    kelas = str(row.get('KELAS CABANG') or '').strip()
    if job in TIERED:
        return rules_text.get(job) or jn
    if job == 'PNC' and kelas in ('A', 'B'):
        return f'{jn} {kelas}'
    if job == 'MBI' and kelas in ('A', 'B'):
        return f'{jn} {kelas}'
    if job == 'KUPC' and kelas in ('A', 'B'):
        unit = str(row.get('NAMA UNIT KERJA') or '').upper()
        kind = 'UPS' if unit.startswith(('UPS', 'UPKS')) else 'UPC'
        return f'Kepala {kind} {kelas}'
    return jn


def read_validation_changes():
    try:
        val = pd.read_excel(SRC, sheet_name='VALIDASI_REVISI', header=None, dtype=object).dropna(how='all')
    except Exception:
        return []
    changes = []
    for _, r in val.iterrows():
        p, v, k = r.get(0), r.get(1), r.get(2)
        if isinstance(p, str) and isinstance(k, str) and p.strip().upper() not in ('ITEM', 'PARAMETER', 'VALIDASI REVISI MASTER SOTK'):
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                changes.append({'org': '', 'kind': str(p).strip(), 'text': str(k).strip()})
    return changes


def main():
    data = {n: read(n) for n in SHEETS}
    rules = data['POSITION_GRADE_RULES']
    rules_text = {k: tier_text(rules, k) for k in TIERED}

    # Additional display metadata only: source SOTK_WILAYAH/SOTK_AREA fields
    # are copied unchanged and POSITION mirrors their existing JOB NAME.
    w = data['SOTK_WILAYAH']
    a = data['SOTK_AREA']
    c = data['SOTK_CABANG']
    w['POSITION'] = w['JOB NAME']
    a['POSITION'] = a['JOB NAME']
    c['POSITION'] = c.apply(lambda r: position_cabang(r, rules_text), axis=1)

    pre = {}
    for n, df in data.items():
        df = df.drop(columns=[x for x in DROP_COLS.get(n, ()) if x in df.columns])
        pre[n + '_H'] = list(df.columns)
        pre[n] = [[clean(v, col) for col, v in zip(df.columns, row)] for row in df.itertuples(index=False, name=None)]

    # Metadata is informational only and reflects the actual source filename.
    changes = read_validation_changes()
    pre['SOTK_META'] = {
        'version': 'SOTK 2026 — master terbaru dengan Position Name dan peta tingkat jabatan',
        'source': SRC.replace('\\', '/').split('/')[-1],
        'generated': datetime.date.today().isoformat(),
        'changes': changes + [{
            'org': '', 'kind': 'Kolom POSITION',
            'text': 'POSITION ditambahkan sebagai metadata display; isi formasi Kantor Wilayah dan Kantor Area dipertahankan.'
        }, {
            'org': '', 'kind': 'Peta tingkat jabatan',
            'text': 'POSITION_GRADE_RULES dan POSITION_GRADE_TIER_MAP dimuat ke aplikasi untuk deteksi Position Name dan validasi grade.'
        }]
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.SOTK_PRELOAD=' + json.dumps(pre, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + ';\n')

    forms_idx = pre['SOTK_CABANG_H'].index('FORMASI')
    total_formasi = sum((r[forms_idx] or 0) for r in pre['SOTK_CABANG'])
    um_headers = pre['UNIT_MASTER_CABANG_H']
    um_key_idx = um_headers.index('UNIT_KEY')
    outlets = {r[um_key_idx] for r in pre['UNIT_MASTER_CABANG'] if r[um_key_idx] not in (None, '')}
    print('Baris:', {n: len(pre[n]) for n in SHEETS})
    print('Total formasi SOTK_CABANG:', total_formasi, '| outlet master:', len(outlets))
    print('POSITION_GRADE_TIER_MAP rows:', len(pre['POSITION_GRADE_TIER_MAP']))
    print('Contoh POSITION Cabang:')
    headers = pre['SOTK_CABANG_H']
    pos_idx = headers.index('POSITION')
    job_idx = headers.index('JOB CODE')
    for j in ['PSR', 'AMNG', 'SAO', 'AO', 'PAGN']:
        row = next((r for r in pre['SOTK_CABANG'] if r[job_idx] == j), None)
        print(' ', j, '->', row[pos_idx] if row else '(tidak ditemukan)')
    if FORMASI_SRC:
        try:
            src_df = pd.read_excel(FORMASI_SRC, sheet_name=0, header=1, dtype=object).dropna(subset=['KODE'])
            src_df = src_df[pd.to_numeric(src_df['KODE'], errors='coerce').notna()]
            print('Total formasi file sumber:', int(pd.to_numeric(src_df['TOTAL FORMASI'], errors='coerce').fillna(0).sum()), '| outlet sumber:', src_df['KODE'].nunique())
        except Exception as exc:
            print('Peringatan: sumber pembanding tidak dapat dibaca:', exc)

if __name__ == '__main__':
    main()
