# 숫자 포맷 (미리보기용 - 문자열 변환)
def format_numbers_preview(row: dict) -> dict:
    """천 단위 콤마 + yld 퍼센트 표시 (문자열)"""
    for col in ["inqty", "currqty", "testedqty", "goodqty"]:
        if col in row and row[col] is not None:
            try:
                row[col] = "{:,.0f}".format(float(row[col]))
            except:
                pass
    if "yld" in row and row["yld"] is not None:
        try:
            row["yld"] = f"{float(row['yld']) * 100:.1f}%"
        except:
            pass
    return row


# 숫자 포맷 (엑셀 서식용 - 엑셀에서 계산 가능 + 가운데 정렬 + 값 있는 셀만 노란색)
def apply_excel_formats(writer, df):
    """엑셀 워크시트에 숫자, 퍼센트, 날짜 서식 적용 + 가운데 정렬 + 값 있는 셀만 노란색"""
    workbook = writer.book
    worksheet = writer.sheets["SortedData"]

    # 포맷 정의
    center_align = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
    number_format = workbook.add_format({'num_format': '#,##0', 'align': 'center', 'valign': 'vcenter'})
    percent_format = workbook.add_format({'num_format': '0.0%', 'align': 'center', 'valign': 'vcenter'})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center', 'valign': 'vcenter'})
    yellow_bg = workbook.add_format({'bg_color': '#FFFF00', 'align': 'center', 'valign': 'vcenter'})

    # 기본 가운데 정렬 (전체 컬럼)
    worksheet.set_column(0, len(df.columns) - 1, None, center_align)

    # 천 단위 콤마 적용
    for col_name in ["inqty", "currqty", "testedqty", "goodqty"]:
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name)
            worksheet.set_column(col_idx, col_idx, 15, number_format)

    # 퍼센트 적용
    if "yld" in df.columns:
        col_idx = df.columns.get_loc("yld")
        worksheet.set_column(col_idx, col_idx, 10, percent_format)

    # 날짜 서식 적용
    for col_name in ["Testdate", "shipdate"]:
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name)
            worksheet.set_column(col_idx, col_idx, 12, date_format)

    # 📌 조건부 서식 - 값이 있는 셀만 노란색
    yellow_cols = ["partno", "codes", "lotno", "dcode", "Testdate", "shipdate",
                   "boxno", "serialst", "serialsp", "inqty", "currqty",
                   "testedqty", "goodqty", "yld"]

    for col_name in yellow_cols:
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name)
            worksheet.conditional_format(
                1, col_idx, len(df), col_idx,  # 데이터 범위만
                {'type': 'no_blanks', 'format': yellow_bg}
            )
